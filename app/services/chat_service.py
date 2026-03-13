import asyncio
from uuid import uuid4

from app.contracts.dto import (
    AuditEventRecord,
    ChatExchangeRecord,
    ChatRequest,
    ChatResponse,
)
from app.storage.audit_repository import FileAuditRepository
from app.storage.chat_repository import FileChatRepository
from app.storage.chroma_repository import RetrievedContext
from app.storage.chroma_repository import TenantChromaRepository
from app.tenant_context import require_tenant


class ChatService:
    def __init__(
        self,
        repository: FileChatRepository | None = None,
        audit_repository: FileAuditRepository | None = None,
        knowledge_repository: TenantChromaRepository | None = None,
    ) -> None:
        self.repository = repository or FileChatRepository()
        self.audit_repository = audit_repository or FileAuditRepository()
        self.knowledge_repository = knowledge_repository or TenantChromaRepository()

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

        retrieved_contexts = self.knowledge_repository.query_context(
            tenant_id=tenant_id,
            query_text=chat_request.message,
            limit=1,
        )

        response = ChatResponse(
            request_id=request_id,
            session_id=session_id,
            tenant_id=tenant_id,
            message=self._build_response_message(tenant_id, retrieved_contexts),
            channel=chat_request.channel,
        )

        self.audit_repository.append_event(
            AuditEventRecord(
                request_id=response.request_id,
                tenant_id=tenant_id,
                session_id=session_id,
                event_type="chat_retrieval_completed",
                payload={
                    "channel": chat_request.channel,
                    "collection_name": self.knowledge_repository.collection_name(tenant_id),
                    "retrieved_count": str(len(retrieved_contexts)),
                    "top_document_id": retrieved_contexts[0].document_id if retrieved_contexts else "",
                    "top_excerpt": self._format_context_excerpt(retrieved_contexts),
                },
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
        self.knowledge_repository.upsert_exchange(exchange_record)

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

    def _build_response_message(
        self,
        tenant_id: str,
        retrieved_contexts: list[RetrievedContext],
    ) -> str:
        message = f"Fluxo mínimo ativo para o tenant '{tenant_id}'."
        excerpt = self._format_context_excerpt(retrieved_contexts)
        if excerpt:
            return f"{message} Contexto recuperado: {excerpt}"
        return message

    def _format_context_excerpt(self, retrieved_contexts: list[RetrievedContext]) -> str:
        if not retrieved_contexts:
            return ""
        excerpt = retrieved_contexts[0].content.replace("\n", " ").strip()
        if len(excerpt) <= 160:
            return excerpt
        return f"{excerpt[:157]}..."
