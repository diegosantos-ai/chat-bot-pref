from app.observability.cost_estimation import (
    estimate_llm_operational_cost,
    estimate_retrieval_operational_cost,
)


def test_llm_cost_estimation_mock_provider_is_explicitly_non_billed() -> None:
    estimate = estimate_llm_operational_cost(
        provider="mock",
        input_text="Qual o horario da central?",
        output_text="A central atende das 8h as 17h.",
    )

    assert estimate.estimated_cost_usd == 0.0
    assert estimate.status == "non_billed"
    assert estimate.method == "mock_provider_non_billed_v1"
    assert estimate.input_tokens_estimated == 0
    assert estimate.output_tokens_estimated == 0


def test_llm_cost_estimation_non_mock_uses_heuristic_tokens() -> None:
    estimate = estimate_llm_operational_cost(
        provider="gemini",
        input_text="A" * 40,
        output_text="B" * 20,
    )

    assert estimate.status == "estimated"
    assert estimate.method == "chars_per_token_heuristic_v1"
    assert estimate.input_tokens_estimated >= 1
    assert estimate.output_tokens_estimated >= 1


def test_retrieval_cost_estimation_is_non_billed_in_local_runtime() -> None:
    estimate = estimate_retrieval_operational_cost()

    assert estimate.estimated_cost_usd == 0.0
    assert estimate.status == "non_billed"
    assert estimate.method == "local_chroma_runtime_non_billed_v1"
