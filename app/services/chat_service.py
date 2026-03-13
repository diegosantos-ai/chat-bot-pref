import asyncio
from uuid import uuid4

from app.contracts.dto import (
    AuditEventRecord,
    ChatExchangeRecord,
    ChatRequest,
    ChatResponse,
    RagQueryRequest,
)
from app.services.rag_service import RagService
from app.storage.audit_repository import FileAuditRepository
from app.storage.chat_repository import FileChatRepository
from app.tenant_context import require_tenant


class ChatService:
    def __init__(
        self,
        repository: FileChatRepository | None = None,
        audit_repository: FileAuditRepository | None = None,
        rag_service: RagService | None = None,
    ) -> None:
        self.repository = repository or FileChatRepository()
        self.audit_repository = audit_repository or FileAuditRepository()
        self.rag_service = rag_service or RagService()

    async def process(self, chat_request: ChatRequest) -> ChatResponse:
        tenant_id = await self._resolve_active_tenant()
        request_id = str(uuid4())
        session_id = chat_request.session_id or str(uuid4())

        self.audit_repository.append_event(
            AuditEventRecord(
                request_id=request_id,
                tenant_id=tenant_id,
                session_id=session_id,
                event_type="chat_request_received",
                payload={
                    "channel": chat_request.channel,
                    "message": chat_request.message,
                },
            )
        )

        rag_response = self.rag_service.query(
            RagQueryRequest(
                tenant_id=tenant_id,
                query=chat_request.message,
                top_k=1,
                min_score=0.1,
            )
        )

        if rag_response.status == "ready":
            retrieval_event_type = "chat_retrieval_completed"
            response_message = (
                f"Fluxo mínimo ativo para o tenant '{tenant_id}'. "
                f"Contexto recuperado: {rag_response.chunks[0].text}"
            )
            retrieval_payload = {
                "channel": chat_request.channel,
                "collection_name": rag_response.params_used.collection,
                "retrieved_count": str(rag_response.total_chunks),
                "top_document_id": rag_response.chunks[0].id,
                "top_excerpt": self._truncate(rag_response.chunks[0].text),
                "status": rag_response.status,
            }
        else:
            retrieval_event_type = "chat_retrieval_unavailable"
            response_message = rag_response.message
            retrieval_payload = {
                "channel": chat_request.channel,
                "collection_name": rag_response.params_used.collection,
                "retrieved_count": "0",
                "top_document_id": "",
                "top_excerpt": "",
                "status": rag_response.status,
            }

        response = ChatResponse(
            request_id=request_id,
            session_id=session_id,
            tenant_id=tenant_id,
            message=response_message,
            channel=chat_request.channel,
        )

        self.audit_repository.append_event(
            AuditEventRecord(
                request_id=response.request_id,
                tenant_id=tenant_id,
                session_id=session_id,
                event_type=retrieval_event_type,
                payload=retrieval_payload,
            )
        )

        exchange_record = ChatExchangeRecord(
            request_id=response.request_id,
            tenant_id=tenant_id,
            session_id=session_id,
            channel=chat_request.channel,
            user_message=chat_request.message,
            assistant_message=response.message,
        )
        self.repository.append_exchange(exchange_record)

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

    async def _resolve_active_tenant(self) -> str:
        await asyncio.sleep(0)
        return require_tenant()

    def _truncate(self, text: str) -> str:
        normalized = text.replace("\n", " ").strip()
        if len(normalized) <= 160:
            return normalized
        return f"{normalized[:157]}..."
