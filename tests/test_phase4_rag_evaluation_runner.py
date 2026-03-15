"""Testes da execucao offline da Fase 4 com benchmark, avaliacao e tracking."""

import asyncio
import csv
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from mlflow.tracking import MlflowClient

from app.llmops.benchmark_dataset import PHASE3_INITIAL_BASELINE_MANIFEST
from app.llmops.rag_evaluation import (
    RagEvaluationCaseInput,
    RagEvaluationCaseResult,
    RagEvaluationLibraryName,
    RagEvaluationStackResolution,
    build_rag_evaluation_case_result,
)
from app.llmops.rag_evaluation_runner import (
    MlflowTrackingConfig,
    OfflineRagEvaluationExecutor,
    RagEvaluationCaseStatus,
)
from app.services.demo_tenant_service import DemoTenantService
from app.services.rag_service import RagService
from app.storage.chroma_repository import TenantChromaRepository
from app.storage.document_repository import FileDocumentRepository
from app.contracts.dto import RagIngestRequest


def _manifest_path() -> Path:
    """Retorna o manifest baseline da Fase 3 usado nos testes."""

    return PHASE3_INITIAL_BASELINE_MANIFEST


def _tenant_manifest_path() -> Path:
    """Retorna o tenant demonstrativo usado para bootstrap da base temporaria."""

    return (
        Path(__file__).resolve().parents[1]
        / "tenants"
        / "prefeitura-vila-serena"
        / "tenant.json"
    )


def _build_executor(
    tmp_path: Path,
    *,
    metric_evaluator: Any = None,
) -> OfflineRagEvaluationExecutor:
    """Constroi um executor isolado em diretorios temporarios do teste."""

    tracking_config = MlflowTrackingConfig(
        base_dir=tmp_path / "tracking",
        experiment_name="phase4-test-experiment",
    )
    document_repository = FileDocumentRepository(base_dir=tmp_path / "knowledge")
    chroma_repository = TenantChromaRepository(base_dir=tmp_path / "chroma")
    return OfflineRagEvaluationExecutor(
        document_repository=document_repository,
        chroma_repository=chroma_repository,
        tracking_config=tracking_config,
        experiment_name="phase4-test-experiment",
        metric_evaluator=metric_evaluator,
    )


def _bootstrap_demo_knowledge_base(tmp_path: Path) -> None:
    """Carrega e ingesta a base demonstrativa em storage temporario."""

    service = DemoTenantService()
    service.bootstrap_bundle(
        manifest_path=_tenant_manifest_path(),
        target_base_dir=tmp_path / "knowledge",
        purge_documents=True,
    )
    rag_service = RagService(
        document_repository=FileDocumentRepository(base_dir=tmp_path / "knowledge"),
        chroma_repository=TenantChromaRepository(base_dir=tmp_path / "chroma"),
    )
    rag_service.ingest(
        RagIngestRequest(tenant_id="prefeitura-vila-serena", reset_collection=True)
    )


def test_phase4_executor_connects_benchmark_to_offline_evaluation_and_aggregation(tmp_path) -> None:
    _bootstrap_demo_knowledge_base(tmp_path)
    executor = _build_executor(tmp_path)

    execution = asyncio.run(
        executor.execute_dataset(
            manifest_path=_manifest_path(),
            case_ids=("vs-normal-001", "vs-risco-policy-001"),
        )
    )

    assert len(execution.case_executions) == 2
    assert execution.summary.faithfulness_mean is not None
    assert execution.summary.answer_relevance_mean is not None
    assert execution.summary.expected_context_coverage_mean is not None
    assert execution.summary.retrieval_empty_rate == 0.5
    assert execution.evaluated_cases_count() == 1
    assert execution.partial_cases_count() == 1
    assert execution.skipped_cases_count() == 0

    case_map = {case.case_input.case_id: case for case in execution.case_executions}
    assert case_map["vs-normal-001"].status == RagEvaluationCaseStatus.EVALUATED
    assert case_map["vs-normal-001"].case_result.faithfulness is not None
    assert case_map["vs-normal-001"].case_result.answer_relevance is not None
    assert case_map["vs-risco-policy-001"].status == RagEvaluationCaseStatus.PARTIAL
    assert case_map["vs-risco-policy-001"].rag_status == "policy_pre_blocked"
    assert case_map["vs-risco-policy-001"].case_result.faithfulness is None
    assert case_map["vs-risco-policy-001"].case_result.answer_relevance is not None
    assert "faithfulness" in case_map["vs-risco-policy-001"].skipped_metrics


def test_phase4_executor_logs_minimum_tracking_run_in_mlflow(tmp_path) -> None:
    _bootstrap_demo_knowledge_base(tmp_path)
    executor = _build_executor(tmp_path)

    execution, logged_run = asyncio.run(
        executor.execute_and_track(
            manifest_path=_manifest_path(),
            case_ids=("vs-normal-001",),
        )
    )

    client = MlflowClient(tracking_uri=logged_run.tracking_uri)
    run = client.get_run(logged_run.run_id)

    assert run.data.tags["phase"] == "F4"
    assert run.data.tags["run_kind"] == "rag_formal_evaluation"
    assert run.data.tags["tenant_id"] == "prefeitura-vila-serena"
    assert run.data.tags["evaluator_library"] == "ragas"
    assert run.data.params["dataset_version"] == "benchmark_v1"
    assert run.data.params["evaluator_mode"] == "offline_heuristic_ragas"
    assert run.data.params["vectorstore_fingerprint"] == execution.vectorstore_fingerprint
    assert run.data.params["selected_cases_count"] == "1"
    assert run.data.metrics["cases_total"] == 1.0
    assert run.data.metrics["cases_evaluated"] == 1.0
    assert run.data.metrics["faithfulness_cases"] == 1.0
    assert run.data.metrics["answer_relevance_cases"] == 1.0
    assert "answer_relevance_mean" in run.data.metrics
    assert "faithfulness_mean" in run.data.metrics

    artifact_names = {item.path for item in client.list_artifacts(logged_run.run_id)}
    assert logged_run.report_path.name in artifact_names
    assert logged_run.comparison_snapshot_path.name in artifact_names
    assert logged_run.comparison_csv_path.name in artifact_names
    assert logged_run.case_ranking_path.name in artifact_names
    assert logged_run.baseline_summary_path.name in artifact_names
    assert logged_run.report_path.is_file()
    assert logged_run.comparison_snapshot_path.is_file()
    assert logged_run.comparison_csv_path.is_file()
    assert logged_run.case_ranking_path.is_file()
    assert logged_run.baseline_summary_path.is_file()


def test_phase4_executor_generates_comparison_artifacts_with_required_fields(tmp_path) -> None:
    _bootstrap_demo_knowledge_base(tmp_path)
    executor = _build_executor(tmp_path)

    _, first_logged_run = asyncio.run(
        executor.execute_and_track(
            manifest_path=_manifest_path(),
            case_ids=("vs-normal-001",),
        )
    )
    _, second_logged_run = asyncio.run(
        executor.execute_and_track(
            manifest_path=_manifest_path(),
            case_ids=("vs-normal-001", "vs-risco-policy-001"),
        )
    )

    comparison_snapshot = json.loads(
        second_logged_run.comparison_snapshot_path.read_text(encoding="utf-8")
    )
    case_ranking = json.loads(
        second_logged_run.case_ranking_path.read_text(encoding="utf-8")
    )
    baseline_summary = json.loads(
        second_logged_run.baseline_summary_path.read_text(encoding="utf-8")
    )

    assert comparison_snapshot["artifact_type"] == "comparison_snapshot"
    assert comparison_snapshot["experiment_name"] == "phase4-test-experiment"
    assert comparison_snapshot["tenant_id"] == "prefeitura-vila-serena"
    assert comparison_snapshot["runs_compared"] == 2
    assert "scores_from_offline_heuristic_ragas_are_not_external_semantic_judgments" in comparison_snapshot["methodology_notes"]

    rows_by_run_id = {row["run_id"]: row for row in comparison_snapshot["runs"]}
    assert first_logged_run.run_id in rows_by_run_id
    assert second_logged_run.run_id in rows_by_run_id

    first_row = rows_by_run_id[first_logged_run.run_id]
    second_row = rows_by_run_id[second_logged_run.run_id]
    for row in (first_row, second_row):
        assert row["tenant_id"] == "prefeitura-vila-serena"
        assert row["dataset_version"] == "benchmark_v1"
        assert row["evaluator_library"] == "ragas"
        assert row["evaluator_mode"] == "offline_heuristic_ragas"
        assert row["prompt_version"]
        assert row["policy_version"]
        assert row["retriever_version"]
        assert row["chunking_version"]
        assert row["vectorstore_fingerprint"]

    assert first_row["faithfulness_cases"] == 1
    assert second_row["cases_partial"] == 1
    assert second_row["cases_with_methodology_limitations"] == 2

    with second_logged_run.comparison_csv_path.open(encoding="utf-8", newline="") as csv_file:
        csv_rows = list(csv.DictReader(csv_file))
    assert len(csv_rows) == 2
    assert {"run_id", "tenant_id", "dataset_version", "vectorstore_fingerprint", "cases_partial"} <= set(
        csv_rows[0].keys()
    )

    assert case_ranking["artifact_type"] == "case_ranking"
    assert case_ranking["status_counts"]["evaluated"] == 1
    assert case_ranking["status_counts"]["partial"] == 1
    assert case_ranking["best_evaluated_cases"][0]["case_id"] == "vs-normal-001"
    assert case_ranking["non_evaluated_cases"][0]["case_id"] == "vs-risco-policy-001"

    assert baseline_summary["artifact_type"] == "baseline_summary"
    assert baseline_summary["tenant_id"] == "prefeitura-vila-serena"
    assert baseline_summary["dataset_version"] == "benchmark_v1"
    assert baseline_summary["full_dataset_run"] is False
    assert baseline_summary["official_metrics"]["cases_total"] == 2
    assert baseline_summary["partial_or_blocked_metrics"]["context_precision"] == "blocked_without_reference_answer"
    assert baseline_summary["official_metric_status"]["answer_relevance"] == "baseline_primary_with_low_interpretability_on_current_stack"


@dataclass
class _AlwaysSkipEvaluator:
    stack_resolution: RagEvaluationStackResolution = RagEvaluationStackResolution(
        metric_library=RagEvaluationLibraryName.RAGAS,
        metric_library_version="0.2.15",
        tracking_target="mlflow",
        resolution_order=(RagEvaluationLibraryName.RAGAS,),
    )
    evaluator_mode: str = "test_skip_evaluator"

    async def evaluate_case(
        self,
        case_input: RagEvaluationCaseInput,
    ) -> tuple[RagEvaluationCaseResult, dict[str, str]]:
        """Retorna um caso inteiramente pulado para validar a classificacao da run."""

        return (
            build_rag_evaluation_case_result(case_input),
            {
                "faithfulness": "evaluation_error:forced_skip",
                "answer_relevance": "evaluation_error:forced_skip",
            },
        )


def test_phase4_executor_marks_case_as_skipped_when_no_mandatory_metric_is_available(tmp_path) -> None:
    executor = _build_executor(tmp_path, metric_evaluator=_AlwaysSkipEvaluator())

    execution = asyncio.run(
        executor.execute_dataset(
            manifest_path=_manifest_path(),
            case_ids=("vs-risco-policy-001",),
        )
    )

    assert len(execution.case_executions) == 1
    case_execution = execution.case_executions[0]
    assert case_execution.status == RagEvaluationCaseStatus.SKIPPED
    assert execution.evaluated_cases_count() == 0
    assert execution.partial_cases_count() == 0
    assert execution.skipped_cases_count() == 1
    assert execution.summary.faithfulness_mean is None
    assert execution.summary.answer_relevance_mean is None
    assert execution.metric_skip_counts()["faithfulness"] == 1
    assert execution.metric_skip_counts()["answer_relevance"] == 1
