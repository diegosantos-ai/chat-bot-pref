"""
Policy Guard Service — Pilot Atendimento MVE
=============================================
Avalia políticas de segurança e restrição ANTES e DEPOIS do processamento.

Responsabilidades:
- Detectar conteúdo bloqueado (prompt injection, PII, ofensivo)
- Detectar saúde clínica (limitar resposta a contato/localização)
- Aplicar regras de superfície (público vs privado)
- Validar resposta gerada (pós-processamento)
"""

import re
from typing import Optional

from app.contracts.enums import (
    Intent,
    PolicyDecision,
    PolicyReason,
    SurfaceType,
)
from app.contracts.dto import PolicyPreResult, PolicyPostResult
from app.settings import settings


# ========================================
# Padrões de Detecção
# ========================================

# Prompt injection / jailbreak
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|rules?|prompts?)",
    r"disregard\s+(all\s+)?(previous|above|prior)",
    r"you\s+are\s+now\s+(a|an|the)",
    r"pretend\s+(you\s+are|to\s+be)",
    r"act\s+as\s+(if|a|an)",
    r"new\s+instructions?:",
    r"system\s*:\s*you\s+are",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode",
]

# PII (Personally Identifiable Information) - Solicitação de dados pessoais
PII_REQUEST_PATTERNS = [
    r"(me\s+)?pass[ae]\s+(seu|teu|o)\s+(cpf|rg|cnh|titulo)",
    r"(qual|diga|fala|informa).*(seu|teu|o)\s+(cpf|rg|cnh)",
    r"(documento|identidade|cpf|rg).*(você|vc|tu)",
    r"dados\s+(pessoais|bancários|financeiros)",
    r"(número|numero)\s+(do\s+)?(cartão|cartao|conta)",
]

# Conteúdo ofensivo/inapropriado
OFFENSIVE_PATTERNS = [
    r"\b(idiota|imbecil|burr[oa]s?|estúpid[oa]s?|merda|porra|caralho)\b",
    r"\b(vagabund[oa]s?|ladr[aã]o?s?|ladrao?s?|corrupt[oa]s?|bandid[oa]s?)\b",
    r"(vou\s+te\s+|vamos\s+)(processar|denunciar|acabar|ferrar)",
    r"(você[s]?\s+são|vcs\s+são|vocês\s+são)\s+(uns?|uma?)\s+(bando|quadrilha)",
]

# Saúde clínica - termos que requerem resposta limitada
HEALTH_CLINICAL_PATTERNS = [
    r"\b(dor|doendo|machuc|ferid[oa]|sangr|vomit|diarreia|febre)\b",
    r"\b(sintoma|diagnóstico|diagnostico|doença|doenca|enferm)\b",
    r"\b(remédio|remedio|medicamento|medicação|medicacao|receita)\b",
    r"\b(médico|medico|doutor[a]?|dr[a]?\.|enfermeiro|enfermeira)\b",
    r"\b(emergência|emergencia|urgência|urgencia|socorro|grave)\b",
    r"\b(hospital|pronto.?socorro|upa|samu|ambulância|ambulancia)\b",
    r"\b(pressão|pressao|diabetes|coração|coracao|infarto|avc)\b",
    r"\b(gravidez|grávida|gravida|gestante|pré.?natal|prenatal)\b",
    r"\b(vacina|vacinação|vacinacao|imunização|imunizacao)\b",
    r"(o\s+que\s+faço|o\s+que\s+eu\s+faço|o\s+que\s+devo|como\s+tratar)",
    r"(preciso\s+de\s+atendimento|estou\s+(mal|passando\s+mal))",
]

# Temas fora do escopo institucional
OUT_OF_SCOPE_PATTERNS = [
    r"(casamento|casar|matrimônio|matrimonio)\s+(comunitário|comunitario|civil|religioso)",
    r"(concurso|prova|vestibular|enem)\s+(público|publico)?",
    r"(emprego|trabalho|vaga|contrat[ao]ção)",
    r"(política|politica|eleição|eleicao|voto|candidato)",
    r"(clima|tempo|previsão|previsao|temperatura)",
]

# Crise: Suicídio / Saúde Mental
CRISIS_SUICIDE_PATTERNS = [
    r"(quero|vou)\s+(me\s+)?(matar|suicidar|morrer|tirar\s+(a\s+)?minha\s+vida)",
    r"(pensando|pensamento)\s+em\s+(suicidio|suicídio|morte)",
    r"(não\s+aguento\s+mais|quero\s+sumir|desisto\s+de\s+viver)",
    r"(cortar\s+os\s+pulsos|envenenar|enforcar)",
    r"estou\s+(desesperad[oa]|no\s+limite|precisando\s+de\s+ajuda\s+urgente)",
]

# Crise: Violência Doméstica / Abuso
CRISIS_VIOLENCE_PATTERNS = [
    r"(ele|ela)\s+(me\s+)?(bateu|agrediu|espancou|ameaçou|violentou)",
    r"(sendo|fui)\s+(estuprad[oa]|abusad[oa]|violentad[oa])",
    r"(apanh[oei]|surra|soco|chute)\s+(do|da)\s+(marido|esposa|namorad[oa]|pai|mãe)",
    r"(violência|violencia)\s+(doméstica|domestica|contra\s+a\s+mulher)",
    r"(medida\s+protetiva|denunciar\s+agressão|preciso\s+esconder)",
]


class PolicyGuardService:
    """
    Serviço de avaliação de políticas.
    
    Fases:
    1. PRE: Avalia mensagem ANTES do processamento
    2. POST: Valida resposta DEPOIS do RAG
    """
    
    def __init__(self):
        self.max_message_length = settings.POLICY_MAX_MESSAGE_LENGTH
        self.public_max_length = settings.POLICY_PUBLIC_COMMENT_MAX_LENGTH
    
    def evaluate_pre(
        self,
        message: str,
        surface: SurfaceType,
        intent: Intent,
        docs_found: Optional[bool] = None,
    ) -> PolicyPreResult:
        """
        Avalia políticas ANTES do processamento.
        
        Args:
            message: Texto da mensagem do usuário
            surface: Tipo de superfície (INBOX/PUBLIC_COMMENT)
            intent: Intent classificado
            docs_found: Se RAG encontrou documentos (pode ser None se não executou)
            
        Returns:
            PolicyPreResult com decisão e motivo
        """
        text = message.lower()
        
        # 1. Verifica tamanho da mensagem
        if len(message) > self.max_message_length:
            return PolicyPreResult(
                policy_decision=PolicyDecision.BLOCK if surface == SurfaceType.INBOX else PolicyDecision.NO_REPLY,
                reason=PolicyReason.MESSAGE_TOO_LONG,
            )
        
        # 2. Detecta prompt injection
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return PolicyPreResult(
                    policy_decision=PolicyDecision.NO_REPLY if surface == SurfaceType.PUBLIC_COMMENT else PolicyDecision.BLOCK,
                    reason=PolicyReason.PROMPT_INJECTION,
                )
        
        # 3. Detecta solicitação de PII
        for pattern in PII_REQUEST_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return PolicyPreResult(
                    policy_decision=PolicyDecision.NO_REPLY if surface == SurfaceType.PUBLIC_COMMENT else PolicyDecision.BLOCK,
                    reason=PolicyReason.PII_DETECTED,
                )
        
        # 4. Detecta conteúdo ofensivo
        for pattern in OFFENSIVE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return PolicyPreResult(
                    policy_decision=PolicyDecision.NO_REPLY,
                    reason=PolicyReason.OFFENSIVE_CONTENT,
                )
        
        # 4.1 Detecta Crise (Suicídio)
        for pattern in CRISIS_SUICIDE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return PolicyPreResult(
                    policy_decision=PolicyDecision.BLOCK, # Block para forçar resposta estática
                    reason=PolicyReason.CRISIS_SUICIDE,
                )

        # 4.2 Detecta Crise (Violência)
        for pattern in CRISIS_VIOLENCE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return PolicyPreResult(
                    policy_decision=PolicyDecision.BLOCK, # Block para forçar resposta estática
                    reason=PolicyReason.CRISIS_VIOLENCE,
                )
        
        # 5. Detecta saúde clínica
        health_detected = False
        for pattern in HEALTH_CLINICAL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                health_detected = True
                break
        
        if health_detected:
            # Público: redirect
            if surface == SurfaceType.PUBLIC_COMMENT:
                return PolicyPreResult(
                    policy_decision=PolicyDecision.REDIRECT,
                    reason=PolicyReason.HEALTH_CLINICAL_DETECTED,
                    details={"public_health_redirect": True},
                )
            # Privado: permite apenas contato/localização
            return PolicyPreResult(
                policy_decision=PolicyDecision.ALLOW_LIMITED,
                reason=PolicyReason.HEALTH_CLINICAL_DETECTED,
                allowed_content="contact_or_location_only",
            )
        
        # 6. Verifica OUT_OF_SCOPE
        if intent == Intent.OUT_OF_SCOPE:
            # Público: silêncio (não expõe que não sabe responder)
            if surface == SurfaceType.PUBLIC_COMMENT:
                return PolicyPreResult(
                    policy_decision=PolicyDecision.NO_REPLY,
                    reason=PolicyReason.OUT_OF_SCOPE,
                )
            # Inbox: permite fallback (vai direcionar para prefeitura)
            return PolicyPreResult(
                policy_decision=PolicyDecision.ALLOW,
                reason=PolicyReason.OUT_OF_SCOPE,
            )
        
        # 7. Verifica se RAG não encontrou docs
        if docs_found is False:
            # Público: silêncio (não expõe fragilidade)
            if surface == SurfaceType.PUBLIC_COMMENT:
                return PolicyPreResult(
                    policy_decision=PolicyDecision.NO_REPLY,
                    reason=PolicyReason.NO_DOCS_FOUND,
                )
            # Inbox: permite fallback (vai direcionar para prefeitura)
            return PolicyPreResult(
                policy_decision=PolicyDecision.ALLOW,
                reason=PolicyReason.NO_DOCS_FOUND,
            )
        
        # 8. Permite processamento normal
        return PolicyPreResult(
            policy_decision=PolicyDecision.ALLOW,
            reason=PolicyReason.OK,
        )
    
    def evaluate_post(
        self,
        response_text: str,
        policy_pre: PolicyPreResult,
    ) -> PolicyPostResult:
        """
        Valida resposta DEPOIS do processamento.
        
        Verifica se a resposta respeita as restrições definidas no PRE.
        
        Args:
            response_text: Texto da resposta gerada
            policy_pre: Resultado da avaliação PRE
            
        Returns:
            PolicyPostResult com validação
        """
        details = {}
        
        # Se era ALLOW_LIMITED (saúde clínica), verifica se não há orientação clínica
        if policy_pre.policy_decision == PolicyDecision.ALLOW_LIMITED:
            # Padrões que indicam orientação clínica (proibido)
            clinical_advice_patterns = [
                r"(tome|tomar|usar|use|aplique|aplicar)\s+(o|a|um|uma|este|esta)",
                r"(você\s+deve|vc\s+deve|deveria|recomendo|sugiro|indicar)",
                r"(tratamento|terapia|procedimento)\s+(indicado|recomendado)",
                r"(faça|faca|realize|procure\s+fazer)",
            ]
            
            text = response_text.lower()
            for pattern in clinical_advice_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return PolicyPostResult(
                        no_clinical_advice=False,
                        content_validated=False,
                        details={"clinical_advice_detected": True},
                    )
            
            details["no_clinical_advice"] = True
        
        return PolicyPostResult(
            no_clinical_advice=True,
            content_validated=True,
            details=details,
        )
    
    def is_out_of_scope_by_pattern(self, message: str) -> bool:
        """
        Detecta se mensagem é claramente fora do escopo por padrão.
        Usado para classificação rápida.
        """
        text = message.lower()
        for pattern in OUT_OF_SCOPE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


# Instância padrão
_default_guard: Optional[PolicyGuardService] = None


def get_policy_guard() -> PolicyGuardService:
    """Retorna instância padrão do policy guard."""
    global _default_guard
    if _default_guard is None:
        _default_guard = PolicyGuardService()
    return _default_guard


def evaluate_pre(
    message: str,
    surface: SurfaceType,
    intent: Intent,
    docs_found: Optional[bool] = None,
) -> PolicyPreResult:
    """Atalho para avaliação PRE."""
    return get_policy_guard().evaluate_pre(message, surface, intent, docs_found)


def evaluate_post(
    response_text: str,
    policy_pre: PolicyPreResult,
) -> PolicyPostResult:
    """Atalho para avaliação POST."""
    return get_policy_guard().evaluate_post(response_text, policy_pre)


# CLI para testes
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Uso: python -m app.policy_guard.service '<mensagem>' <INBOX|PUBLIC_COMMENT>")
        sys.exit(1)
    
    message = sys.argv[1]
    surface = SurfaceType(sys.argv[2].upper())
    
    print(f"\n🔍 Avaliando: '{message}'")
    print(f"   Surface: {surface.value}")
    print("-" * 50)
    
    from app.contracts.enums import Intent
    result = evaluate_pre(message, surface, Intent.INFO_REQUEST)
    
    print(f"📊 Policy Decision: {result.policy_decision.value}")
    print(f"   Reason: {result.reason.value}")
    if result.allowed_content:
        print(f"   Allowed Content: {result.allowed_content}")
    if result.details:
        print(f"   Details: {result.details}")
