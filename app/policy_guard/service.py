from __future__ import annotations

from dataclasses import dataclass
import re

from app.contracts.dto import PolicyDecision, RagQueryResponse
from app.services.tenant_profile_service import TenantProfile
from app.settings import settings

PROMPT_INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"ignore .*regras",
        r"ignore .*instruc",
        r"bypass",
        r"ignore .*policy",
        r"system prompt",
        r"prompt secreto",
        r"responda livremente",
    ]
]

CRISIS_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"suic",
        r"me matar",
        r"em crise",
        r"crise emocional",
        r"ataque de panico",
        r"dor no peito",
        r"remedio",
        r"medicac",
    ]
]

SENSITIVE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bcpf\b",
        r"\brg\b",
        r"dados pessoais",
        r"senha",
        r"telefone pessoal",
        r"endereco residencial",
    ]
]

TRANSACTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bemita\b",
        r"\bgera\b",
        r"\bgera[r]?\b .*segunda via",
        r"\bagende\b",
        r"\bmarque\b",
        r"\bcancele\b",
        r"\baprove\b",
        r"\bprotocole\b",
        r"\bfaça\b .*por mim",
    ]
]

OUT_OF_SCOPE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"invest",
        r"criptomoeda",
        r"bitcoin",
        r"namor",
        r"horoscopo",
        r"receita de bolo",
        r"aposta",
    ]
]


@dataclass(frozen=True)
class PostPolicyInput:
    question: str
    candidate_response: str
    rag_response: RagQueryResponse


class PolicyGuardService:
    def __init__(
        self,
        *,
        policy_version: str | None = None,
        min_context_score: float | None = None,
    ) -> None:
        self.policy_version = (policy_version or settings.POLICY_TEXT_VERSION).strip()
        self.min_context_score = (
            min_context_score if min_context_score is not None else settings.LLM_MIN_CONTEXT_SCORE
        )

    def evaluate_pre(self, question: str, profile: TenantProfile) -> PolicyDecision:
        normalized = question.strip()

        if self._matches_any(normalized, PROMPT_INJECTION_PATTERNS):
            return self._decision(
                stage="policy_pre",
                decision="block",
                reason_codes=["PROMPT_INJECTION_SUSPECTED"],
                summary="Tentativa de contornar regras ou instrucao de sistema detectada.",
                metadata={"matched_rule": "prompt_injection"},
            )

        if self._matches_any(normalized, CRISIS_PATTERNS):
            return self._decision(
                stage="policy_pre",
                decision="block",
                reason_codes=["CRISIS_OR_MEDICAL_RISK"],
                summary="Pedido com conteudo clinico, crise ou risco exige resposta segura e limitada.",
                metadata={"matched_rule": "crisis_or_medical"},
            )

        if self._matches_any(normalized, SENSITIVE_PATTERNS):
            return self._decision(
                stage="policy_pre",
                decision="block",
                reason_codes=["SENSITIVE_DATA_REQUEST"],
                summary="Solicitacao de dado sensivel ou pessoal fora do escopo do assistente.",
                metadata={"matched_rule": "sensitive_data"},
            )

        if self._matches_any(normalized, TRANSACTION_PATTERNS):
            return self._decision(
                stage="policy_pre",
                decision="block",
                reason_codes=["UNSUPPORTED_TRANSACTIONAL_ACTION"],
                summary="O assistente nao executa acoes transacionais nem atos administrativos.",
                metadata={"matched_rule": "transaction_not_supported"},
            )

        if self._matches_any(normalized, OUT_OF_SCOPE_PATTERNS):
            return self._decision(
                stage="policy_pre",
                decision="block",
                reason_codes=["OUT_OF_SCOPE"],
                summary=(
                    f"O assistente {profile.bot_name} deve permanecer no escopo institucional da prefeitura."
                ),
                metadata={"matched_rule": "out_of_scope"},
            )

        return self._decision(
            stage="policy_pre",
            decision="allow",
            reason_codes=[],
            summary="Pergunta dentro do escopo inicial para seguir ao retrieval e composicao.",
            metadata={"matched_rule": "allow"},
        )

    def evaluate_post(
        self,
        post_input: PostPolicyInput,
        *,
        pre_decision: PolicyDecision | None = None,
    ) -> PolicyDecision:
        if pre_decision is not None and pre_decision.decision != "allow":
            return self._decision(
                stage="policy_post",
                decision="allow",
                reason_codes=pre_decision.reason_codes,
                summary="Resposta final preservou o bloqueio ou fallback definido na policy_pre.",
                metadata={"guardrail_source": "policy_pre"},
            )

        rag_response = post_input.rag_response
        if rag_response.status == "knowledge_base_not_loaded":
            return self._decision(
                stage="policy_post",
                decision="fallback",
                reason_codes=["NO_KNOWLEDGE_BASE"],
                summary="Base documental ausente para o tenant do request.",
                metadata={
                    "retrieval_status": rag_response.status,
                    "best_score": str(rag_response.best_score),
                },
            )

        if rag_response.status != "ready":
            return self._decision(
                stage="policy_post",
                decision="fallback",
                reason_codes=["LOW_CONFIDENCE_RETRIEVAL"],
                summary="Retrieval nao retornou contexto suficiente para resposta segura.",
                metadata={
                    "retrieval_status": rag_response.status,
                    "best_score": str(rag_response.best_score),
                },
            )

        if rag_response.best_score < self.min_context_score:
            return self._decision(
                stage="policy_post",
                decision="fallback",
                reason_codes=["LOW_CONFIDENCE_RETRIEVAL"],
                summary="Melhor chunk abaixo do score minimo para resposta com confianca.",
                metadata={
                    "retrieval_status": rag_response.status,
                    "best_score": f"{rag_response.best_score:.4f}",
                },
            )

        if self._max_overlap(post_input.question, rag_response) < 2:
            return self._decision(
                stage="policy_post",
                decision="fallback",
                reason_codes=["LOW_CONFIDENCE_RETRIEVAL"],
                summary="Os chunks recuperados nao apresentam aderencia lexical minima com a pergunta.",
                metadata={
                    "retrieval_status": rag_response.status,
                    "best_score": f"{rag_response.best_score:.4f}",
                    "overlap": str(self._max_overlap(post_input.question, rag_response)),
                },
            )

        if "posso emitir" in post_input.candidate_response.lower():
            return self._decision(
                stage="policy_post",
                decision="fallback",
                reason_codes=["POLICY_POST_RESPONSE_REWRITE"],
                summary="A resposta candidata extrapolou o papel informativo do assistente.",
                metadata={"matched_rule": "rewrite_transactional_claim"},
            )

        return self._decision(
            stage="policy_post",
            decision="allow",
            reason_codes=[],
            summary="Resposta candidata manteve aderencia ao contexto e ao escopo institucional.",
            metadata={
                "retrieval_status": rag_response.status,
                "best_score": f"{rag_response.best_score:.4f}",
            },
        )

    def _decision(
        self,
        *,
        stage: str,
        decision: str,
        reason_codes: list[str],
        summary: str,
        metadata: dict[str, str],
    ) -> PolicyDecision:
        return PolicyDecision(
            stage=stage,
            decision=decision,
            reason_codes=reason_codes,
            policy_version=self.policy_version,
            summary=summary,
            metadata=metadata,
        )

    def _matches_any(self, text: str, patterns: list[re.Pattern[str]]) -> bool:
        return any(pattern.search(text) for pattern in patterns)

    def _max_overlap(self, question: str, rag_response: RagQueryResponse) -> int:
        tokens = {
            token
            for token in re.findall(r"[a-zA-Z0-9à-ÿÀ-ß]{4,}", question.lower())
            if token not in {"qual", "como", "onde", "agora", "centro"}
        }
        max_overlap = 0
        for chunk in rag_response.chunks:
            haystack = f"{chunk.title} {chunk.text}".lower()
            overlap = sum(1 for token in tokens if token in haystack)
            if overlap > max_overlap:
                max_overlap = overlap
        return max_overlap
