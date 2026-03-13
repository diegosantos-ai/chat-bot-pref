"""
Contrato de Enums — Pilot Atendimento MVE
==========================================
Versão: v1.1
Escopo: MVE_PILOT
Status: EXPANDIDO para Fase 3

REGRAS:
- Intenção NÃO é serviço
- Decisão NÃO é resposta
- Default obrigatório: OUT_OF_SCOPE
"""

from enum import Enum


class Intent(str, Enum):
    """
    O que o usuário quer.
    Classificado pelo Classifier antes de qualquer decisão.
    """
    GREETING = "GREETING"
    COMPLIMENT = "COMPLIMENT"  # Elogio/agradecimento (especialmente em comentários públicos)
    INFO_REQUEST = "INFO_REQUEST"
    SCHEDULE_QUERY = "SCHEDULE_QUERY"
    CONTACT_REQUEST = "CONTACT_REQUEST"
    COMPLAINT = "COMPLAINT"  # Reclamação
    HUMAN_HANDOFF = "HUMAN_HANDOFF"
    TRANSACTIONAL_IPTU = "TRANSACTIONAL_IPTU" # Emissão de 2ª via IPTU (Mock GTM)
    TRANSACTIONAL_TICKET = "TRANSACTIONAL_TICKET" # Abertura de chamado (Mock GTM)
    OUT_OF_SCOPE = "OUT_OF_SCOPE"  # Default obrigatório


class Decision(str, Enum):
    """
    O que o sistema decide fazer.
    Determinado pelo Orchestrator APÓS Policy Guard.
    """
    ANSWER_RAG = "ANSWER_RAG"           # Resposta via RAG
    ANSWER_DIRECT = "ANSWER_DIRECT"     # Resposta direta (template)
    PUBLIC_ACK = "PUBLIC_ACK"           # Reconhecimento público (elogio)
    PUBLIC_REDIRECT = "PUBLIC_REDIRECT" # Redirecionar para inbox
    FALLBACK = "FALLBACK"               # Não encontrou informação
    ESCALATE = "ESCALATE"               # Encaminhar para humano
    NO_REPLY = "NO_REPLY"               # Silêncio (policy blocked)
    BLOCK = "BLOCK"                     # Bloqueado com mensagem


class ResponseType(str, Enum):
    """
    Como o usuário percebe a resposta.
    Representa o resultado final da interação.
    """
    SUCCESS = "SUCCESS"
    FALLBACK = "FALLBACK"
    BLOCKED = "BLOCKED"
    ESCALATED = "ESCALATED"
    NO_REPLY = "NO_REPLY"  # Nenhuma mensagem enviada
    ERROR = "ERROR"


class PolicyDecision(str, Enum):
    """
    Resultado da avaliação do Policy Guard.
    Executado ANTES da decisão do orquestrador.
    """
    ALLOW = "ALLOW"                     # Permite processamento normal
    ALLOW_LIMITED = "ALLOW_LIMITED"     # Permite apenas contato/localização (saúde clínica)
    REDIRECT = "REDIRECT"               # Redirecionar para inbox (público)
    NO_REPLY = "NO_REPLY"               # Silêncio total (blocked em público)
    BLOCK = "BLOCK"                     # Bloqueado com mensagem (inbox)


class PolicyReason(str, Enum):
    """
    Motivo da decisão do Policy Guard.
    Usado para auditoria e diagnóstico.
    """
    OK = "ok"
    OUT_OF_SCOPE = "out_of_scope"
    NO_DOCS_FOUND = "no_docs_found"
    HEALTH_CLINICAL_DETECTED = "health_clinical_detected"
    POLICY_BLOCKED = "policy_blocked"
    PROMPT_INJECTION = "prompt_injection"
    PII_DETECTED = "pii_detected"
    OFFENSIVE_CONTENT = "offensive_content"
    MESSAGE_TOO_LONG = "message_too_long"
    CRISIS_SUICIDE = "crisis_suicide"
    CRISIS_VIOLENCE = "crisis_violence"


class FallbackReason(str, Enum):
    """
    Motivo específico quando response_type = FALLBACK.
    Usado para diagnóstico e métricas.
    """
    OUT_OF_SCOPE = "out_of_scope"
    LOW_CONFIDENCE = "low_confidence"
    NO_DOCS_FOUND = "no_docs_found"
    POLICY_BLOCKED = "policy_blocked"


class Channel(str, Enum):
    """
    Canal de origem da mensagem.
    Identifica a plataforma de onde veio a interação.
    """
    WEB_WIDGET = "web_widget"
    INSTAGRAM_DM = "instagram_dm"
    INSTAGRAM_COMMENT = "instagram_comment"
    FACEBOOK_DM = "facebook_dm"
    FACEBOOK_COMMENT = "facebook_comment"


class SurfaceType(str, Enum):
    """
    Tipo de superfície da interação.
    Determina regras de resposta (público vs privado).
    """
    INBOX = "INBOX"                    # DMs, chat privado
    PUBLIC_COMMENT = "PUBLIC_COMMENT"  # Comentários públicos
    WEB = "WEB"                        # Web widget


class ResponseMode(str, Enum):
    """
    Modo de resposta do RAG/Formatter.
    Controla tamanho e formato da saída.
    """
    FULL = "full"           # Resposta completa (DM, web)
    BRIEF = "brief"         # Resposta resumida (comentários públicos)


class AuditEventType(str, Enum):
    """
    Tipos de eventos de auditoria.
    Cada etapa do pipeline gera um evento.
    """
    CLASSIFIER_RESULT = "classifier_result"
    POLICY_PRE = "policy_pre"
    POLICY_POST = "policy_post"
    RAG_RETRIEVE = "rag_retrieve"
    RESPONSE_SELECTED = "response_selected"
    MESSAGE_SENT = "message_sent"
    PUBLIC_ACK = "public_ack"


# Metadados do contrato (para validação/auditoria)
CONTRACT_META = {
    "version": "v1.0",
    "scope": "MVE_PILOT",
    "frozen_for_pilot": True,
}
