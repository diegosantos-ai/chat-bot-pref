from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.contracts.dto import ChatRequest, ChatResponse

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest) -> ChatResponse:
    if not chat_request.tenant_id or not chat_request.tenant_id.strip():
        raise HTTPException(status_code=400, detail="tenant_id obrigatório")

    if not chat_request.message.strip():
        raise HTTPException(status_code=400, detail="message obrigatória")

    session_id = chat_request.session_id or str(uuid4())
    tenant_id = chat_request.tenant_id.strip()

    return ChatResponse(
        session_id=session_id,
        tenant_id=tenant_id,
        message=f"Fluxo mínimo ativo para o tenant '{tenant_id}'.",
        channel=chat_request.channel,
    )
