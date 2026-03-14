import asyncio
from uuid import uuid4

from app.contracts.dto import (
    AuditEventRecord,
    ChatExchangeRecord,
    ChatRequest,
    ChatResponse,
    PolicyDecision,
    RagQueryParamsUsed,
    RagQueryRequest,
    RagQueryResponse,
)
from app.policy_guard.service import PolicyGuardService, PostPolicyInput
from app.services.llm_service import LLMComposeService, LLMGenerationResponse
from app.services.rag_service import RagService
from app.services.tenant_profile_service import TenantProfileService
from app.settings import settings
from app.storage.audit_repository import FileAuditRepository
from app.storage.chat_repository import FileChatRepository
from app.tenant_context import require_tenant


class ChatService:
    def __init__(
        self,
        repository: FileChatRepository | None = None,
        audit_repository: FileAuditRepository | None = None,
        rag_service: RagService | None = None,
        llm_service: LLMComposeService | None = None,
        policy_guard: PolicyGuardService | None = None,
        tenant_profile_service: TenantProfileService | None = None,
    ) -> None:
        self.repository = repository or FileChatRepository()
        self.audit_repository = audit_repository or FileAuditRepository()
        self.rag_service = rag_service or RagService()
        self.llm_service = llm_service or LLMComposeService()
        self.policy_guard = policy_guard or PolicyGuardService()
        self.tenant_profile_service = tenant_profile_service or TenantProfileService()

    async def process(
        self,
        chat_request: ChatRequest,
        *,
        request_id: str | None = None,
        session_id: str | None = None,
        audit_context: dict[str, str] | None = None,
    ) -> ChatResponse:
        tenant_id = await self._resolve_active_tenant()
        resolved_request_id = request_id or str(uuid4())
        resolved_session_id = session_id or chat_request.session_id or str(uuid4())
        normalized_audit_context = self._normalize_audit_context(audit_context)
        channel = chat_request.channel
        tenant_profile = self.tenant_profile_service.get_profile(tenant_id)

        self._append_event(
            request_id=resolved_request_id,
            tenant_id=tenant_id,
            session_id=resolved_session_id,
            channel=channel,
            event_type="chat_request_received",
            payload=self._build_audit_payload(
                {
                    "message": chat_request.message,
                    "bot_name": tenant_profile.bot_name,
                    "client_name": tenant_profile.client_name,
                },
                normalized_audit_context,
            ),
        )

        pre_decision = self.policy_guard.evaluate_pre(chat_request.message, tenant_profile)
        self._append_policy_event(
            request_id=resolved_request_id,
            tenant_id=tenant_id,
            session_id=resolved_session_id,
            channel=channel,
            event_type="policy_pre_evaluated",
            policy_decision=pre_decision,
            payload=self._build_audit_payload(
                {
                    "message": self._truncate(chat_request.message),
                },
                normalized_audit_context,
            ),
        )

        rag_response = self._build_empty_rag_response(tenant_id, chat_request.message)
        llm_result: LLMGenerationResponse
        initial_reason_code = ""

        if pre_decision.decision == "allow":
            rag_response = self.rag_service.query(
                RagQueryRequest(
                    tenant_id=tenant_id,
                    query=chat_request.message,
                    top_k=settings.LLM_CONTEXT_TOP_K,
                    min_score=0.0,
                    boost_enabled=False,
                )
            )
            self._append_retrieval_event(
                request_id=resolved_request_id,
                tenant_id=tenant_id,
                session_id=resolved_session_id,
                channel=channel,
                rag_response=rag_response,
                audit_context=normalized_audit_context,
            )

            if rag_response.status == "ready":
                llm_result = await self.llm_service.compose_answer(
                    tenant_profile=tenant_profile,
                    question=chat_request.message,
                    context_chunks=rag_response.chunks,
                )
            else:
                initial_reason_code = self._fallback_reason_from_rag(rag_response)
                llm_result = await self.llm_service.compose_fallback(
                    tenant_profile=tenant_profile,
                    question=chat_request.message,
                    reason_code=initial_reason_code,
                    policy_summary=rag_response.message,
                )
        else:
            self._append_event(
                request_id=resolved_request_id,
                tenant_id=tenant_id,
                session_id=resolved_session_id,
                channel=channel,
                event_type="chat_retrieval_skipped",
                payload=self._build_audit_payload(
                    {
                        "status": "policy_pre_blocked",
                        "reason_codes": self._join_reason_codes(pre_decision),
                    },
                    normalized_audit_context,
                ),
            )
            initial_reason_code = self._primary_reason_code(pre_decision)
            llm_result = await self.llm_service.compose_fallback(
                tenant_profile=tenant_profile,
                question=chat_request.message,
                reason_code=initial_reason_code,
                policy_summary=pre_decision.summary,
            )

        self._append_event(
            request_id=resolved_request_id,
            tenant_id=tenant_id,
            session_id=resolved_session_id,
            channel=channel,
            event_type="llm_composition_completed",
            payload=self._build_audit_payload(
                {
                    "provider": llm_result.provider,
                    "model": llm_result.model,
                    "prompt_version": llm_result.prompt_version,
                    "mode": llm_result.mode,
                },
                normalized_audit_context,
            ),
        )

        post_decision = self.policy_guard.evaluate_post(
            PostPolicyInput(
                question=chat_request.message,
                candidate_response=llm_result.message,
                rag_response=rag_response,
            ),
            pre_decision=pre_decision,
        )
        self._append_policy_event(
            request_id=resolved_request_id,
            tenant_id=tenant_id,
            session_id=resolved_session_id,
            channel=channel,
            event_type="policy_post_evaluated",
            policy_decision=post_decision,
            payload=self._build_audit_payload(
                {
                    "provider": llm_result.provider,
                    "prompt_version": llm_result.prompt_version,
                },
                normalized_audit_context,
            ),
        )

        final_llm_result = llm_result
        post_reason_code = self._primary_reason_code(post_decision)
        should_rewrite = post_decision.decision != "allow" and (
            llm_result.mode != "fallback" or post_reason_code != initial_reason_code
        )
        if should_rewrite:
            final_llm_result = await self.llm_service.compose_fallback(
                tenant_profile=tenant_profile,
                question=chat_request.message,
                reason_code=post_reason_code,
                policy_summary=post_decision.summary,
            )
            self._append_event(
                request_id=resolved_request_id,
                tenant_id=tenant_id,
                session_id=resolved_session_id,
                channel=channel,
                event_type="llm_response_rewritten",
                payload=self._build_audit_payload(
                    {
                        "provider": final_llm_result.provider,
                        "model": final_llm_result.model,
                        "prompt_version": final_llm_result.prompt_version,
                        "reason_codes": self._join_reason_codes(post_decision),
                    },
                    normalized_audit_context,
                ),
            )

        response = ChatResponse(
            request_id=resolved_request_id,
            session_id=resolved_session_id,
            tenant_id=tenant_id,
            message=final_llm_result.message,
            channel=channel,
        )

        exchange_record = ChatExchangeRecord(
            request_id=response.request_id,
            tenant_id=tenant_id,
            session_id=resolved_session_id,
            channel=channel,
            user_message=chat_request.message,
            assistant_message=response.message,
        )
        self.repository.append_exchange(exchange_record)

        self._append_event(
            request_id=response.request_id,
            tenant_id=tenant_id,
            session_id=resolved_session_id,
            channel=channel,
            event_type="chat_response_generated",
            payload=self._build_audit_payload(
                {
                    "message": response.message,
                    "provider": final_llm_result.provider,
                    "model": final_llm_result.model,
                    "prompt_version": final_llm_result.prompt_version,
                    "response_mode": final_llm_result.mode,
                    "policy_version": post_decision.policy_version,
                    "reason_codes": self._join_reason_codes(post_decision or pre_decision),
                },
                normalized_audit_context,
            ),
        )
        return response

    async def _resolve_active_tenant(self) -> str:
        await asyncio.sleep(0)
        return require_tenant()

    def _append_retrieval_event(
        self,
        *,
        request_id: str,
        tenant_id: str,
        session_id: str,
        channel: str,
        rag_response: RagQueryResponse,
        audit_context: dict[str, str],
    ) -> None:
        if rag_response.status == "ready":
            event_type = "chat_retrieval_completed"
            payload = {
                "collection_name": rag_response.params_used.collection,
                "retrieved_count": str(rag_response.total_chunks),
                "best_score": f"{rag_response.best_score:.4f}",
                "top_document_id": rag_response.chunks[0].id,
                "top_title": rag_response.chunks[0].title,
                "top_excerpt": self._truncate(rag_response.chunks[0].text),
                "status": rag_response.status,
            }
        else:
            event_type = "chat_retrieval_unavailable"
            payload = {
                "collection_name": rag_response.params_used.collection,
                "retrieved_count": "0",
                "best_score": f"{rag_response.best_score:.4f}",
                "top_document_id": "",
                "top_title": "",
                "top_excerpt": "",
                "status": rag_response.status,
            }

        self._append_event(
            request_id=request_id,
            tenant_id=tenant_id,
            session_id=session_id,
            channel=channel,
            event_type=event_type,
            payload=self._build_audit_payload(payload, audit_context),
        )

    def _append_policy_event(
        self,
        *,
        request_id: str,
        tenant_id: str,
        session_id: str,
        channel: str,
        event_type: str,
        policy_decision: PolicyDecision,
        payload: dict[str, str],
    ) -> None:
        self._append_event(
            request_id=request_id,
            tenant_id=tenant_id,
            session_id=session_id,
            channel=channel,
            event_type=event_type,
            payload=payload,
            policy_decision=policy_decision,
        )

    def _append_event(
        self,
        *,
        request_id: str,
        tenant_id: str,
        session_id: str,
        channel: str,
        event_type: str,
        payload: dict[str, str],
        policy_decision: PolicyDecision | None = None,
    ) -> None:
        self.audit_repository.append_event(
            AuditEventRecord(
                request_id=request_id,
                tenant_id=tenant_id,
                session_id=session_id,
                channel=channel,
                event_type=event_type,
                policy_decision=policy_decision,
                payload=payload,
            )
        )

    def _build_empty_rag_response(self, tenant_id: str, query: str) -> RagQueryResponse:
        return RagQueryResponse(
            tenant_id=tenant_id,
            query=query,
            status="policy_pre_blocked",
            message="Retrieval nao executado porque a policy_pre bloqueou o request.",
            chunks=[],
            total_chunks=0,
            best_score=0.0,
            params_used=RagQueryParamsUsed(
                min_score=0.0,
                top_k=settings.LLM_CONTEXT_TOP_K,
                boost_enabled=False,
                collection=self.rag_service.chroma_repository.collection_name(tenant_id),
            ),
        )

    def _fallback_reason_from_rag(self, rag_response: RagQueryResponse) -> str:
        if rag_response.status == "knowledge_base_not_loaded":
            return "NO_KNOWLEDGE_BASE"
        return "LOW_CONFIDENCE_RETRIEVAL"

    def _primary_reason_code(self, decision: PolicyDecision) -> str:
        if decision.reason_codes:
            return decision.reason_codes[0]
        return "POLICY_POST_RESPONSE_REWRITE"

    def _join_reason_codes(self, decision: PolicyDecision | None) -> str:
        if decision is None or not decision.reason_codes:
            return ""
        return ",".join(decision.reason_codes)

    def _truncate(self, text: str) -> str:
        normalized = text.replace("\n", " ").strip()
        if len(normalized) <= 160:
            return normalized
        return f"{normalized[:157]}..."

    def _normalize_audit_context(self, audit_context: dict[str, str] | None) -> dict[str, str]:
        if not audit_context:
            return {}
        return {
            str(key).strip(): str(value).strip()
            for key, value in audit_context.items()
            if str(key).strip() and str(value).strip()
        }

    def _build_audit_payload(
        self,
        payload: dict[str, str],
        audit_context: dict[str, str],
    ) -> dict[str, str]:
        merged = dict(payload)
        merged.update(audit_context)
        return merged
