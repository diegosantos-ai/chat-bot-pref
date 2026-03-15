import app.llmops.rag_evaluation as rag_evaluation
from app.llmops.benchmark_dataset import load_phase3_initial_baseline
from app.llmops.rag_evaluation import (
    PHASE4_INITIAL_COMPLEMENTARY_RAG_EVALUATION_METRICS,
    PHASE4_MANDATORY_RAG_EVALUATION_METRICS,
    RagEvaluationCaseInput,
    RagEvaluationLibraryAvailability,
    RagEvaluationLibraryName,
    RagEvaluationMetricName,
    build_rag_evaluation_case_result,
    build_rag_evaluation_run_summary,
    compute_expected_context_coverage,
    get_rag_evaluation_metric,
    resolve_rag_evaluation_stack,
)


def _load_case(case_id: str):
    dataset = load_phase3_initial_baseline()
    return next(case for case in dataset.cases if case.case_id == case_id)


def test_phase4_stack_resolution_prefers_ragas_over_other_available_libraries(monkeypatch) -> None:
    monkeypatch.setattr(
        rag_evaluation,
        "inspect_rag_evaluation_libraries",
        lambda: (
            RagEvaluationLibraryAvailability(
                library_name=RagEvaluationLibraryName.RAGAS,
                available=True,
                version="0.2.15",
                detail="ok",
            ),
            RagEvaluationLibraryAvailability(
                library_name=RagEvaluationLibraryName.DEEPEVAL,
                available=True,
                version="3.8.9",
                detail="ok",
            ),
        ),
    )

    resolution = resolve_rag_evaluation_stack()

    assert resolution.metric_library == RagEvaluationLibraryName.RAGAS
    assert resolution.metric_library_version == "0.2.15"
    assert resolution.tracking_target == "mlflow"


def test_phase4_metric_catalog_keeps_mandatory_and_complementary_contracts_explicit() -> None:
    mandatory_names = {metric.metric_name for metric in PHASE4_MANDATORY_RAG_EVALUATION_METRICS}
    complementary_names = {
        metric.metric_name for metric in PHASE4_INITIAL_COMPLEMENTARY_RAG_EVALUATION_METRICS
    }

    assert mandatory_names == {
        RagEvaluationMetricName.FAITHFULNESS,
        RagEvaluationMetricName.ANSWER_RELEVANCE,
    }
    assert complementary_names == {
        RagEvaluationMetricName.CONTEXT_PRECISION,
        RagEvaluationMetricName.CONTEXT_RECALL,
        RagEvaluationMetricName.EXPECTED_CONTEXT_COVERAGE,
        RagEvaluationMetricName.RETRIEVAL_EMPTY,
    }
    assert get_rag_evaluation_metric(
        RagEvaluationMetricName.ANSWER_RELEVANCE
    ).provider_metric_name == "answer_relevancy"


def test_phase4_case_contract_reuses_phase3_benchmark_and_derives_expected_context_coverage() -> None:
    benchmark_case = _load_case("vs-normal-001")
    case_input = RagEvaluationCaseInput(
        benchmark_case=benchmark_case,
        response="A Central de Atendimento funciona de segunda a sexta, das 8h as 17h.",
        retrieved_contexts=(
            "Central de atendimento presencial com expediente de segunda a sexta, das 8h as 17h.",
        ),
    )

    assert case_input.supports_metric(RagEvaluationMetricName.FAITHFULNESS)
    assert case_input.supports_metric(RagEvaluationMetricName.ANSWER_RELEVANCE)
    assert not case_input.supports_metric(RagEvaluationMetricName.CONTEXT_PRECISION)
    assert case_input.supports_metric(RagEvaluationMetricName.EXPECTED_CONTEXT_COVERAGE)
    assert compute_expected_context_coverage(case_input) == 1.0


def test_phase4_run_summary_aggregates_case_metrics_without_touching_runtime_contracts() -> None:
    answered_case = RagEvaluationCaseInput(
        benchmark_case=_load_case("vs-normal-002"),
        response="Leve documento com foto, CPF e comprovante de endereco ao protocolo geral.",
        retrieved_contexts=(
            "Para protocolo geral presencial sao exigidos documento com foto, CPF e comprovante de endereco.",
        ),
    )
    empty_case = RagEvaluationCaseInput(
        benchmark_case=_load_case("vs-baixa-confianca-001"),
        response="Nao encontrei contexto suficiente e recomendo buscar os canais oficiais.",
        retrieved_contexts=(),
    )

    summary = build_rag_evaluation_run_summary(
        tenant_id="prefeitura-vila-serena",
        dataset_version="benchmark_v1",
        case_results=(
            build_rag_evaluation_case_result(
                answered_case,
                faithfulness=0.82,
                answer_relevance=0.91,
            ),
            build_rag_evaluation_case_result(
                empty_case,
                answer_relevance=0.54,
            ),
        ),
        stack_resolution=rag_evaluation.RagEvaluationStackResolution(
            metric_library=RagEvaluationLibraryName.RAGAS,
            metric_library_version="0.2.15",
            tracking_target="mlflow",
            resolution_order=(RagEvaluationLibraryName.RAGAS, RagEvaluationLibraryName.DEEPEVAL),
        ),
    )

    assert summary.total_cases == 2
    assert summary.metric_library == RagEvaluationLibraryName.RAGAS
    assert summary.faithfulness_mean == 0.82
    assert summary.answer_relevance_mean == 0.725
    assert summary.expected_context_coverage_mean == 1.0
    assert summary.retrieval_empty_rate == 0.5
    assert summary.metric_case_counts["faithfulness"] == 1
    assert summary.metric_case_counts["retrieval_empty"] == 1
