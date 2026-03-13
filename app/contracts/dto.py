"""
Contratos de Dados (DTOs) — Pilot Atendimento MVE
==================================================
Versão: v1.2
Escopo: MVE_PILOT
Status: EXPANDIDO para Fase 3 (Auditoria E2E)

Define os objetos de entrada e saída da API.
Inclui modelos de auditoria para testes E2E.
"""

from typing import Optional
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field

from app.contracts.enums import (
    Intent,
    Decision,
    ResponseType,
    PolicyDecision,
    PolicyReason,
    FallbackReason,
    Channel,
    SurfaceType,
    AuditEventType,
)


# ========================================
# DTOs de Entrada (Normalizado)
# ========================================


class NormalizedInboundEvent(BaseModel):
    """
    Evento de entrada normalizado.
    Usado internamente após parsing do webhook Meta ou web widget.
    """

    # Identificação
    external_message_id: str = Field(
        ..., description="ID único da mensagem na plataforma (idempotência)"
    )
    session_id: str = Field(
        ...,
        description="ID da sessão (gerado: {channel}:{thread_id} ou {channel}:{post_id}:{author})",
    )

    # Canal e superfície
    channel: Channel = Field(..., description="Canal de origem")
    surface_type: SurfaceType = Field(
        ..., description="Tipo de superfície (inbox/public_comment)"
    )

    # Conteúdo
    text: str = Field(
        default="",
        max_length=2000,
        description="Texto da mensagem (pode ser vazio se só mídia)",
    )
    has_media: bool = Field(default=False, description="Indica se há anexos/mídia")

    # IDs da plataforma (DM)
    thread_id: Optional[str] = Field(
        default=None, description="ID do thread de DM (Instagram/Facebook)"
    )

    # IDs da plataforma (Comentários)
    post_id: Optional[str] = Field(
        default=None, description="ID do post (para comentários)"
    )
    comment_id: Optional[str] = Field(default=None, description="ID do comentário")
    parent_comment_id: Optional[str] = Field(
        default=None, description="ID do comentário pai (se for resposta)"
    )

    # Autor
    author_platform_id: str = Field(
        ..., description="ID do usuário na plataforma (não é PII)"
    )


class ChatRequest(BaseModel):
    """
    Requisição de chat do usuário.
    Usado pelo web widget e como base para processamento.
    """

    session_id: str = Field(
        ...,
        description="Identificador único da sessão de conversa",
        examples=["sess_abc123", "instagram_dm:123456789"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Mensagem do usuário",
        examples=["Qual o horário de funcionamento?"],
    )

    # Campos opcionais para canais externos
    channel: Channel = Field(default=Channel.WEB_WIDGET, description="Canal de origem")
    surface_type: SurfaceType = Field(
        default=SurfaceType.INBOX, description="Tipo de superfície"
    )
    external_message_id: Optional[str] = Field(
        default=None, description="ID externo para idempotência"
    )

    # Campos para comentários públicos
    post_id: Optional[str] = Field(
        default=None, description="ID do post (para comentários)"
    )
    comment_id: Optional[str] = Field(default=None, description="ID do comentário")


# ========================================
# DTOs de Saída
# ========================================


class ChatResponse(BaseModel):
    """Resposta do chatbot para o usuário."""

    session_id: str = Field(..., description="Identificador da sessão")
    message: str = Field(..., description="Resposta do bot")
    intent: Intent = Field(..., description="Intenção classificada do usuário")
    decision: Decision = Field(..., description="Decisão tomada pelo orquestrador")
    response_type: ResponseType = Field(..., description="Tipo da resposta entregue")
    base_id: Optional[str] = Field(
        default=None,
        description="ID da base RAG utilizada (quando aplicável)",
        examples=["BA-RAG-PILOTO-2026.01.v1"],
    )

    # Campos para canais externos
    channel: Channel = Field(default=Channel.WEB_WIDGET, description="Canal de origem")
    surface_type: SurfaceType = Field(
        default=SurfaceType.INBOX, description="Tipo de superfície"
    )

    # Campos de auditoria
    docs_found: Optional[bool] = Field(
        default=None, description="Se RAG encontrou documentos"
    )
    fallback_used: bool = Field(default=False, description="Se usou fallback")
    sources: list[str] = Field(
        default_factory=list, description="Fontes usadas na resposta"
    )
    fallback_reason: Optional[FallbackReason] = Field(
        default=None, description="Motivo do fallback, se aplicável"
    )


# ========================================
# DTOs de Auditoria (Pipeline Events)
# ========================================


class ClassifierResult(BaseModel):
    """Resultado da classificação de intent."""

    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    raw_output: Optional[str] = None


class PolicyPreResult(BaseModel):
    """Resultado da avaliação de policy PRÉ-processamento."""

    policy_decision: PolicyDecision
    reason: PolicyReason = PolicyReason.OK
    allowed_content: Optional[str] = None  # ex: "contact_or_location_only"
    details: Optional[dict] = None


class PolicyPostResult(BaseModel):
    """Resultado da avaliação de policy PÓS-processamento."""

    no_clinical_advice: bool = True
    content_validated: bool = True
    details: Optional[dict] = None


class RAGRetrieveResult(BaseModel):
    """Resultado da busca RAG."""

    base_id: str
    query_id: str
    query_text_hash: str
    k: int
    docs_count: int
    docs_found: bool
    doc_ids: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    best_score: float = 0.0


class ResponseSelectedResult(BaseModel):
    """Resultado da seleção de resposta."""

    template: str  # ex: "rag_answer.txt", "public_ack.txt"
    decision: Decision
    response_type: ResponseType
    fallback_reason: Optional[FallbackReason] = None


class MessageSentResult(BaseModel):
    """Resultado do envio de mensagem."""

    surface: SurfaceType
    channel: Channel
    message_length: int
    sent_at: datetime = Field(default_factory=datetime.utcnow)


class PublicAckResult(BaseModel):
    """Resultado de ACK público (controle de não-repetição)."""

    choice_id: str  # ex: "ack_v1", "ack_v2"
    thread_id: Optional[str] = None
    post_id: Optional[str] = None


# ========================================
# Evento de Auditoria Unificado
# ========================================


class AuditEvent(BaseModel):
    """
    Evento de auditoria unificado.
    Cada etapa do pipeline gera um evento desse tipo.
    """

    request_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: AuditEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict = Field(default_factory=dict)


# ========================================
# Contexto de Request (Estado do Pipeline)
# ========================================


class RequestContext(BaseModel):
    """
    Contexto completo de um request através do pipeline.
    Acumula eventos de auditoria para persistência.
    """

    # Identificadores
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    external_message_id: Optional[str] = None
    session_id: str

    # Input
    surface: SurfaceType
    channel: Channel
    user_message: str

    # Thread info (para controle de ACK)
    thread_id: Optional[str] = None
    post_id: Optional[str] = None
    comment_id: Optional[str] = None

    # NLP - Análise de linguagem
    user_formality: Optional[str] = None  # formal, neutral, informal, very_informal
    sentiment: Optional[str] = (
        None  # very_positive, positive, neutral, negative, very_negative
    )
    emotion: Optional[str] = None  # joy, gratitude, anxiety, frustration, etc.
    needs_empathy: bool = False  # Se usuário precisa de resposta empática
    is_vulnerable: bool = (
        False  # Se é usuário vulnerável (gestante confusa, idoso, etc.)
    )
    tone_suggestion: Optional[str] = None  # Sugestão de tom para resposta
    expanded_query: Optional[str] = None  # Query expandida com sinônimos

    # Resultados do pipeline (preenchidos progressivamente)
    classifier_result: Optional[ClassifierResult] = None
    policy_pre: Optional[PolicyPreResult] = None
    rag_retrieve: Optional[RAGRetrieveResult] = None
    policy_post: Optional[PolicyPostResult] = None
    response_selected: Optional[ResponseSelectedResult] = None
    message_sent: Optional[MessageSentResult] = None
    public_ack: Optional[PublicAckResult] = None

    # Campos finais consolidados
    intent: Optional[Intent] = None
    confidence: Optional[float] = None
    policy_decision_pre: Optional[PolicyDecision] = None
    final_decision: Optional[Decision] = None
    response_type: Optional[ResponseType] = None
    response_message: Optional[str] = None
    base_id: Optional[str] = None
    docs_found: Optional[bool] = None
    fallback_used: bool = False

    # Eventos de auditoria
    audit_events: list[AuditEvent] = Field(default_factory=list)

    def add_event(self, event_type: AuditEventType, data: dict) -> None:
        """Adiciona um evento de auditoria."""
        self.audit_events.append(
            AuditEvent(
                request_id=self.request_id,
                event_type=event_type,
                data=data,
            )
        )

    def get_event(self, event_type: AuditEventType) -> Optional[AuditEvent]:
        """Retorna o primeiro evento do tipo especificado."""
        for event in self.audit_events:
            if event.event_type == event_type:
                return event
        return None

    def has_event(self, event_type: AuditEventType) -> bool:
        """Verifica se existe evento do tipo especificado."""
        return self.get_event(event_type) is not None
