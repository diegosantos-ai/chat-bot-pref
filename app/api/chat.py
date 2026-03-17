from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.contracts.dto import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from app.tenant_context import clear_tenant, set_tenant

router = APIRouter(prefix="/api", tags=["Chat"])
chat_service = ChatService()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    chat_request: ChatRequest,
    response: Response,
    request_id: str | None = Header(default=None, alias="X-Request-ID"),
    parent_run_id: str | None = Header(default=None, alias="X-Parent-Run-ID"),
    strategy_name: str | None = Header(default=None, alias="X-Strategy-Name"),
) -> ChatResponse:
    if chat_request.tenant_id is None:
        raise HTTPException(status_code=400, detail="tenant_id obrigatório")

    set_tenant(chat_request.tenant_id)
    try:
        audit_context = {
            "run_id": request_id,
            "parent_run_id": parent_run_id,
            "strategy_name": strategy_name,
        }
        chat_response = await chat_service.process(
            chat_request,
            request_id=request_id or getattr(request.state, "request_id", None),
            audit_context=audit_context,
        )
        response.headers["X-Request-ID"] = chat_response.request_id
        return chat_response
    finally:
        clear_tenant()
