from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    tenant_id: Optional[str] = Field(
        default=None,
        description="Tenant explicito do request. Obrigatorio para o chat direto.",
    )
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000)
    channel: str = "web"


class ChatResponse(BaseModel):
    session_id: str
    tenant_id: str
    message: str
    channel: str = "web"
