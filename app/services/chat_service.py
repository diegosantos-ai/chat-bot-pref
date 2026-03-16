import asyncio
from time import perf_counter
from uuid import uuid4

from opentelemetry.trace import Status, StatusCode

from app.contracts.dto import (
    AuditEventRecord,
    ChatExchangeRecord,
    ChatRequest,
    ChatResponse,
    PolicyDecision,
    RagQueryParamsUsed,
    RagQueryRequest,
    RagQueryResponse,
    RagRerankingUsed,
    RagQueryTransformationUsed,
)
from app.llmops import ActiveArtifactResolver
from app.observability.context import update_correlation_context
from app.observability.logging import log_event
from app.observability.metrics import (
    record_chat_request,
    record_llm_composition,
    track_pipeline_stage_latency,
    record_policy_decision,
    record_retrieval,
)
from app.observability.phase6_contracts import PipelineStageName
from app.observability.tracing import annotate_current_span, get_tracer
from app.policy_guard.service import PolicyGuardService, PostPolicyInput
from app.services.llm_service import LLMComposeService, LLMGenerationResponse
from app.services.prompt_service import PromptService
from app.services.rag_service import RagService
from app.services.tenant_profile_service import TenantProfileService
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
        artifact_resolver: ActiveArtifactResolver | None = None,
    ) -> None:
        self.artifact_resolver = artifact_resolver or ActiveArtifactResolver()
        self.repository = repository or FileChatRepository()
        self.audit_repository = audit_repository or FileAuditRepository()
        self.rag_service = rag_service or RagService(artifact_resolver=self.artifact_resolver)
        self.llm_service = llm_service or LLMComposeService(
            prompt_service=PromptService(artifact_resolver=self.artifact_resolver)
        )
        self.policy_guard = policy_guard or PolicyGuardService(
            artifact_resolver=self.artifact_resolver
        )
        self.tenant_profile_service = tenant_profile_service or TenantProfileService()
        self.tracer = get_tracer(__name__)

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
        update_correlation_context(
            request_id=resolved_request_id,
            tenant_id=tenant_id,
            session_id=resolved_session_id,
            channel=channel,
        )
        annotate_current_span(
            request_id=resolved_request_id,
            tenant_id=tenant_id,
            session_id=resolved_session_id,
            channel=channel,
        )
        record_chat_request(channel=channel)

        with self.tracer.start_as_current_span("chat.process") as process_span:
            annotate_current_span(
                request_id=resolved_request_id,
                tenant_id=tenant_id,
                session_id=resolved_session_id,
                channel=channel,
            )
            log_event(
                "chat.process.started",
                request_id=resolved_request_id,
                tenant_id=tenant_id,
                session_id=resolved_session_id,
                channel=channel,
                bot_name=tenant_profile.bot_name,
                client_name=tenant_profile.client_name,
            )

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

            with track_pipeline_stage_latency(
                tenant_id=tenant_id,
                stage_name=PipelineStageName.POLICY_PRE,
                channel=channel,
            ) as mark_policy_pre_status:
                with self.tracer.start_as_current_span("policy_pre") as policy_pre_span:
                    annotate_current_span(
                        request_id=resolved_request_id,
                        tenant_id=tenant_id,
                        session_id=resolved_session_id,
                        channel=channel,
                    )
                    pre_decision = self.policy_guard.evaluate_pre(chat_request.message, tenant_profile)
                    annotate_current_span(
                        policy_stage=pre_decision.stage,
                        decision=pre_decision.decision,
                        reason_codes=",".join(pre_decision.reason_codes),
                    )
                mark_policy_pre_status(pre_decision.decision)

            record_policy_decision(
                stage=pre_decision.stage,
                decision=pre_decision.decision,
                reason_codes=pre_decision.reason_codes,
                channel=channel,
            )
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
                with self.tracer.start_as_current_span("retrieval") as retrieval_span:
                    annotate_current_span(
                        request_id=resolved_request_id,
                        tenant_id=tenant_id,
                        session_id=resolved_session_id,
                        channel=channel,
                    )
                    rag_response = self.rag_service.query(
                        RagQueryRequest(
                            tenant_id=tenant_id,
                            query=chat_request.message,
                            top_k=self._active_top_k(),
                            min_score=0.0,
                            boost_enabled=False,
                        )
                    )
                    annotate_current_span(
                        retrieval_status=rag_response.status,
                        best_score=f"{rag_response.best_score:.4f}",
                    )

                record_retrieval(status=rag_response.status, channel=channel)
                self._append_retrieval_event(
                    request_id=resolved_request_id,
                    tenant_id=tenant_id,
                    session_id=resolved_session_id,
                    channel=channel,
                    rag_response=rag_response,
                    audit_context=normalized_audit_context,
                )

                if rag_response.status == "ready":
                    llm_result, llm_latency = await self._compose_with_span(
                        tenant_profile=tenant_profile,
                        question=chat_request.message,
                        context_chunks=rag_response.chunks,
                        channel=channel,
                    )
                else:
                    initial_reason_code = self._fallback_reason_from_rag(rag_response)
                    llm_result, llm_latency = await self._compose_fallback_with_span(
                        tenant_profile=tenant_profile,
                        question=chat_request.message,
                        reason_code=initial_reason_code,
                        policy_summary=rag_response.message,
                        channel=channel,
                        span_name="compose",
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
                llm_result, llm_latency = await self._compose_fallback_with_span(
                    tenant_profile=tenant_profile,
                    question=chat_request.message,
                    reason_code=initial_reason_code,
                    policy_summary=pre_decision.summary,
                    channel=channel,
                    span_name="compose",
                )

            record_llm_composition(
                provider=llm_result.provider,
                mode=llm_result.mode,
                channel=channel,
                latency_seconds=llm_latency,
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
                        "latency_ms": f"{llm_latency * 1000:.2f}",
                    },
                    normalized_audit_context,
                ),
            )

            with track_pipeline_stage_latency(
                tenant_id=tenant_id,
                stage_name=PipelineStageName.POLICY_POST,
                channel=channel,
            ) as mark_policy_post_status:
                with self.tracer.start_as_current_span("policy_post") as policy_post_span:
                    annotate_current_span(
                        request_id=resolved_request_id,
                        tenant_id=tenant_id,
                        session_id=resolved_session_id,
                        channel=channel,
                    )
                    post_decision = self.policy_guard.evaluate_post(
                        PostPolicyInput(
                            question=chat_request.message,
                            candidate_response=llm_result.message,
                            rag_response=rag_response,
                        ),
                        pre_decision=pre_decision,
                    )
                    annotate_current_span(
                        policy_stage=post_decision.stage,
                        decision=post_decision.decision,
                        reason_codes=",".join(post_decision.reason_codes),
                    )
                mark_policy_post_status(post_decision.decision)

            record_policy_decision(
                stage=post_decision.stage,
                decision=post_decision.decision,
                reason_codes=post_decision.reason_codes,
                channel=channel,
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
                final_llm_result, rewrite_latency = await self._compose_fallback_with_span(
                    tenant_profile=tenant_profile,
                    question=chat_request.message,
                    reason_code=post_reason_code,
                    policy_summary=post_decision.summary,
                    channel=channel,
                    span_name="compose.rewrite",
                )
                record_llm_composition(
                    provider=final_llm_result.provider,
                    mode=final_llm_result.mode,
                    channel=channel,
                    latency_seconds=rewrite_latency,
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
                            "latency_ms": f"{rewrite_latency * 1000:.2f}",
                        },
                        normalized_audit_context,
                    ),
                )

            with track_pipeline_stage_latency(
                tenant_id=tenant_id,
                stage_name=PipelineStageName.RESPONSE_FINAL,
                channel=channel,
            ):
                with self.tracer.start_as_current_span("response") as response_span:
                    annotate_current_span(
                        request_id=resolved_request_id,
                        tenant_id=tenant_id,
                        session_id=resolved_session_id,
                        channel=channel,
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

            process_span.set_status(Status(StatusCode.OK))
            log_event(
                "chat.process.completed",
                request_id=response.request_id,
                tenant_id=tenant_id,
                session_id=resolved_session_id,
                channel=channel,
                response_mode=final_llm_result.mode,
                provider=final_llm_result.provider,
                prompt_version=final_llm_result.prompt_version,
                reason_codes=post_decision.reason_codes or pre_decision.reason_codes,
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
        experimental_config = self.artifact_resolver.resolve_phase5_experimental_config()
        query_transformation_config = self.artifact_resolver.query_transformation_config()
        reranking_config = self.artifact_resolver.reranking_config()
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
                top_k=self._active_top_k(),
                boost_enabled=False,
                collection=self.rag_service.chroma_repository.collection_name(tenant_id),
                strategy_name=experimental_config.retrieval.strategy_name,
                experimental_axes=experimental_config.as_payload(),
                query_transformation=RagQueryTransformationUsed(
                    strategy_name=experimental_config.query_transformation.strategy_name,
                    applied=False,
                    original_query=query,
                    retrieval_query=query,
                    added_terms=[],
                    source_fields=list(query_transformation_config.source_fields),
                    max_added_terms=query_transformation_config.max_added_terms,
                ),
                reranking=RagRerankingUsed(
                    strategy_name=experimental_config.reranking.strategy_name,
                    applied=False,
                    input_query=query,
                    reranked_candidates=0,
                    total_candidates=0,
                    max_candidates=reranking_config.max_candidates,
                    score_weights={
                        "retrieval_score": reranking_config.score_weights.retrieval_score,
                        "title_overlap": reranking_config.score_weights.title_overlap,
                        "tag_overlap": reranking_config.score_weights.tag_overlap,
                        "text_density": reranking_config.score_weights.text_density,
                    },
                ),
            ),
        )

    def _active_top_k(self) -> int:
        """Resolve o `top_k` ativo do runtime a partir do artefato de retrieval."""

        return self.artifact_resolver.retrieval_top_k_default()

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

    async def _compose_with_span(
        self,
        *,
        tenant_profile,
        question: str,
        context_chunks,
        channel: str,
    ) -> tuple[LLMGenerationResponse, float]:
        started_at = perf_counter()
        with track_pipeline_stage_latency(
            tenant_id=tenant_profile.tenant_id,
            stage_name=PipelineStageName.COMPOSER,
            channel=channel,
        ) as mark_composer_status:
            with self.tracer.start_as_current_span("compose"):
                result = await self.llm_service.compose_answer(
                    tenant_profile=tenant_profile,
                    question=question,
                    context_chunks=context_chunks,
                )
                latency_seconds = perf_counter() - started_at
                annotate_current_span(
                    provider=result.provider,
                    model=result.model,
                    prompt_version=result.prompt_version,
                    mode=result.mode,
                    channel=channel,
                    latency_ms=f"{latency_seconds * 1000:.2f}",
                )
                mark_composer_status(result.mode)
                return result, latency_seconds

    async def _compose_fallback_with_span(
        self,
        *,
        tenant_profile,
        question: str,
        reason_code: str,
        policy_summary: str,
        channel: str,
        span_name: str,
    ) -> tuple[LLMGenerationResponse, float]:
        started_at = perf_counter()
        with track_pipeline_stage_latency(
            tenant_id=tenant_profile.tenant_id,
            stage_name=PipelineStageName.COMPOSER,
            channel=channel,
        ) as mark_composer_status:
            with self.tracer.start_as_current_span(span_name):
                result = await self.llm_service.compose_fallback(
                    tenant_profile=tenant_profile,
                    question=question,
                    reason_code=reason_code,
                    policy_summary=policy_summary,
                )
                latency_seconds = perf_counter() - started_at
                annotate_current_span(
                    provider=result.provider,
                    model=result.model,
                    prompt_version=result.prompt_version,
                    mode=result.mode,
                    channel=channel,
                    reason_code=reason_code,
                    latency_ms=f"{latency_seconds * 1000:.2f}",
                )
                mark_composer_status(result.mode)
                return result, latency_seconds

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
