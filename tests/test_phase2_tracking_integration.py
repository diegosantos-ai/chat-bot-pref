from app.llmops import ActiveArtifactResolver
from app.llmops.tracking_integration import build_phase2_tracking_run
from app.rag.query_transformation import (
    NO_QUERY_TRANSFORM_STRATEGY_NAME,
    TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME,
)
from app.rag.retrieval_scoring import (
    BASELINE_RETRIEVAL_STRATEGY_NAME,
    HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
)
from app.settings import settings


def test_phase2_tracking_run_uses_active_versions_and_metadata() -> None:
    resolver = ActiveArtifactResolver()

    tracking_run = build_phase2_tracking_run(
        tenant_id="prefeitura-demo",
        request_id="req-phase2-track-001",
        dataset_version="dataset.phase2.v1",
        artifact_resolver=resolver,
    )

    assert tracking_run.run_contract.tenant_id == "prefeitura-demo"
    assert tracking_run.run_contract.prompt_version == settings.PROMPT_BASE_VERSION
    assert tracking_run.run_contract.policy_version == settings.POLICY_TEXT_VERSION
    assert tracking_run.run_contract.retriever_version == settings.RAG_RETRIEVER_VERSION
    assert tracking_run.run_contract.retrieval_strategy_name == BASELINE_RETRIEVAL_STRATEGY_NAME
    assert tracking_run.run_contract.query_transform_strategy_name == NO_QUERY_TRANSFORM_STRATEGY_NAME
    assert tracking_run.run_contract.embedding_version == settings.RAG_EMBEDDING_VERSION
    assert tracking_run.run_contract.top_k == settings.LLM_CONTEXT_TOP_K
    assert tracking_run.as_params()["chunking_version"] == resolver.resolve_chunking_config().version
    assert tracking_run.as_tags()["prompt_version_id"] == resolver.resolve_composer_prompt().version_id
    assert tracking_run.as_tags()["policy_version_id"] == resolver.resolve_policy_text().version_id
    assert tracking_run.as_tags()["retriever_version_id"] == resolver.resolve_retrieval_config().version_id


def test_phase2_tracking_run_supports_fallback_prompt_version() -> None:
    resolver = ActiveArtifactResolver()

    tracking_run = build_phase2_tracking_run(
        tenant_id="prefeitura-demo",
        request_id="req-phase2-track-002",
        dataset_version="dataset.phase2.v1",
        prompt_version=settings.PROMPT_FALLBACK_VERSION,
        artifact_resolver=resolver,
    )

    assert tracking_run.run_contract.prompt_version == settings.PROMPT_FALLBACK_VERSION
    assert tracking_run.as_tags()["prompt_version_id"] == resolver.resolve_fallback_prompt().version_id
    assert tracking_run.as_artifact_payload()["chunking_version_id"] == resolver.resolve_chunking_config().version_id


def test_phase2_tracking_run_supports_retrieval_strategy_override() -> None:
    resolver = ActiveArtifactResolver()

    tracking_run = build_phase2_tracking_run(
        tenant_id="prefeitura-demo",
        request_id="req-phase2-track-003",
        dataset_version="dataset.phase2.v1",
        retrieval_strategy_name=HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
        artifact_resolver=resolver,
    )

    assert (
        tracking_run.run_contract.retrieval_strategy_name
        == HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME
    )
    assert (
        tracking_run.as_params()["retrieval_strategy_name"]
        == HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME
    )


def test_phase2_tracking_run_supports_query_transform_strategy_override() -> None:
    resolver = ActiveArtifactResolver()

    tracking_run = build_phase2_tracking_run(
        tenant_id="prefeitura-demo",
        request_id="req-phase2-track-004",
        dataset_version="dataset.phase2.v1",
        query_transform_strategy_name=TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME,
        artifact_resolver=resolver,
    )

    assert (
        tracking_run.run_contract.query_transform_strategy_name
        == TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME
    )
    assert (
        tracking_run.as_params()["query_transform_strategy_name"]
        == TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME
    )
