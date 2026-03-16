#!/usr/bin/env python3
"""Diagnostica o fluxo Telegram -> tenant -> RAG -> fallback sem alterar o runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.contracts.dto import RagQueryRequest  # noqa: E402
from app.llmops import ActiveArtifactResolver  # noqa: E402
from app.services.chat_service import ChatService  # noqa: E402
from app.services.rag_service import RagService  # noqa: E402
from app.services.telegram_service import (  # noqa: E402
    TelegramService,
    TelegramTenantResolutionError,
)
from app.services.tenant_profile_service import TenantProfileService  # noqa: E402
from app.settings import settings  # noqa: E402
from app.storage.chroma_repository import TenantChromaRepository  # noqa: E402
from app.storage.document_repository import FileDocumentRepository  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Le os argumentos minimos do diagnostico."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chat-id", default="", help="Chat ID do Telegram para resolver tenant.")
    parser.add_argument("--tenant-id", default="", help="Tenant explicito para inspecao.")
    parser.add_argument(
        "--message",
        default="Qual o horario da Central de Atendimento ao Cidadao?",
        help="Mensagem de teste para inspecionar retrieval e fallback.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Top-k usado na consulta de diagnostico.",
    )
    return parser.parse_args()


def main() -> None:
    """Executa o diagnostico e imprime um JSON curto com o estado observado."""

    args = parse_args()
    artifact_resolver = ActiveArtifactResolver()
    document_repository = FileDocumentRepository()
    chroma_repository = TenantChromaRepository(artifact_resolver=artifact_resolver)
    rag_service = RagService(
        document_repository=document_repository,
        chroma_repository=chroma_repository,
        artifact_resolver=artifact_resolver,
    )
    telegram_service = TelegramService()
    tenant_profile_service = TenantProfileService()
    chat_service = ChatService(
        rag_service=rag_service,
        artifact_resolver=artifact_resolver,
    )
    policy_guard = chat_service.policy_guard

    resolved_telegram_tenant = None
    tenant_resolution_error = ""
    if args.chat_id:
        try:
            resolved_telegram_tenant = telegram_service._resolve_tenant(args.chat_id)
        except TelegramTenantResolutionError as exc:
            tenant_resolution_error = str(exc)

    effective_tenant = (args.tenant_id or resolved_telegram_tenant or "").strip()

    payload: dict[str, object] = {
        "settings": {
            "env": settings.ENV,
            "knowledge_base_dir": settings.KNOWLEDGE_BASE_DIR,
            "chroma_dir": settings.CHROMA_DIR,
            "telegram_delivery_mode": settings.TELEGRAM_DELIVERY_MODE,
            "telegram_default_tenant_id": settings.TELEGRAM_DEFAULT_TENANT_ID,
            "telegram_chat_tenant_map": settings.TELEGRAM_CHAT_TENANT_MAP,
            "telegram_bot_token_configured": bool(settings.TELEGRAM_BOT_TOKEN),
            "telegram_webhook_secret_configured": bool(settings.TELEGRAM_WEBHOOK_SECRET),
            "rag_retriever_version": settings.RAG_RETRIEVER_VERSION,
            "llm_provider": settings.LLM_PROVIDER,
            "llm_min_context_score": settings.LLM_MIN_CONTEXT_SCORE,
        },
        "telegram_resolution": {
            "chat_id": args.chat_id,
            "resolved_tenant_id": resolved_telegram_tenant,
            "error": tenant_resolution_error,
        },
        "effective_tenant_id": effective_tenant or None,
        "retrieval_artifact": {
            "version": artifact_resolver.resolve_retrieval_config().version,
            "version_id": artifact_resolver.resolve_retrieval_config().version_id,
            "phase5_experimental_config": artifact_resolver.resolve_phase5_experimental_config().as_payload(),
        },
        "collections": {
            "available": chroma_repository.list_collection_names(),
        },
    }

    if not effective_tenant:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    rag_status = rag_service.status(effective_tenant)
    documents = document_repository.list_documents(effective_tenant)
    query_response = rag_service.query(
        RagQueryRequest(
            tenant_id=effective_tenant,
            query=args.message,
            top_k=args.top_k,
            min_score=0.0,
            boost_enabled=False,
        )
    )
    tenant_profile = tenant_profile_service.get_profile(effective_tenant)
    pre_decision = policy_guard.evaluate_pre(args.message, tenant_profile)
    post_decision = policy_guard.evaluate_post(
        SimpleNamespace(
            question=args.message,
            candidate_response="diagnostic-placeholder",
            rag_response=query_response,
        ),
        pre_decision=pre_decision,
    )

    if pre_decision.decision != "allow":
        effective_fallback_cause = f"policy_pre:{','.join(pre_decision.reason_codes)}"
    elif query_response.status == "knowledge_base_not_loaded":
        effective_fallback_cause = "rag_status:knowledge_base_not_loaded"
    elif query_response.status != "ready":
        effective_fallback_cause = f"rag_status:{query_response.status}"
    elif post_decision.decision != "allow":
        effective_fallback_cause = f"policy_post:{','.join(post_decision.reason_codes)}"
    else:
        effective_fallback_cause = "no_fallback_detected"

    payload["tenant_runtime"] = {
        "tenant_id": effective_tenant,
        "collection_name": chroma_repository.collection_name(effective_tenant),
        "documents_count": len(documents),
        "chunks_count": chroma_repository.count_chunks(effective_tenant),
        "rag_status": rag_status.model_dump(mode="json"),
    }
    payload["diagnostic_query"] = {
        "message": args.message,
        "retrieval_status": query_response.status,
        "retrieval_message": query_response.message,
        "best_score": query_response.best_score,
        "retrieved_titles": [chunk.title for chunk in query_response.chunks],
        "pre_policy": pre_decision.model_dump(mode="json"),
        "post_policy": post_decision.model_dump(mode="json"),
        "effective_fallback_cause": effective_fallback_cause,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
