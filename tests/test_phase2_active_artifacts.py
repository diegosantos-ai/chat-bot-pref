import json
from pathlib import Path

from app.contracts.dto import RagDocumentRecord
from app.llmops import ActiveArtifactResolver, PHASE2_ARTIFACT_CATALOG, build_content_hash
from app.llmops import build_version_id
from app.rag.query_transformation import (
    NO_QUERY_TRANSFORM_STRATEGY_NAME,
    TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME,
)
from app.rag.reranking import (
    HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME,
    NO_RERANK_STRATEGY_NAME,
)
from app.rag.retrieval_scoring import (
    BASELINE_RETRIEVAL_STRATEGY_NAME,
    HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
)
from app.services.prompt_service import PromptService
from app.services.rag_service import RagService
from app.settings import settings
from app.storage.chroma_repository import TenantChromaRepository


def _write_metadata_sidecar(
    artifact_path: Path,
    *,
    artifact_type: str,
    artifact_name: str,
    version_label: str,
) -> None:
    content_hash = build_content_hash(artifact_path)
    version_id = build_version_id(
        artifact_type=artifact_type,
        artifact_name=artifact_name,
        version_label=version_label,
        content_hash=content_hash,
    )
    metadata_path = artifact_path.with_suffix(f"{artifact_path.suffix}.meta.json")
    metadata_path.write_text(
        json.dumps(
            {
                "artifact_type": artifact_type,
                "artifact_name": artifact_name,
                "version_label": version_label,
                "version_id": version_id,
                "content_hash": content_hash,
                "status": "candidate",
                "created_at": "2026-03-15T00:00:00Z",
                "notes": "Artefato temporário para validação do fallback local.",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def test_active_artifact_resolver_loads_runtime_versions_and_metadata() -> None:
    resolver = ActiveArtifactResolver()

    composer = resolver.resolve_composer_prompt()
    fallback = resolver.resolve_fallback_prompt()
    policy = resolver.resolve_policy_text()
    retrieval = resolver.resolve_retrieval_config()
    chunking = resolver.resolve_chunking_config()
    experimental_config = resolver.resolve_phase5_experimental_config()

    assert composer.version == settings.PROMPT_BASE_VERSION
    assert fallback.version == settings.PROMPT_FALLBACK_VERSION
    assert policy.version == settings.POLICY_TEXT_VERSION
    assert retrieval.version == settings.RAG_RETRIEVER_VERSION
    assert retrieval.payload["top_k_default"] == settings.LLM_CONTEXT_TOP_K
    assert retrieval.payload["embedding_version"] == settings.RAG_EMBEDDING_VERSION
    assert resolver.retrieval_strategy_name() == BASELINE_RETRIEVAL_STRATEGY_NAME
    assert resolver.retrieval_supported_strategy_names() == (
        BASELINE_RETRIEVAL_STRATEGY_NAME,
        HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
    )
    assert resolver.query_transform_strategy_name() == NO_QUERY_TRANSFORM_STRATEGY_NAME
    assert resolver.query_transform_supported_strategy_names() == (
        NO_QUERY_TRANSFORM_STRATEGY_NAME,
        TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME,
    )
    assert resolver.rerank_strategy_name() == NO_RERANK_STRATEGY_NAME
    assert resolver.rerank_supported_strategy_names() == (
        NO_RERANK_STRATEGY_NAME,
        HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME,
    )
    assert (
        resolver.resolve_retrieval_strategy_name(HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME)
        == HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME
    )
    assert (
        resolver.resolve_query_transform_strategy_name(TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME)
        == TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME
    )
    assert (
        resolver.resolve_rerank_strategy_name(HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME)
        == HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME
    )
    assert resolver.retrieval_candidate_pool_multiplier() == 3
    assert resolver.retrieval_score_weights().lexical == 0.75
    assert resolver.retrieval_score_weights().semantic == 0.25
    assert resolver.query_transformation_config().max_added_terms == 4
    assert resolver.query_transformation_config().source_fields == ("keywords",)
    assert resolver.reranking_config().max_candidates == 5
    assert resolver.reranking_config().score_weights.retrieval_score == 0.35
    assert experimental_config.retrieval.strategy_name == BASELINE_RETRIEVAL_STRATEGY_NAME
    assert experimental_config.query_transformation.strategy_name == NO_QUERY_TRANSFORM_STRATEGY_NAME
    assert experimental_config.reranking.strategy_name == NO_RERANK_STRATEGY_NAME
    assert experimental_config.retrieval.params["candidate_pool_multiplier"] == 3
    assert experimental_config.query_transformation.params["source_fields"] == ["keywords"]
    assert experimental_config.reranking.params["max_candidates"] == 5
    assert chunking.version == PHASE2_ARTIFACT_CATALOG.chunking_config.version
    assert chunking.payload["split_strategy"] == "double_newline_paragraphs"


def test_prompt_service_uses_versioned_active_artifacts_by_default() -> None:
    resolver = ActiveArtifactResolver()
    service = PromptService(artifact_resolver=resolver)

    base_prompt = service.load_base_prompt()
    fallback_prompt = service.load_fallback_prompt()
    policy_text = service.load_policy_text()

    assert base_prompt.path == resolver.resolve_composer_prompt().path
    assert fallback_prompt.path == resolver.resolve_fallback_prompt().path
    assert policy_text.path == resolver.resolve_policy_text().path
    assert build_content_hash(base_prompt.path) == resolver.resolve_composer_prompt().metadata.content_hash


def test_retrieval_top_k_default_falls_back_to_settings_when_config_key_is_missing(tmp_path) -> None:
    artifacts_dir = tmp_path / "ai_artifacts"
    descriptor = PHASE2_ARTIFACT_CATALOG.retrieval_config
    artifact_path = artifacts_dir / descriptor.relative_path
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "boost_enabled_default": False,
                "collection_strategy": "tenant_collection_name",
                "embedding_version": settings.RAG_EMBEDDING_VERSION,
                "min_score_default": 0.0,
                "query_transform_strategy_name": NO_QUERY_TRANSFORM_STRATEGY_NAME,
                "supported_query_transform_strategies": [
                    NO_QUERY_TRANSFORM_STRATEGY_NAME,
                    TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME,
                ],
                "rerank_strategy_name": NO_RERANK_STRATEGY_NAME,
                "supported_rerank_strategies": [
                    NO_RERANK_STRATEGY_NAME,
                    HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME,
                ],
                "scope": "tenant_aware",
                "strategy_name": BASELINE_RETRIEVAL_STRATEGY_NAME,
                "supported_strategies": [
                    BASELINE_RETRIEVAL_STRATEGY_NAME,
                    HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
                ],
                "vector_store": "chroma",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_metadata_sidecar(
        artifact_path,
        artifact_type=descriptor.artifact_type,
        artifact_name=descriptor.artifact_name,
        version_label=descriptor.version,
    )

    resolver = ActiveArtifactResolver(artifacts_dir=artifacts_dir)

    assert resolver.retrieval_top_k_default() == settings.LLM_CONTEXT_TOP_K
    assert resolver.retrieval_candidate_pool_multiplier() == 3
    assert resolver.retrieval_strategy_name() == BASELINE_RETRIEVAL_STRATEGY_NAME
    assert resolver.query_transform_strategy_name() == NO_QUERY_TRANSFORM_STRATEGY_NAME
    assert resolver.rerank_strategy_name() == NO_RERANK_STRATEGY_NAME


def test_rag_runtime_uses_active_chunking_and_retriever_versions(tmp_path) -> None:
    resolver = ActiveArtifactResolver()
    repository = TenantChromaRepository(base_dir=tmp_path / "chroma", artifact_resolver=resolver)
    service = RagService(chroma_repository=repository, artifact_resolver=resolver)

    chunks = service._build_chunks(
        [
            RagDocumentRecord(
                tenant_id="prefeitura-demo",
                title="Horario do Alvara",
                content="O atendimento ocorre das 8h às 17h.\n\nLeve documento com foto.",
                keywords=["alvara"],
                intents=["INFO_REQUEST"],
            )
        ]
    )

    assert [chunk.section for chunk in chunks] == ["section-1", "section-2"]
    assert repository.retriever_version() == settings.RAG_RETRIEVER_VERSION
    assert repository.embedding_version() == settings.RAG_EMBEDDING_VERSION
