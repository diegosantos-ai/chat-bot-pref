import pytest
from app.observability.metrics import (
    record_pipeline_fallback,
    record_pipeline_policy_block,
    record_pipeline_retrieval_empty,
    PIPELINE_FALLBACK_TOTAL,
    PIPELINE_POLICY_BLOCK_TOTAL,
    PIPELINE_RETRIEVAL_EMPTY_TOTAL,
    REGISTRY
)

def test_pipeline_fallback_metrics():
    before = REGISTRY.get_sample_value(
        "chatpref_pipeline_fallback_total",
        {"tenant_id": "test_tenant", "reason_code": "llm_error", "channel": "web"}
    ) or 0.0

    record_pipeline_fallback(tenant_id="test_tenant", reason_code="llm_error", channel="web")

    after = REGISTRY.get_sample_value(
        "chatpref_pipeline_fallback_total",
        {"tenant_id": "test_tenant", "reason_code": "llm_error", "channel": "web"}
    )
    assert after == before + 1.0


def test_pipeline_policy_block_metrics():
    before = REGISTRY.get_sample_value(
        "chatpref_pipeline_policy_block_total",
        {"tenant_id": "test_tenant", "stage": "policy_pre", "reason_code": "toxic", "channel": "telegram"}
    ) or 0.0

    record_pipeline_policy_block(tenant_id="test_tenant", stage="policy_pre", reason_codes=["toxic"], channel="telegram")

    after = REGISTRY.get_sample_value(
        "chatpref_pipeline_policy_block_total",
        {"tenant_id": "test_tenant", "stage": "policy_pre", "reason_code": "toxic", "channel": "telegram"}
    )
    assert after == before + 1.0


def test_pipeline_retrieval_empty_metrics():
    before = REGISTRY.get_sample_value(
        "chatpref_pipeline_retrieval_empty_total",
        {"tenant_id": "test_tenant", "channel": "web"}
    ) or 0.0

    record_pipeline_retrieval_empty(tenant_id="test_tenant", channel="web")

    after = REGISTRY.get_sample_value(
        "chatpref_pipeline_retrieval_empty_total",
        {"tenant_id": "test_tenant", "channel": "web"}
    )
    assert after == before + 1.0
