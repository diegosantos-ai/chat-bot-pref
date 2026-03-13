from fastapi import APIRouter
from fastapi import HTTPException

from app.contracts.dto import ChatRequest, ChatResponse, WebhookChatRequest
from app.services.chat_service import ChatService
from app.tenant_context import clear_tenant, set_tenant
from app.tenant_resolver import TenantResolutionError, TenantResolver

router = APIRouter(prefix="/api", tags=["Webhook"])
chat_service = ChatService()
tenant_resolver = TenantResolver()


@router.post("/webhook", response_model=ChatResponse)
async def webhook_chat(webhook_request: WebhookChatRequest) -> ChatResponse:
    try:
        resolved_tenant = tenant_resolver.resolve_webhook_tenant(
            tenant_id=webhook_request.tenant_id,
            page_id=webhook_request.page_id,
        )
    except TenantResolutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    set_tenant(resolved_tenant)
    try:
        chat_request = ChatRequest(
            tenant_id=resolved_tenant,
            session_id=webhook_request.session_id,
            message=webhook_request.message,
            channel=webhook_request.channel,
        )
        return await chat_service.process(chat_request)
    finally:
        clear_tenant()
