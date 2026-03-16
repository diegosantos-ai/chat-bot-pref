from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Protocol

import httpx

from app.contracts.dto import RagRetrievedChunk
from app.observability.cost_estimation import estimate_llm_operational_cost
from app.services.prompt_service import PromptArtifact, PromptService
from app.services.tenant_profile_service import TenantProfile
from app.settings import settings


@dataclass(frozen=True)
class LLMGenerationRequest:
    prompt: PromptArtifact
    question: str
    tenant_profile: TenantProfile
    context_chunks: list[RagRetrievedChunk]
    reason_code: str | None = None
    policy_summary: str = ""


@dataclass(frozen=True)
class LLMGenerationResponse:
    provider: str
    model: str
    prompt_version: str
    message: str
    mode: str
    estimated_cost_usd: float = 0.0
    cost_estimation_status: str = ""
    cost_estimation_method: str = ""
    input_tokens_estimated: int = 0
    output_tokens_estimated: int = 0


class LLMProvider(Protocol):
    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        ...


class MockLLMProvider:
    def __init__(self, model: str | None = None) -> None:
        self.model = (model or settings.LLM_MODEL).strip() or "mock-compose-v1"

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        if request.reason_code:
            message = self._fallback_message(request)
            mode = "fallback"
        else:
            message = self._contextual_message(request)
            mode = "answer"

        return LLMGenerationResponse(
            provider="mock",
            model=self.model,
            prompt_version=request.prompt.version,
            message=message,
            mode=mode,
        )

    def _contextual_message(self, request: LLMGenerationRequest) -> str:
        selected_sentences = self._select_sentences(request.question, request.context_chunks)
        lead = f"De acordo com as informacoes institucionais da {request.tenant_profile.client_name}, "
        answer = " ".join(selected_sentences).strip()
        answer = answer.rstrip(".")
        closing = " Se precisar de atendimento formal, procure os canais oficiais da prefeitura."
        return f"{lead}{answer}.{closing}"

    def _fallback_message(self, request: LLMGenerationRequest) -> str:
        profile = request.tenant_profile
        reason_code = request.reason_code or "OUT_OF_SCOPE"
        if reason_code == "NO_KNOWLEDGE_BASE":
            return (
                f"No momento, a base institucional de {profile.client_name} ainda nao possui "
                "informacoes carregadas para responder com seguranca. Procure os canais oficiais da prefeitura."
            )
        if reason_code == "LOW_CONFIDENCE_RETRIEVAL":
            if self._looks_like_greeting_or_under_specified_query(request.question):
                return (
                    f"Posso orientar sobre servicos e informacoes institucionais de {profile.client_name}. "
                    "Descreva o assunto ou servico que voce quer consultar, por exemplo: horario de atendimento, "
                    "alvara, protocolo, IPTU ou vacinacao."
                )
            return (
                f"Nao encontrei contexto institucional suficiente em {profile.client_name} para responder com seguranca. "
                "Procure os canais oficiais da prefeitura para orientacao confirmada."
            )
        if reason_code == "OUT_OF_SCOPE":
            return (
                f"Posso ajudar apenas com orientacoes institucionais de {profile.client_name}. "
                "Para esse assunto, procure o canal adequado fora do escopo da prefeitura."
            )
        if reason_code == "UNSUPPORTED_TRANSACTIONAL_ACTION":
            return (
                f"Posso orientar sobre o servico, mas nao executar a acao solicitada em nome de {profile.client_name}. "
                "Para emissao, protocolo ou agendamento, use os canais oficiais da prefeitura."
            )
        if reason_code == "SENSITIVE_DATA_REQUEST":
            return (
                "Nao posso fornecer ou expor dados pessoais, sigilosos ou sensiveis. "
                "Se houver necessidade formal, procure o canal oficial da prefeitura."
            )
        if reason_code == "CRISIS_OR_MEDICAL_RISK":
            return (
                "Nao posso orientar casos de crise ou risco clinico. Se houver urgencia, procure atendimento imediato "
                "e os servicos de emergencia da sua regiao."
            )
        if reason_code == "PROMPT_INJECTION_SUSPECTED":
            return (
                "Nao posso ignorar as regras do assistente nem responder fora do escopo institucional. "
                "Se quiser, reformule sua pergunta sobre servicos da prefeitura."
            )
        if reason_code == "POLICY_POST_RESPONSE_REWRITE":
            return (
                f"Posso oferecer apenas orientacao institucional segura sobre {profile.client_name}. "
                "Para confirmar esse assunto, consulte os canais oficiais da prefeitura."
            )
        return (
            f"Posso oferecer apenas orientacao institucional geral sobre {profile.client_name}. "
            "Se precisar, procure os canais oficiais da prefeitura."
        )

    def _looks_like_greeting_or_under_specified_query(self, question: str) -> bool:
        normalized = " ".join(question.lower().strip().split())
        if not normalized:
            return True
        if len(re.findall(r"\w+", normalized)) <= 2:
            return True
        greeting_patterns = (
            r"^oi+$",
            r"^ola+$",
            r"^ol[aá]$",
            r"^bom dia$",
            r"^boa tarde$",
            r"^boa noite$",
            r"^tudo bem$",
        )
        return any(re.fullmatch(pattern, normalized) for pattern in greeting_patterns)

    def _select_sentences(
        self,
        question: str,
        context_chunks: list[RagRetrievedChunk],
    ) -> list[str]:
        tokens = {token for token in question.lower().split() if len(token) >= 4}
        ranked_sentences: list[tuple[int, str]] = []
        for chunk in context_chunks:
            sentences = [item.strip() for item in chunk.text.replace("\n", " ").split(".") if item.strip()]
            for sentence in sentences:
                overlap = sum(1 for token in tokens if token in sentence.lower())
                ranked_sentences.append((overlap, sentence))

        ranked_sentences.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
        best_overlap = ranked_sentences[0][0] if ranked_sentences else 0
        selected: list[str] = []
        for overlap, sentence in ranked_sentences:
            if best_overlap > 1 and overlap < best_overlap:
                continue
            if best_overlap <= 1 and overlap <= 0:
                continue
            normalized = sentence.strip()
            if normalized and normalized not in selected:
                selected.append(normalized)
            if len(selected) == 2:
                break

        if selected:
            return selected
        if context_chunks:
            return [context_chunks[0].text.replace("\n", " ").strip()]
        return ["Nao ha contexto institucional suficiente para compor uma resposta."]


class GeminiLLMProvider:
    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        api_base_url: str = "https://generativelanguage.googleapis.com/v1beta",
    ) -> None:
        self.model = (model or settings.LLM_MODEL).strip() or "gemini-2.0-flash"
        self.api_key = (api_key or settings.LLM_API_KEY).strip()
        self.api_base_url = api_base_url.rstrip("/")

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        if not self.api_key:
            raise RuntimeError("LLM_API_KEY obrigatorio para LLM_PROVIDER=gemini.")

        url = f"{self.api_base_url}/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": request.prompt.content}],
                }
            ]
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

        body = response.json()
        message = self._extract_text(body)
        return LLMGenerationResponse(
            provider="gemini",
            model=self.model,
            prompt_version=request.prompt.version,
            message=message,
            mode="fallback" if request.reason_code else "answer",
        )

    def _extract_text(self, body: dict) -> str:
        candidates = body.get("candidates", [])
        for candidate in candidates:
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                text = str(part.get("text", "")).strip()
                if text:
                    return text
        raise RuntimeError("Resposta do Gemini sem texto utilizavel.")


class LLMComposeService:
    def __init__(
        self,
        *,
        prompt_service: PromptService | None = None,
        provider: LLMProvider | None = None,
    ) -> None:
        self.prompt_service = prompt_service or PromptService()
        self.provider = provider or self._build_provider()

    async def compose_answer(
        self,
        *,
        tenant_profile: TenantProfile,
        question: str,
        context_chunks: list[RagRetrievedChunk],
    ) -> LLMGenerationResponse:
        context_block = "\n\n".join(
            f"- {chunk.title}: {chunk.text.strip()}"
            for chunk in context_chunks
        )
        prompt = self.prompt_service.render_base_prompt(
            bot_name=tenant_profile.bot_name,
            client_name=tenant_profile.client_name,
            question=question,
            context_block=context_block,
            institutional_voice=tenant_profile.institutional_voice,
        )
        request = LLMGenerationRequest(
            prompt=prompt,
            question=question,
            tenant_profile=tenant_profile,
            context_chunks=context_chunks,
        )
        response = await self.provider.generate(request)
        cost_estimation = estimate_llm_operational_cost(
            provider=response.provider,
            input_text=prompt.content,
            output_text=response.message,
        )
        return LLMGenerationResponse(
            provider=response.provider,
            model=response.model,
            prompt_version=response.prompt_version,
            message=response.message,
            mode=response.mode,
            estimated_cost_usd=cost_estimation.estimated_cost_usd,
            cost_estimation_status=cost_estimation.status,
            cost_estimation_method=cost_estimation.method,
            input_tokens_estimated=cost_estimation.input_tokens_estimated,
            output_tokens_estimated=cost_estimation.output_tokens_estimated,
        )

    async def compose_fallback(
        self,
        *,
        tenant_profile: TenantProfile,
        question: str,
        reason_code: str,
        policy_summary: str,
    ) -> LLMGenerationResponse:
        prompt = self.prompt_service.render_fallback_prompt(
            bot_name=tenant_profile.bot_name,
            client_name=tenant_profile.client_name,
            question=question,
            reason_code=reason_code,
            policy_summary=policy_summary,
        )
        request = LLMGenerationRequest(
            prompt=prompt,
            question=question,
            tenant_profile=tenant_profile,
            context_chunks=[],
            reason_code=reason_code,
            policy_summary=policy_summary,
        )
        response = await self.provider.generate(request)
        cost_estimation = estimate_llm_operational_cost(
            provider=response.provider,
            input_text=prompt.content,
            output_text=response.message,
        )
        return LLMGenerationResponse(
            provider=response.provider,
            model=response.model,
            prompt_version=response.prompt_version,
            message=response.message,
            mode=response.mode,
            estimated_cost_usd=cost_estimation.estimated_cost_usd,
            cost_estimation_status=cost_estimation.status,
            cost_estimation_method=cost_estimation.method,
            input_tokens_estimated=cost_estimation.input_tokens_estimated,
            output_tokens_estimated=cost_estimation.output_tokens_estimated,
        )

    def policy_version(self) -> str:
        return self.prompt_service.load_policy_text().version

    def _build_provider(self) -> LLMProvider:
        if settings.LLM_PROVIDER == "gemini":
            return GeminiLLMProvider()
        return MockLLMProvider()
