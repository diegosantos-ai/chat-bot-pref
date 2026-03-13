from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


def _normalize_optional_identifier(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized


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
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("message obrigatória")
        return normalized


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
        normalized = str(value).strip()
        if not normalized:
            raise ValueError("message obrigatória")
        return normalized


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


class AuditEventRecord(BaseModel):
    request_id: str
    tenant_id: str
    session_id: str
    event_type: str
    payload: dict[str, str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
