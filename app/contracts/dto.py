from datetime import datetime, timezone
from typing import Any
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_optional_identifier(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized


def _normalize_required_text(value: Any, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{field_name} obrigatória")
    return normalized


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        items = str(value).split(",")
    normalized_items: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in normalized_items:
            normalized_items.append(normalized)
    return normalized_items


def _normalize_string_mapping(value: Any) -> dict[str, str]:
    if value in (None, ""):
        return {}
    if not isinstance(value, dict):
        raise ValueError("valor deve ser um objeto")

    normalized_mapping: dict[str, str] = {}
    for key, item in value.items():
        normalized_key = str(key).strip()
        normalized_item = str(item).strip()
        if normalized_key and normalized_item:
            normalized_mapping[normalized_key] = normalized_item
    return normalized_mapping


class ChatRequest(BaseModel):
    tenant_id: Optional[str] = Field(
        default=None,
        description="Tenant explicito do request. Obrigatorio para o chat direto.",
    )
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000)
    channel: str = "web"

    @field_validator("tenant_id", mode="before")
    @classmethod
    def normalize_tenant_id(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_identifier(value)

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        return _normalize_required_text(value, "message")


class WebhookChatRequest(BaseModel):
    tenant_id: Optional[str] = Field(
        default=None,
        description="Tenant explicito do webhook. Se ausente, deve ser resolvido por page_id.",
    )
    page_id: Optional[str] = Field(
        default=None,
        description="Identificador externo usado para resolver o tenant no webhook.",
    )
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000)
    channel: str = "webhook"

    @field_validator("tenant_id", "page_id", mode="before")
    @classmethod
    def normalize_identifiers(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_identifier(value)

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        return _normalize_required_text(value, "message")


class ChatResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    tenant_id: str
    message: str
    channel: str = "web"


class ChatExchangeRecord(BaseModel):
    request_id: str
    tenant_id: str
    session_id: str
    channel: str
    user_message: str
    assistant_message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PolicyDecision(BaseModel):
    stage: str
    decision: str
    reason_codes: list[str] = Field(default_factory=list)
    policy_version: str
    summary: str
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("stage", mode="before")
    @classmethod
    def normalize_stage(cls, value: Any) -> str:
        normalized = _normalize_required_text(value, "stage").lower()
        if normalized not in {"policy_pre", "policy_post"}:
            raise ValueError("stage deve ser policy_pre ou policy_post")
        return normalized

    @field_validator("decision", mode="before")
    @classmethod
    def normalize_decision(cls, value: Any) -> str:
        normalized = _normalize_required_text(value, "decision").lower()
        if normalized not in {"allow", "block", "fallback", "review"}:
            raise ValueError("decision deve ser allow, block, fallback ou review")
        return normalized

    @field_validator("policy_version", "summary", mode="before")
    @classmethod
    def normalize_required_fields(cls, value: Any, info) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("reason_codes", mode="before")
    @classmethod
    def normalize_reason_codes(cls, value: Any) -> list[str]:
        return _normalize_string_list(value)

    @field_validator("metadata", mode="before")
    @classmethod
    def normalize_metadata(cls, value: Any) -> dict[str, str]:
        return _normalize_string_mapping(value)


class AuditEventRecord(BaseModel):
    schema_version: str = "audit.v1"
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    request_id: str
    tenant_id: str
    session_id: str
    channel: str = "web"
    event_type: str
    policy_decision: Optional[PolicyDecision] = None
    payload: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("schema_version", "request_id", "tenant_id", "session_id", "channel", "event_type", mode="before")
    @classmethod
    def normalize_string_fields(cls, value: Any, info) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("payload", mode="before")
    @classmethod
    def normalize_payload(cls, value: Any) -> dict[str, str]:
        return _normalize_string_mapping(value)


class RagDocumentCreateRequest(BaseModel):
    tenant_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=20000)
    keywords: list[str] = Field(default_factory=list)
    intents: list[str] = Field(default_factory=list)

    @field_validator("tenant_id", mode="before")
    @classmethod
    def normalize_tenant_id(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_identifier(value)

    @field_validator("title", "content", mode="before")
    @classmethod
    def normalize_required_fields(cls, value: str, info) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("keywords", "intents", mode="before")
    @classmethod
    def normalize_tags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value)


class RagDocumentUpdateRequest(BaseModel):
    tenant_id: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1, max_length=20000)
    keywords: Optional[list[str]] = None
    intents: Optional[list[str]] = None

    @field_validator("tenant_id", mode="before")
    @classmethod
    def normalize_tenant_id(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_identifier(value)

    @field_validator("title", "content", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Optional[str], info) -> Optional[str]:
        if value is None:
            return None
        return _normalize_required_text(value, info.field_name)

    @field_validator("keywords", "intents", mode="before")
    @classmethod
    def normalize_optional_tags(cls, value: Any) -> Optional[list[str]]:
        if value is None:
            return None
        return _normalize_string_list(value)


class RagDocumentRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    title: str
    content: str
    keywords: list[str] = Field(default_factory=list)
    intents: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RagDocumentSummary(BaseModel):
    id: str
    tenant_id: str
    title: str
    file: str
    tags: list[str]
    intents: list[str]
    updated_at: datetime


class RagDocumentContent(BaseModel):
    id: str
    tenant_id: str
    title: str
    file: str
    content: str
    keywords: list[str]
    intents: list[str]
    created_at: datetime
    updated_at: datetime


class RagDocumentListResponse(BaseModel):
    tenant_id: str
    source_dir: str
    collection_name: str
    ready: bool
    documents_count: int
    chunks_count: int
    last_ingested_at: Optional[datetime] = None
    documents: list[RagDocumentSummary]


class RagIngestRequest(BaseModel):
    tenant_id: Optional[str] = None
    reset_collection: bool = True

    @field_validator("tenant_id", mode="before")
    @classmethod
    def normalize_tenant_id(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_identifier(value)


class RagIngestResponse(BaseModel):
    tenant_id: str
    collection_name: str
    source_dir: str
    documents_count: int
    chunks_count: int
    ready: bool
    reset_collection: bool
    last_ingested_at: Optional[datetime] = None
    message: str


class RagResetRequest(BaseModel):
    tenant_id: Optional[str] = None
    purge_documents: bool = False
    remove_legacy_collections: bool = True

    @field_validator("tenant_id", mode="before")
    @classmethod
    def normalize_tenant_id(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_identifier(value)


class RagResetResponse(BaseModel):
    tenant_id: str
    collection_name: str
    removed_collections: list[str]
    removed_documents_count: int
    source_dir: str
    message: str


class RagStatusResponse(BaseModel):
    tenant_id: str
    collection_name: str
    source_dir: str
    documents_count: int
    chunks_count: int
    ready: bool
    last_ingested_at: Optional[datetime] = None
    message: str


class RagQueryRequest(BaseModel):
    tenant_id: Optional[str] = None
    query: str = Field(..., min_length=1, max_length=2000)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    top_k: int = Field(default=5, ge=1, le=20)
    boost_enabled: bool = False
    strategy_name: Optional[str] = None
    query_transform_strategy_name: Optional[str] = None
    rerank_strategy_name: Optional[str] = None

    @field_validator(
        "tenant_id",
        "strategy_name",
        "query_transform_strategy_name",
        "rerank_strategy_name",
        mode="before",
    )
    @classmethod
    def normalize_optional_identifiers(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_identifier(value)

    @field_validator("query", mode="before")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        return _normalize_required_text(value, "query")


class RagRetrievedChunk(BaseModel):
    id: str
    text: str
    source: str
    title: str
    section: str
    score: float
    retrieval_score: Optional[float] = None
    rerank_score: Optional[float] = None
    tags: list[str]


class RagQueryTransformationUsed(BaseModel):
    strategy_name: str
    applied: bool
    original_query: str
    retrieval_query: str
    added_terms: list[str] = Field(default_factory=list)
    source_fields: list[str] = Field(default_factory=list)
    max_added_terms: int


class RagRerankingUsed(BaseModel):
    strategy_name: str
    applied: bool
    input_query: str
    reranked_candidates: int
    total_candidates: int
    max_candidates: int
    score_weights: dict[str, float] = Field(default_factory=dict)


class RagQueryParamsUsed(BaseModel):
    min_score: float
    top_k: int
    boost_enabled: bool
    collection: str
    strategy_name: str
    query_transformation: RagQueryTransformationUsed
    reranking: RagRerankingUsed


class RagQueryResponse(BaseModel):
    tenant_id: str
    query: str
    status: str
    message: str
    chunks: list[RagRetrievedChunk]
    total_chunks: int
    best_score: float
    params_used: RagQueryParamsUsed


class TelegramUser(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    is_bot: Optional[bool] = None
    first_name: Optional[str] = None
    username: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, value: Any) -> str:
        return _normalize_required_text(value, "id")

    @field_validator("first_name", "username", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_identifier(value)


class TelegramChat(BaseModel):
    id: str
    type: str = "private"
    title: Optional[str] = None
    username: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, value: Any) -> str:
        return _normalize_required_text(value, "id")

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, value: Any) -> str:
        return _normalize_required_text(value or "private", "type")

    @field_validator("title", "username", mode="before")
    @classmethod
    def normalize_optional_fields(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_identifier(value)


class TelegramMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message_id: str
    date: Optional[int] = None
    chat: TelegramChat
    from_user: Optional[TelegramUser] = Field(default=None, alias="from")
    text: Optional[str] = None

    @field_validator("message_id", mode="before")
    @classmethod
    def normalize_message_id(cls, value: Any) -> str:
        return _normalize_required_text(value, "message_id")

    @field_validator("text", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return _normalize_required_text(value, "text")


class TelegramWebhookRequest(BaseModel):
    update_id: str
    message: Optional[TelegramMessage] = None
    edited_message: Optional[TelegramMessage] = None

    @field_validator("update_id", mode="before")
    @classmethod
    def normalize_update_id(cls, value: Any) -> str:
        return _normalize_required_text(value, "update_id")


class TelegramWebhookResponse(BaseModel):
    ok: bool = True
    status: str
    request_id: Optional[str] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    channel: str = "telegram"
    update_id: str
    chat_id: Optional[str] = None
    inbound_message_id: Optional[str] = None
    outbound_status: Optional[str] = None
    detail: Optional[str] = None
