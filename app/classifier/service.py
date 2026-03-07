"""
Classifier Service — Pilot Atendimento MVE
============================================
Classifica a intenção (intent) da mensagem do usuário usando LLM.

Responsabilidades:
- Analisar mensagem do usuário
- Determinar intent com confidence score
- Detectar padrões especiais (elogio, reclamação, etc.)
"""

import re
from typing import Optional
import json

from google import genai
from google.genai import types

from app.contracts.enums import Intent
from app.contracts.dto import ClassifierResult
from app.prompts import load_prompt
from app.settings import settings


# Padrões de detecção rápida (sem LLM)
GREETING_PATTERNS = [
    r"^\s*(oi|olá|ola|bom dia|boa tarde|boa noite|ei|hey|hello|hi)\s*[!?.]*\s*$",
    r"^\s*(oi|olá|ola)\s+tudo\s+(bem|bom)\s*[?!.]*\s*$",
]

COMPLIMENT_PATTERNS = [
    r"(parabéns|parabens|obrigad[oa]|muito bom|excelente|ótimo|otimo|maravilh|adorei|amei)",
    r"(bom trabalho|bom atendimento|continue assim|mandou bem|arrasou)",
    r"(vocês são|voces sao|você é|voce e).*(demais|incríve|incrivel|melhor)",
]

COMPLAINT_PATTERNS = [
    r"(reclamação|reclamacao|denúncia|denuncia|insatisf|péssimo|pessimo|horrível|horrivel)",
    r"(não funciona|nao funciona|não resolve|nao resolve|descaso|abandon)",
]

HUMAN_HANDOFF_PATTERNS = [
    r"(falar com|atendente|humano|pessoa real|alguém|alguem|funcionário|funcionario)",
    r"(quero reclamar|fazer reclamação|registrar|protocolo)",
]

TRANSACTIONAL_IPTU_PATTERNS = [
    r"(iptu|2a via iptu|segunda via iptu|boleto iptu|pagar iptu|imposto predial)",
]

TRANSACTIONAL_TICKET_PATTERNS = [
    r"(buraco na rua|abrir chamado|reportar problema|denunciar|entulho|lâmpada queimada|iluminação|poste|mato alto|vazamento)",
]


class ClassifierService:
    """
    Serviço de classificação de intent.

    Pipeline:
    1. Tenta detecção rápida por regex (GREETING, COMPLIMENT, COMPLAINT)
    2. Se não detectar, usa LLM para classificação
    """

    def __init__(
        self,
        model: Optional[str] = None,
        use_fast_detect: bool = True,
    ):
        # Use effective config (from admin panel) or fallback to settings
        if model is None:
            from app.settings import get_effective_rag_config

            effective_config = get_effective_rag_config()
            self.model = effective_config.get("model", settings.GEMINI_MODEL)
        else:
            self.model = model

        self.use_fast_detect = use_fast_detect
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def _fast_detect(self, message: str) -> Optional[ClassifierResult]:
        """
        Detecção rápida de intents comuns via regex.
        Retorna None se não encontrar padrão claro.
        """
        text = message.lower().strip()

        # Greeting (alta confiança para mensagens curtas)
        for pattern in GREETING_PATTERNS:
            if re.match(pattern, text, re.IGNORECASE):
                return ClassifierResult(
                    intent=Intent.GREETING,
                    confidence=0.95,
                    raw_output="fast_detect:greeting",
                )

        # Compliment
        for pattern in COMPLIMENT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ClassifierResult(
                    intent=Intent.COMPLIMENT,
                    confidence=0.90,
                    raw_output="fast_detect:compliment",
                )

        # Complaint
        for pattern in COMPLAINT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ClassifierResult(
                    intent=Intent.COMPLAINT,
                    confidence=0.85,
                    raw_output="fast_detect:complaint",
                )

        # IPTU
        for pattern in TRANSACTIONAL_IPTU_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ClassifierResult(
                    intent=Intent.TRANSACTIONAL_IPTU,
                    confidence=0.95,
                    raw_output="fast_detect:transactional_iptu",
                )

        # Abertura de Chamado (Zeladoria)
        for pattern in TRANSACTIONAL_TICKET_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ClassifierResult(
                    intent=Intent.TRANSACTIONAL_TICKET,
                    confidence=0.95,
                    raw_output="fast_detect:transactional_ticket",
                )

        # Human handoff
        for pattern in HUMAN_HANDOFF_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return ClassifierResult(
                    intent=Intent.HUMAN_HANDOFF,
                    confidence=0.85,
                    raw_output="fast_detect:human_handoff",
                )

        return None

    async def classify(self, message: str) -> ClassifierResult:
        """
        Classifica a intenção da mensagem.

        Args:
            message: Texto da mensagem do usuário

        Returns:
            ClassifierResult com intent e confidence
        """
        # 1. Tenta detecção rápida
        if self.use_fast_detect:
            fast_result = self._fast_detect(message)
            if fast_result:
                return fast_result

        # 2. Usa LLM para classificação
        return await self._classify_with_llm(message)

    async def _classify_with_llm(self, message: str) -> ClassifierResult:
        """Classifica usando LLM."""

        # Carrega prompt do classifier
        load_prompt("classifier")

        # Lista de intents válidos
        valid_intents = [intent.value for intent in Intent]

        # Monta mensagem
        user_message = f"""Classifique a seguinte mensagem de um cidadão para a Prefeitura Municipal:

MENSAGEM: "{message}"

INTENTS VÁLIDOS: {", ".join(valid_intents)}

Responda EXATAMENTE no formato:
INTENT: <intent>
CONFIDENCE: <0.0-1.0>

Exemplo de resposta:
INTENT: INFO_REQUEST
CONFIDENCE: 0.85"""

        try:
            client = self._get_client()
            response = await client.aio.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=user_message)],
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=settings.GEMINI_MAX_TOKENS,
                ),
            )
            raw_output = response.text or ""

            # Parse da resposta
            intent, confidence = self._parse_llm_response(raw_output)

            return ClassifierResult(
                intent=intent,
                confidence=confidence,
                raw_output=raw_output,
            )

        except Exception as e:
            # Fallback para OUT_OF_SCOPE em caso de erro
            return ClassifierResult(
                intent=Intent.OUT_OF_SCOPE,
                confidence=0.5,
                raw_output=f"error:{str(e)}",
            )

    def _parse_llm_response(self, response: str) -> tuple[Intent, float]:
        """
        Extrai intent e confidence da resposta do LLM.

        Suporta dois formatos:
        1. Texto: "INTENT: INFO_REQUEST\nCONFIDENCE: 0.85"
        2. JSON: {"intent": "INFO_REQUEST", "confidence": 0.85}

        Retorna (OUT_OF_SCOPE, 0.5) se não conseguir parsear.
        """

        # Tenta parsear como JSON primeiro
        try:
            # Remove possíveis markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]

            data = json.loads(clean_response)
            intent_str = data.get("intent", "").upper()
            confidence = float(data.get("confidence", 0.7))

            try:
                intent = Intent(intent_str)
                return intent, max(0.0, min(1.0, confidence))
            except ValueError:
                pass
        except (json.JSONDecodeError, TypeError, KeyError):
            pass

        # Fallback: formato texto "INTENT: xxx"
        intent_match = re.search(r"INTENT:\s*(\w+)", response, re.IGNORECASE)
        if not intent_match:
            return Intent.OUT_OF_SCOPE, 0.5

        intent_str = intent_match.group(1).upper()

        # Valida intent
        try:
            intent = Intent(intent_str)
        except ValueError:
            return Intent.OUT_OF_SCOPE, 0.5

        # Extrai CONFIDENCE
        confidence = 0.7  # Default
        conf_match = re.search(r"CONFIDENCE:\s*([\d.]+)", response, re.IGNORECASE)
        if conf_match:
            try:
                confidence = float(conf_match.group(1))
                confidence = max(0.0, min(1.0, confidence))  # Clamp 0-1
            except ValueError:
                pass

        return intent, confidence


# Instância padrão
_default_classifier: Optional[ClassifierService] = None


def get_classifier() -> ClassifierService:
    """Retorna instância padrão do classifier."""
    global _default_classifier
    if _default_classifier is None:
        _default_classifier = ClassifierService()
    return _default_classifier


async def classify(message: str) -> ClassifierResult:
    """Atalho para classificação rápida."""
    return await get_classifier().classify(message)


# CLI para testes
if __name__ == "__main__":
    import asyncio
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("Uso: python -m app.classifier.service '<mensagem>'")
            sys.exit(1)

        message = sys.argv[1]

        print(f"\n🔍 Classificando: '{message}'")
        print("-" * 50)

        result = await classify(message)

        print(f"📊 Intent: {result.intent.value}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Raw: {result.raw_output}")

    asyncio.run(main())
