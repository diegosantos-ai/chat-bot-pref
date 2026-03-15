"""Testes da execucao offline da Fase 4 com benchmark, avaliacao e tracking."""

import asyncio
from dataclasses import dataclass
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
    assert "answer_relevance_mean" in run.data.metrics
    assert "faithfulness_mean" in run.data.metrics

    artifact_names = {item.path for item in client.list_artifacts(logged_run.run_id)}
    assert logged_run.report_path.name in artifact_names
    assert logged_run.report_path.is_file()


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
