from pathlib import Path

from scripts.run_phase5_strategy_comparison import (
    build_default_phase5_matrix,
    build_phase5_comparison_summary,
)


def test_phase5_strategy_matrix_contains_expected_default_variants() -> None:
    matrix = build_default_phase5_matrix()

    assert [variant.label for variant in matrix] == [
        "baseline_semantic_only",
        "hybrid_lexical_only",
        "hybrid_plus_query_transform",
        "hybrid_plus_rerank",
        "hybrid_plus_query_transform_plus_rerank",
    ]


def test_phase5_strategy_comparison_summary_computes_deltas_from_baseline() -> None:
    summary = build_phase5_comparison_summary(
        experiment_name="fase5-test-experiment",
        manifest_path=Path("/tmp/manifest.json"),
        selected_case_ids=[],
        max_cases=None,
        results=[
            {
                "label": "baseline_semantic_only",
                "retrieval_strategy_name": "baseline",
                "query_transform_strategy_name": "no_query",
                "rerank_strategy_name": "no_rerank",
                "run_id": "run-001",
                "metrics": {
                    "faithfulness_mean": 0.4,
                    "answer_relevance_mean": 0.5,
                    "expected_context_coverage_mean": 0.6,
                    "retrieval_empty_rate": 0.2,
                    "total_latency_ms": 100.0,
                },
            },
            {
                "label": "hybrid_lexical_only",
                "retrieval_strategy_name": "hybrid",
                "query_transform_strategy_name": "no_query",
                "rerank_strategy_name": "no_rerank",
                "run_id": "run-002",
                "metrics": {
                    "faithfulness_mean": 0.45,
                    "answer_relevance_mean": 0.55,
                    "expected_context_coverage_mean": 0.65,
                    "retrieval_empty_rate": 0.1,
                    "total_latency_ms": 130.0,
                },
            },
        ],
    )

    assert summary["baseline_reference"]["label"] == "baseline_semantic_only"
    assert summary["results"][1]["deltas_vs_baseline"]["faithfulness_mean"] == 0.05
    assert summary["results"][1]["deltas_vs_baseline"]["answer_relevance_mean"] == 0.05
    assert summary["results"][1]["deltas_vs_baseline"]["expected_context_coverage_mean"] == 0.05
    assert summary["results"][1]["deltas_vs_baseline"]["retrieval_empty_rate"] == -0.1
    assert summary["results"][1]["deltas_vs_baseline"]["total_latency_ms"] == 30.0
