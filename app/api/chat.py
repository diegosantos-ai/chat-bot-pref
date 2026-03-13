from fastapi import APIRouter
from fastapi import HTTPException

from app.contracts.dto import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.tenant_context import clear_tenant, set_tenant

router = APIRouter(prefix="/api", tags=["Chat"])
chat_service = ChatService()


@router.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest) -> ChatResponse:
    if chat_request.tenant_id is None:
        raise HTTPException(status_code=400, detail="tenant_id obrigatório")

    set_tenant(chat_request.tenant_id)
    try:
        return chat_service.process(chat_request)
    finally:
        clear_tenant()
