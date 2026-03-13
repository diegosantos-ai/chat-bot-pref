from uuid import uuid4

from app.contracts.dto import (
    AuditEventRecord,
    ChatExchangeRecord,
    ChatRequest,
    ChatResponse,
)
from app.storage.audit_repository import FileAuditRepository
from app.storage.chat_repository import FileChatRepository
from app.tenant_context import require_tenant


class ChatService:
    def __init__(
        self,
        repository: FileChatRepository | None = None,
        audit_repository: FileAuditRepository | None = None,
    ) -> None:
        self.repository = repository or FileChatRepository()
        self.audit_repository = audit_repository or FileAuditRepository()

    def process(self, chat_request: ChatRequest) -> ChatResponse:
        tenant_id = require_tenant()
        session_id = chat_request.session_id or str(uuid4())
        response = ChatResponse(
            session_id=session_id,
            tenant_id=tenant_id,
            message=f"Fluxo mínimo ativo para o tenant '{tenant_id}'.",
            channel=chat_request.channel,
        )
        self.audit_repository.append_event(
            AuditEventRecord(
                request_id=response.request_id,
                tenant_id=tenant_id,
                session_id=session_id,
                event_type="chat_request_received",
                payload={
                    "channel": chat_request.channel,
                    "message": chat_request.message,
                },
            )
        )
        self.repository.append_exchange(
            ChatExchangeRecord(
                request_id=response.request_id,
                tenant_id=tenant_id,
                session_id=session_id,
                channel=chat_request.channel,
                user_message=chat_request.message,
                assistant_message=response.message,
            )
        )
        self.audit_repository.append_event(
            AuditEventRecord(
                request_id=response.request_id,
                tenant_id=tenant_id,
                session_id=session_id,
                event_type="chat_response_generated",
                payload={
                    "channel": response.channel,
                    "message": response.message,
                },
            )
        )
        return response
