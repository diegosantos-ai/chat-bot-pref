from app.llmops import ActiveArtifactResolver
from app.llmops.tracking_integration import build_phase2_tracking_run
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
