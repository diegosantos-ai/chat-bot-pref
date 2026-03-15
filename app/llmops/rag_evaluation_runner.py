"""Executor offline da Fase 4 para benchmark, avaliacao RAG e tracking experimental."""

from __future__ import annotations

import asyncio
from copy import deepcopy
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import hashlib
import json
import math
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Final, Protocol, Sequence
from uuid import uuid4

from langchain_core.outputs import Generation, LLMResult
from langchain_core.prompt_values import PromptValue
from ragas.dataset_schema import SingleTurnSample
from ragas.embeddings import BaseRagasEmbeddings
from ragas.llms import BaseRagasLLM
from ragas.metrics import answer_relevancy, faithfulness
from ragas.run_config import RunConfig

from app.contracts.dto import (
    PolicyDecision,
    RagQueryParamsUsed,
    RagQueryResponse,
    RagRetrievedChunk,
)
from app.llmops.benchmark_dataset import (
    BenchmarkCase,
    LoadedBenchmarkDataset,
    load_benchmark_dataset,
)
from app.llmops.rag_evaluation import (
    RagEvaluationCaseInput,
    RagEvaluationCaseResult,
    RagEvaluationLibraryName,
    RagEvaluationMetricName,
    RagEvaluationRunSummary,
    RagEvaluationStackResolution,
    build_rag_evaluation_case_result,
    build_rag_evaluation_run_summary,
    resolve_rag_evaluation_stack,
)
from app.llmops.tracking_integration import Phase2TrackingRun, build_phase2_tracking_run
from app.services.llm_service import LLMComposeService, LLMGenerationResponse
from app.services.prompt_service import PromptService
from app.services.tenant_profile_service import TenantProfileService
from app.policy_guard.service import PolicyGuardService, PostPolicyInput
from app.settings import settings
from app.storage.chroma_repository import HashEmbeddingFunction, TenantChromaRepository
from app.storage.document_repository import FileDocumentRepository

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
DEFAULT_PHASE4_TRACKING_DIR: Final[Path] = REPO_ROOT / "artifacts" / "llmops" / "fase4_rag_evaluation"
DEFAULT_PHASE4_EXPERIMENT_NAME: Final[str] = "chat-pref-fase4-rag-evaluation"
TOKEN_PATTERN: Final[str] = r"[a-z0-9]+"
COMMON_STOPWORDS: Final[frozenset[str]] = frozenset(
    {
        "a",
        "ao",
        "aos",
        "as",
        "com",
        "como",
        "da",
        "das",
        "de",
        "do",
        "dos",
        "e",
        "em",
        "essa",
        "esse",
        "esta",
        "este",
        "institucionais",
        "informacoes",
        "mais",
        "na",
        "nas",
        "no",
        "nos",
        "o",
        "os",
        "ou",
        "para",
        "pela",
        "pelas",
        "pelo",
        "pelos",
        "por",
        "prefeitura",
        "procure",
        "que",
        "se",
        "sua",
        "suo",
        "um",
        "uma",
    }
)
NONCOMMITTAL_HINTS: Final[tuple[str, ...]] = (
    "nao encontrei contexto suficiente",
    "nao possuo informacoes suficientes",
    "no momento",
    "nao posso fornecer",
    "nao posso orientar",
    "procure os canais oficiais",
)
BOILERPLATE_RESPONSE_SNIPPETS: Final[tuple[str, ...]] = (
    "de acordo com as informacoes institucionais",
    "se precisar de atendimento formal",
)


class RagEvaluationCaseStatus(StrEnum):
    """Classifica o nivel de completude de um caso avaliado."""

    EVALUATED = "evaluated"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class RagMetricEvaluator(Protocol):
    """Define o contrato minimo do avaliador por caso usado no executor offline."""

    stack_resolution: RagEvaluationStackResolution
    evaluator_mode: str

    async def evaluate_case(
        self,
        case_input: RagEvaluationCaseInput,
    ) -> tuple[RagEvaluationCaseResult, dict[str, str]]:
        """Avalia um caso e retorna as metricas computadas e os skips observados."""


@dataclass(frozen=True, slots=True)
class MlflowTrackingConfig:
    """Configura o backend local de tracking experimental da Fase 4."""

    base_dir: Path = DEFAULT_PHASE4_TRACKING_DIR
    experiment_name: str = DEFAULT_PHASE4_EXPERIMENT_NAME

    @property
    def database_path(self) -> Path:
        """Retorna o caminho do banco SQLite usado pelo MLflow local."""

        return self.base_dir / "mlflow.db"

    @property
    def artifacts_dir(self) -> Path:
        """Retorna o diretorio raiz dos artifacts do experimento."""

        return self.base_dir / "mlartifacts"

    @property
    def reports_dir(self) -> Path:
        """Retorna o diretorio local onde os relatarios JSON da run sao escritos."""

        return self.base_dir / "run_reports"

    def tracking_uri(self) -> str:
        """Retorna a URI SQLite do tracking experimental local."""

        return f"sqlite:///{self.database_path.resolve().as_posix()}"

    def ensure_directories(self) -> None:
        """Garante a estrutura local minima do tracking offline."""

        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True, slots=True)
class LoggedMlflowRun:
    """Representa a run experimental efetivamente registrada no MLflow."""

    experiment_id: str
    run_id: str
    tracking_uri: str
    report_path: Path
    comparison_snapshot_path: Path
    comparison_csv_path: Path
    case_ranking_path: Path
    baseline_summary_path: Path


@dataclass(frozen=True, slots=True)
class RagEvaluationCaseExecution:
    """Registra o resultado tecnico de um caso executado no pipeline offline."""

    case_input: RagEvaluationCaseInput
    case_result: RagEvaluationCaseResult
    status: RagEvaluationCaseStatus
    skipped_metrics: dict[str, str]
    rag_status: str
    response_mode: str
    prompt_version: str
    policy_version: str
    model_provider: str
    model_name: str
    request_id: str
    latency_ms: float
    pre_decision: PolicyDecision
    post_decision: PolicyDecision
    retrieved_chunk_titles: tuple[str, ...]
    best_score: float

    def mandatory_metrics_complete(self) -> bool:
        """Indica se as duas metricas obrigatorias foram computadas no caso."""

        return (
            self.case_result.faithfulness is not None
            and self.case_result.answer_relevance is not None
        )

    def has_methodology_limitation(self) -> bool:
        """Indica se o caso ficou limitado por dados ou contrato do benchmark."""

        return any(reason.startswith("missing_fields:") for reason in self.skipped_metrics.values())

    def as_artifact_payload(self) -> dict[str, object]:
        """Retorna o payload serializavel minimo do caso executado."""

        return {
            "case_id": self.case_input.case_id,
            "tenant_id": self.case_input.tenant_id,
            "scenario_type": self.case_input.benchmark_case.scenario_type.value,
            "priority_tier": self.case_input.benchmark_case.priority_tier.value,
            "coverage_type": self.case_input.benchmark_case.coverage_type.value,
            "status": self.status.value,
            "request_id": self.request_id,
            "question": self.case_input.user_input,
            "response": self.case_input.response,
            "retrieved_contexts": list(self.case_input.retrieved_contexts),
            "retrieved_chunk_titles": list(self.retrieved_chunk_titles),
            "rag_status": self.rag_status,
            "response_mode": self.response_mode,
            "prompt_version": self.prompt_version,
            "policy_version": self.policy_version,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "latency_ms": self.latency_ms,
            "best_score": self.best_score,
            "pre_decision": self.pre_decision.model_dump(mode="json"),
            "post_decision": self.post_decision.model_dump(mode="json"),
            "metrics": self.case_result.as_artifact_payload(),
            "skipped_metrics": dict(self.skipped_metrics),
        }


@dataclass(frozen=True, slots=True)
class RagEvaluationRunExecution:
    """Consolida a execucao completa do benchmark offline de uma run experimental."""

    dataset: LoadedBenchmarkDataset
    case_executions: tuple[RagEvaluationCaseExecution, ...]
    summary: RagEvaluationRunSummary
    tracking_run: Phase2TrackingRun
    stack_resolution: RagEvaluationStackResolution
    evaluator_mode: str
    experiment_name: str
    dataset_manifest_path: Path
    vectorstore_fingerprint: str
    vectorstore_collection: str
    selected_case_ids: tuple[str, ...]
    observed_prompt_versions: tuple[str, ...]
    total_latency_ms: float

    @property
    def tenant_id(self) -> str:
        """Retorna o tenant avaliado na run."""

        return self.dataset.manifest.tenant_id

    @property
    def run_request_id(self) -> str:
        """Retorna o request_id tecnico usado para correlar a run experimental."""

        return self.tracking_run.run_contract.request_id

    def evaluated_cases_count(self) -> int:
        """Conta casos com ambas as metricas obrigatorias computadas."""

        return sum(1 for case in self.case_executions if case.status == RagEvaluationCaseStatus.EVALUATED)

    def partial_cases_count(self) -> int:
        """Conta casos com avaliacao parcial, mas nao vazia."""

        return sum(1 for case in self.case_executions if case.status == RagEvaluationCaseStatus.PARTIAL)

    def skipped_cases_count(self) -> int:
        """Conta casos inteiramente pulados por falta de metricas computadas."""

        return sum(1 for case in self.case_executions if case.status == RagEvaluationCaseStatus.SKIPPED)

    def cases_with_methodology_limitations_count(self) -> int:
        """Conta casos que sofreram limitacao metodologica do benchmark atual."""

        return sum(1 for case in self.case_executions if case.has_methodology_limitation())

    def metric_skip_counts(self) -> dict[str, int]:
        """Agrega a quantidade de skips por metrica ao longo da run."""

        counts: dict[str, int] = {}
        for case in self.case_executions:
            for metric_name in case.skipped_metrics:
                counts[metric_name] = counts.get(metric_name, 0) + 1
        return counts

    def as_tracking_tags(self) -> dict[str, str]:
        """Retorna as tags minimas da run experimental para o MLflow."""

        return {
            "phase": "F4",
            "run_kind": "rag_formal_evaluation",
            "evaluator_library": self.stack_resolution.metric_library.value,
            "evaluator_mode": self.evaluator_mode,
            "vectorstore_collection": self.vectorstore_collection,
            "vectorstore_fingerprint": self.vectorstore_fingerprint,
            "dataset_manifest": _relative_to_repo(self.dataset_manifest_path),
            "prompt_version_scope": "mixed" if len(self.observed_prompt_versions) > 1 else "single",
            **self.tracking_run.as_tags(),
        }

    def as_tracking_params(self) -> dict[str, str]:
        """Retorna os parametros comparaveis da run experimental."""

        params = {
            **self.tracking_run.as_params(),
            "experiment_name": self.experiment_name,
            "dataset_manifest": _relative_to_repo(self.dataset_manifest_path),
            "selected_case_ids": ",".join(self.selected_case_ids),
            "selected_cases_count": str(len(self.selected_case_ids)),
            "observed_prompt_versions": ",".join(self.observed_prompt_versions),
            "vectorstore_collection": self.vectorstore_collection,
            "vectorstore_fingerprint": self.vectorstore_fingerprint,
            "vectorstore_version": self.vectorstore_fingerprint,
            "evaluator_library": self.stack_resolution.metric_library.value,
            "evaluator_library_version": self.stack_resolution.metric_library_version,
            "evaluator_mode": self.evaluator_mode,
        }
        return params

    def as_tracking_metrics(self) -> dict[str, float]:
        """Retorna as metricas numericas minimas da run para o MLflow."""

        metrics = {
            **self.summary.as_metrics(),
            **self.tracking_run.as_metrics(),
            "cases_evaluated": float(self.evaluated_cases_count()),
            "cases_partial": float(self.partial_cases_count()),
            "cases_skipped": float(self.skipped_cases_count()),
            "cases_with_methodology_limitations": float(
                self.cases_with_methodology_limitations_count()
            ),
        }
        for metric_name, count in self.summary.metric_case_counts.items():
            metrics[f"{metric_name}_cases"] = float(count)
        for metric_name, count in self.metric_skip_counts().items():
            metrics[f"{metric_name}_skipped"] = float(count)
        return metrics

    def as_artifact_payload(self) -> dict[str, object]:
        """Retorna o relatorio JSON minimo da run experimental."""

        return {
            "phase": "F4",
            "experiment_name": self.experiment_name,
            "tenant_id": self.tenant_id,
            "dataset_version": self.dataset.manifest.dataset_version,
            "dataset_manifest": _relative_to_repo(self.dataset_manifest_path),
            "vectorstore_collection": self.vectorstore_collection,
            "vectorstore_fingerprint": self.vectorstore_fingerprint,
            "evaluator_library": self.stack_resolution.metric_library.value,
            "evaluator_library_version": self.stack_resolution.metric_library_version,
            "evaluator_mode": self.evaluator_mode,
            "tracking": {
                "request_id": self.run_request_id,
                "tracking_target": self.stack_resolution.tracking_target,
                "tags": self.as_tracking_tags(),
                "params": self.as_tracking_params(),
                "metrics": self.as_tracking_metrics(),
            },
            "summary": self.summary.as_artifact_payload(),
            "cases": [case.as_artifact_payload() for case in self.case_executions],
        }

    def build_comparison_row(self, *, run_id: str) -> "RagEvaluationComparisonRow":
        """Converte a run atual em uma linha plana comparavel com runs anteriores."""

        run_contract = self.tracking_run.run_contract
        tracking_metadata = self.tracking_run.tracking_metadata
        methodology_notes = _build_methodology_notes(
            evaluator_mode=self.evaluator_mode,
            cases_with_methodology_limitations=self.cases_with_methodology_limitations_count(),
            skipped_metric_entries=sum(self.metric_skip_counts().values()),
        )
        return RagEvaluationComparisonRow(
            run_id=run_id,
            request_id=self.run_request_id,
            experiment_name=self.experiment_name,
            tenant_id=self.tenant_id,
            dataset_version=self.dataset.manifest.dataset_version,
            prompt_version=run_contract.prompt_version,
            prompt_version_id=tracking_metadata.prompt_version_id,
            policy_version=run_contract.policy_version,
            policy_version_id=tracking_metadata.policy_version_id,
            retriever_version=run_contract.retriever_version,
            retriever_version_id=tracking_metadata.retriever_version_id,
            embedding_version=run_contract.embedding_version,
            chunking_version=tracking_metadata.chunking_version,
            chunking_version_id=tracking_metadata.chunking_version_id,
            vectorstore_collection=self.vectorstore_collection,
            vectorstore_fingerprint=self.vectorstore_fingerprint,
            evaluator_library=self.stack_resolution.metric_library.value,
            evaluator_library_version=self.stack_resolution.metric_library_version,
            evaluator_mode=self.evaluator_mode,
            model_provider=run_contract.model_provider,
            model_name=run_contract.model_name,
            selected_cases_count=len(self.selected_case_ids),
            observed_prompt_versions=",".join(self.observed_prompt_versions),
            total_latency_ms=self.total_latency_ms,
            cases_total=self.summary.total_cases,
            cases_evaluated=self.evaluated_cases_count(),
            cases_partial=self.partial_cases_count(),
            cases_skipped=self.skipped_cases_count(),
            cases_with_methodology_limitations=self.cases_with_methodology_limitations_count(),
            faithfulness_mean=self.summary.faithfulness_mean,
            answer_relevance_mean=self.summary.answer_relevance_mean,
            context_precision_mean=self.summary.context_precision_mean,
            context_recall_mean=self.summary.context_recall_mean,
            expected_context_coverage_mean=self.summary.expected_context_coverage_mean,
            retrieval_empty_rate=self.summary.retrieval_empty_rate,
            faithfulness_cases=self.summary.metric_case_counts.get("faithfulness", 0),
            answer_relevance_cases=self.summary.metric_case_counts.get("answer_relevance", 0),
            context_precision_cases=self.summary.metric_case_counts.get("context_precision", 0),
            context_recall_cases=self.summary.metric_case_counts.get("context_recall", 0),
            expected_context_coverage_cases=self.summary.metric_case_counts.get(
                "expected_context_coverage", 0
            ),
            retrieval_empty_cases=self.summary.metric_case_counts.get("retrieval_empty", 0),
            heuristic_evaluator="heuristic" in self.evaluator_mode,
            methodology_notes=methodology_notes,
            logged_at=datetime.now(timezone.utc).isoformat(),
        )

    def build_case_ranking_artifact(
        self,
        *,
        run_id: str,
        limit: int = 5,
    ) -> "RagEvaluationCaseRankingArtifact":
        """Monta o artifact de melhores, piores e nao avaliados da run atual."""

        return RagEvaluationCaseRankingArtifact.from_execution(
            execution=self,
            run_id=run_id,
            limit=limit,
        )

    def build_baseline_summary_artifact(
        self,
        *,
        run_id: str,
    ) -> "RagEvaluationBaselineSummaryArtifact":
        """Monta o sumario pequeno de baseline da run atual para fechamento da fase."""

        return RagEvaluationBaselineSummaryArtifact.from_execution(
            execution=self,
            run_id=run_id,
        )


@dataclass(frozen=True, slots=True)
class RagEvaluationComparisonRow:
    """Representa uma linha plana de comparacao entre runs do mesmo experimento."""

    run_id: str
    request_id: str
    experiment_name: str
    tenant_id: str
    dataset_version: str
    prompt_version: str
    prompt_version_id: str
    policy_version: str
    policy_version_id: str
    retriever_version: str
    retriever_version_id: str
    embedding_version: str
    chunking_version: str
    chunking_version_id: str
    vectorstore_collection: str
    vectorstore_fingerprint: str
    evaluator_library: str
    evaluator_library_version: str
    evaluator_mode: str
    model_provider: str
    model_name: str
    selected_cases_count: int
    observed_prompt_versions: str
    total_latency_ms: float
    cases_total: int
    cases_evaluated: int
    cases_partial: int
    cases_skipped: int
    cases_with_methodology_limitations: int
    faithfulness_mean: float | None
    answer_relevance_mean: float | None
    context_precision_mean: float | None
    context_recall_mean: float | None
    expected_context_coverage_mean: float | None
    retrieval_empty_rate: float | None
    faithfulness_cases: int
    answer_relevance_cases: int
    context_precision_cases: int
    context_recall_cases: int
    expected_context_coverage_cases: int
    retrieval_empty_cases: int
    heuristic_evaluator: bool
    methodology_notes: tuple[str, ...]
    logged_at: str

    def as_artifact_payload(self) -> dict[str, object]:
        """Retorna a linha de comparacao em formato JSON serializavel."""

        return {
            "run_id": self.run_id,
            "request_id": self.request_id,
            "experiment_name": self.experiment_name,
            "tenant_id": self.tenant_id,
            "dataset_version": self.dataset_version,
            "prompt_version": self.prompt_version,
            "prompt_version_id": self.prompt_version_id,
            "policy_version": self.policy_version,
            "policy_version_id": self.policy_version_id,
            "retriever_version": self.retriever_version,
            "retriever_version_id": self.retriever_version_id,
            "embedding_version": self.embedding_version,
            "chunking_version": self.chunking_version,
            "chunking_version_id": self.chunking_version_id,
            "vectorstore_collection": self.vectorstore_collection,
            "vectorstore_fingerprint": self.vectorstore_fingerprint,
            "evaluator_library": self.evaluator_library,
            "evaluator_library_version": self.evaluator_library_version,
            "evaluator_mode": self.evaluator_mode,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "selected_cases_count": self.selected_cases_count,
            "observed_prompt_versions": self.observed_prompt_versions,
            "total_latency_ms": self.total_latency_ms,
            "cases_total": self.cases_total,
            "cases_evaluated": self.cases_evaluated,
            "cases_partial": self.cases_partial,
            "cases_skipped": self.cases_skipped,
            "cases_with_methodology_limitations": self.cases_with_methodology_limitations,
            "faithfulness_mean": self.faithfulness_mean,
            "answer_relevance_mean": self.answer_relevance_mean,
            "context_precision_mean": self.context_precision_mean,
            "context_recall_mean": self.context_recall_mean,
            "expected_context_coverage_mean": self.expected_context_coverage_mean,
            "retrieval_empty_rate": self.retrieval_empty_rate,
            "faithfulness_cases": self.faithfulness_cases,
            "answer_relevance_cases": self.answer_relevance_cases,
            "context_precision_cases": self.context_precision_cases,
            "context_recall_cases": self.context_recall_cases,
            "expected_context_coverage_cases": self.expected_context_coverage_cases,
            "retrieval_empty_cases": self.retrieval_empty_cases,
            "heuristic_evaluator": self.heuristic_evaluator,
            "methodology_notes": list(self.methodology_notes),
            "logged_at": self.logged_at,
        }

    def as_csv_row(self) -> dict[str, str]:
        """Retorna a linha de comparacao pronta para exportacao CSV."""

        payload = self.as_artifact_payload()
        csv_row: dict[str, str] = {}
        for key, value in payload.items():
            if isinstance(value, list):
                csv_row[key] = "|".join(str(item) for item in value)
                continue
            if value is None:
                csv_row[key] = ""
                continue
            csv_row[key] = str(value)
        return csv_row

    @classmethod
    def from_mlflow_run(
        cls,
        *,
        run: Any,
        experiment_name: str,
    ) -> "RagEvaluationComparisonRow":
        """Reconstrui uma linha comparativa a partir de uma run ja persistida no MLflow."""

        data = run.data
        tags = data.tags
        params = data.params
        metrics = data.metrics
        skipped_metric_entries = sum(
            _coerce_int(value)
            for key, value in metrics.items()
            if key.endswith("_skipped")
        )
        methodology_notes = _build_methodology_notes(
            evaluator_mode=tags.get("evaluator_mode", params.get("evaluator_mode", "")),
            cases_with_methodology_limitations=_coerce_int(
                metrics.get("cases_with_methodology_limitations", 0.0)
            ),
            skipped_metric_entries=skipped_metric_entries,
        )
        return cls(
            run_id=run.info.run_id,
            request_id=tags.get("request_id", ""),
            experiment_name=experiment_name,
            tenant_id=tags.get("tenant_id", ""),
            dataset_version=params.get("dataset_version", ""),
            prompt_version=params.get("prompt_version", ""),
            prompt_version_id=tags.get("prompt_version_id", ""),
            policy_version=params.get("policy_version", ""),
            policy_version_id=tags.get("policy_version_id", ""),
            retriever_version=params.get("retriever_version", ""),
            retriever_version_id=tags.get("retriever_version_id", ""),
            embedding_version=params.get("embedding_version", ""),
            chunking_version=params.get("chunking_version", ""),
            chunking_version_id=tags.get("chunking_version_id", ""),
            vectorstore_collection=params.get(
                "vectorstore_collection",
                tags.get("vectorstore_collection", ""),
            ),
            vectorstore_fingerprint=params.get(
                "vectorstore_fingerprint",
                tags.get("vectorstore_fingerprint", ""),
            ),
            evaluator_library=params.get(
                "evaluator_library",
                tags.get("evaluator_library", ""),
            ),
            evaluator_library_version=params.get("evaluator_library_version", ""),
            evaluator_mode=params.get("evaluator_mode", tags.get("evaluator_mode", "")),
            model_provider=params.get("model_provider", ""),
            model_name=params.get("model_name", ""),
            selected_cases_count=_coerce_int(params.get("selected_cases_count", 0)),
            observed_prompt_versions=params.get("observed_prompt_versions", ""),
            total_latency_ms=_coerce_float(metrics.get("latency_ms", 0.0)) or 0.0,
            cases_total=_coerce_int(metrics.get("cases_total", 0.0)),
            cases_evaluated=_coerce_int(metrics.get("cases_evaluated", 0.0)),
            cases_partial=_coerce_int(metrics.get("cases_partial", 0.0)),
            cases_skipped=_coerce_int(metrics.get("cases_skipped", 0.0)),
            cases_with_methodology_limitations=_coerce_int(
                metrics.get("cases_with_methodology_limitations", 0.0)
            ),
            faithfulness_mean=_coerce_float(metrics.get("faithfulness_mean")),
            answer_relevance_mean=_coerce_float(metrics.get("answer_relevance_mean")),
            context_precision_mean=_coerce_float(metrics.get("context_precision_mean")),
            context_recall_mean=_coerce_float(metrics.get("context_recall_mean")),
            expected_context_coverage_mean=_coerce_float(
                metrics.get("expected_context_coverage_mean")
            ),
            retrieval_empty_rate=_coerce_float(metrics.get("retrieval_empty_rate")),
            faithfulness_cases=_coerce_int(metrics.get("faithfulness_cases", 0.0)),
            answer_relevance_cases=_coerce_int(metrics.get("answer_relevance_cases", 0.0)),
            context_precision_cases=_coerce_int(metrics.get("context_precision_cases", 0.0)),
            context_recall_cases=_coerce_int(metrics.get("context_recall_cases", 0.0)),
            expected_context_coverage_cases=_coerce_int(
                metrics.get("expected_context_coverage_cases", 0.0)
            ),
            retrieval_empty_cases=_coerce_int(metrics.get("retrieval_empty_cases", 0.0)),
            heuristic_evaluator="heuristic" in tags.get(
                "evaluator_mode",
                params.get("evaluator_mode", ""),
            ),
            methodology_notes=methodology_notes,
            logged_at=_format_mlflow_timestamp(run.info.start_time),
        )


@dataclass(frozen=True, slots=True)
class RagEvaluationComparisonSnapshot:
    """Consolida um recorte comparavel de runs do mesmo experimento e tenant."""

    experiment_name: str
    tenant_id: str
    runs: tuple[RagEvaluationComparisonRow, ...]
    methodology_notes: tuple[str, ...]

    @classmethod
    def from_rows(
        cls,
        *,
        experiment_name: str,
        tenant_id: str,
        rows: Sequence[RagEvaluationComparisonRow],
    ) -> "RagEvaluationComparisonSnapshot":
        """Monta o snapshot comparativo ordenado a partir das linhas disponiveis."""

        sorted_rows = tuple(
            sorted(rows, key=lambda row: (row.logged_at, row.run_id))
        )
        methodology_notes = _build_comparison_snapshot_notes(sorted_rows)
        return cls(
            experiment_name=experiment_name,
            tenant_id=tenant_id,
            runs=sorted_rows,
            methodology_notes=methodology_notes,
        )

    def as_artifact_payload(self) -> dict[str, object]:
        """Retorna o snapshot comparativo em formato JSON serializavel."""

        return {
            "phase": "F4",
            "artifact_type": "comparison_snapshot",
            "experiment_name": self.experiment_name,
            "tenant_id": self.tenant_id,
            "runs_compared": len(self.runs),
            "dataset_versions": sorted({row.dataset_version for row in self.runs if row.dataset_version}),
            "evaluator_modes": sorted({row.evaluator_mode for row in self.runs if row.evaluator_mode}),
            "methodology_notes": list(self.methodology_notes),
            "runs": [row.as_artifact_payload() for row in self.runs],
        }

    def write_csv(self, path: Path) -> None:
        """Escreve as linhas comparativas em CSV para leitura manual e automacao."""

        csv_rows = [row.as_csv_row() for row in self.runs]
        fieldnames = list(csv_rows[0].keys()) if csv_rows else []
        with path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for row in csv_rows:
                writer.writerow(row)


@dataclass(frozen=True, slots=True)
class RagEvaluationCaseRankingEntry:
    """Representa uma entrada de ranking dos casos executados na run."""

    case_id: str
    scenario_type: str
    status: str
    mandatory_score_mean: float | None
    faithfulness: float | None
    answer_relevance: float | None
    expected_context_coverage: float | None
    response_mode: str
    rag_status: str
    prompt_version: str
    policy_version: str
    best_score: float
    methodology_limitation: bool
    skipped_metrics: dict[str, str]

    @classmethod
    def from_case_execution(
        cls,
        case_execution: RagEvaluationCaseExecution,
    ) -> "RagEvaluationCaseRankingEntry":
        """Converte a execucao de um caso em uma entrada compacta de ranking."""

        mandatory_values = [
            value
            for value in (
                case_execution.case_result.faithfulness,
                case_execution.case_result.answer_relevance,
            )
            if value is not None
        ]
        mandatory_score_mean = (
            round(sum(mandatory_values) / len(mandatory_values), 4)
            if mandatory_values
            else None
        )
        return cls(
            case_id=case_execution.case_input.case_id,
            scenario_type=case_execution.case_input.benchmark_case.scenario_type.value,
            status=case_execution.status.value,
            mandatory_score_mean=mandatory_score_mean,
            faithfulness=case_execution.case_result.faithfulness,
            answer_relevance=case_execution.case_result.answer_relevance,
            expected_context_coverage=case_execution.case_result.expected_context_coverage,
            response_mode=case_execution.response_mode,
            rag_status=case_execution.rag_status,
            prompt_version=case_execution.prompt_version,
            policy_version=case_execution.policy_version,
            best_score=case_execution.best_score,
            methodology_limitation=case_execution.has_methodology_limitation(),
            skipped_metrics=dict(case_execution.skipped_metrics),
        )

    def as_artifact_payload(self) -> dict[str, object]:
        """Retorna a entrada de ranking em formato JSON serializavel."""

        return {
            "case_id": self.case_id,
            "scenario_type": self.scenario_type,
            "status": self.status,
            "mandatory_score_mean": self.mandatory_score_mean,
            "faithfulness": self.faithfulness,
            "answer_relevance": self.answer_relevance,
            "expected_context_coverage": self.expected_context_coverage,
            "response_mode": self.response_mode,
            "rag_status": self.rag_status,
            "prompt_version": self.prompt_version,
            "policy_version": self.policy_version,
            "best_score": self.best_score,
            "methodology_limitation": self.methodology_limitation,
            "skipped_metrics": dict(self.skipped_metrics),
        }


@dataclass(frozen=True, slots=True)
class RagEvaluationCaseRankingArtifact:
    """Consolida melhores, piores e nao avaliados da run atual sem inferencia extra."""

    experiment_name: str
    run_id: str
    request_id: str
    tenant_id: str
    dataset_version: str
    evaluator_library: str
    evaluator_mode: str
    methodology_notes: tuple[str, ...]
    status_counts: dict[str, int]
    best_evaluated_cases: tuple[RagEvaluationCaseRankingEntry, ...]
    worst_evaluated_cases: tuple[RagEvaluationCaseRankingEntry, ...]
    non_evaluated_cases: tuple[RagEvaluationCaseRankingEntry, ...]

    @classmethod
    def from_execution(
        cls,
        *,
        execution: RagEvaluationRunExecution,
        run_id: str,
        limit: int = 5,
    ) -> "RagEvaluationCaseRankingArtifact":
        """Gera o ranking dos casos da run atual sem misturar avaliados e nao avaliados."""

        entries = tuple(
            RagEvaluationCaseRankingEntry.from_case_execution(case_execution)
            for case_execution in execution.case_executions
        )
        evaluated = sorted(
            (entry for entry in entries if entry.status == RagEvaluationCaseStatus.EVALUATED.value),
            key=lambda entry: (
                -(entry.mandatory_score_mean if entry.mandatory_score_mean is not None else -1.0),
                entry.case_id,
            ),
        )
        non_evaluated = tuple(
            sorted(
                (entry for entry in entries if entry.status != RagEvaluationCaseStatus.EVALUATED.value),
                key=lambda entry: (entry.status, entry.case_id),
            )
        )
        worst_evaluated = tuple(
            sorted(
                evaluated,
                key=lambda entry: (
                    entry.mandatory_score_mean if entry.mandatory_score_mean is not None else 2.0,
                    entry.case_id,
                ),
            )[:limit]
        )
        best_evaluated = tuple(evaluated[:limit])
        methodology_notes = _build_methodology_notes(
            evaluator_mode=execution.evaluator_mode,
            cases_with_methodology_limitations=execution.cases_with_methodology_limitations_count(),
            skipped_metric_entries=sum(execution.metric_skip_counts().values()),
        )
        return cls(
            experiment_name=execution.experiment_name,
            run_id=run_id,
            request_id=execution.run_request_id,
            tenant_id=execution.tenant_id,
            dataset_version=execution.dataset.manifest.dataset_version,
            evaluator_library=execution.stack_resolution.metric_library.value,
            evaluator_mode=execution.evaluator_mode,
            methodology_notes=methodology_notes,
            status_counts={
                RagEvaluationCaseStatus.EVALUATED.value: execution.evaluated_cases_count(),
                RagEvaluationCaseStatus.PARTIAL.value: execution.partial_cases_count(),
                RagEvaluationCaseStatus.SKIPPED.value: execution.skipped_cases_count(),
            },
            best_evaluated_cases=best_evaluated,
            worst_evaluated_cases=worst_evaluated,
            non_evaluated_cases=non_evaluated,
        )

    def as_artifact_payload(self) -> dict[str, object]:
        """Retorna o ranking de casos em formato JSON serializavel."""

        return {
            "phase": "F4",
            "artifact_type": "case_ranking",
            "experiment_name": self.experiment_name,
            "run_id": self.run_id,
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "dataset_version": self.dataset_version,
            "evaluator_library": self.evaluator_library,
            "evaluator_mode": self.evaluator_mode,
            "methodology_notes": list(self.methodology_notes),
            "status_counts": dict(self.status_counts),
            "best_evaluated_cases": [
                entry.as_artifact_payload() for entry in self.best_evaluated_cases
            ],
            "worst_evaluated_cases": [
                entry.as_artifact_payload() for entry in self.worst_evaluated_cases
            ],
            "non_evaluated_cases": [
                entry.as_artifact_payload() for entry in self.non_evaluated_cases
            ],
        }


@dataclass(frozen=True, slots=True)
class RagEvaluationBaselineSummaryArtifact:
    """Resume a baseline inicial observada na run sem extrapolar a evidência disponível."""

    run_id: str
    request_id: str
    experiment_name: str
    tenant_id: str
    dataset_version: str
    selected_cases_count: int
    dataset_cases_count: int
    full_dataset_run: bool
    evaluator_library: str
    evaluator_library_version: str
    evaluator_mode: str
    official_metrics: dict[str, float | int | None]
    official_metric_status: dict[str, str]
    partial_or_blocked_metrics: dict[str, str]
    methodology_notes: tuple[str, ...]

    @classmethod
    def from_execution(
        cls,
        *,
        execution: RagEvaluationRunExecution,
        run_id: str,
    ) -> "RagEvaluationBaselineSummaryArtifact":
        """Consolida o sumario da baseline a partir da execucao da run atual."""

        answer_relevance_values = [
            case.case_result.answer_relevance
            for case in execution.case_executions
            if case.case_result.answer_relevance is not None
        ]
        answer_relevance_flat_zero = (
            bool(answer_relevance_values)
            and all(value == 0.0 for value in answer_relevance_values)
        )
        full_dataset_run = len(execution.selected_case_ids) == len(execution.dataset.cases)
        methodology_notes = _build_methodology_notes(
            evaluator_mode=execution.evaluator_mode,
            cases_with_methodology_limitations=execution.cases_with_methodology_limitations_count(),
            skipped_metric_entries=sum(execution.metric_skip_counts().values()),
        )
        return cls(
            run_id=run_id,
            request_id=execution.run_request_id,
            experiment_name=execution.experiment_name,
            tenant_id=execution.tenant_id,
            dataset_version=execution.dataset.manifest.dataset_version,
            selected_cases_count=len(execution.selected_case_ids),
            dataset_cases_count=len(execution.dataset.cases),
            full_dataset_run=full_dataset_run,
            evaluator_library=execution.stack_resolution.metric_library.value,
            evaluator_library_version=execution.stack_resolution.metric_library_version,
            evaluator_mode=execution.evaluator_mode,
            official_metrics={
                "faithfulness_mean": execution.summary.faithfulness_mean,
                "answer_relevance_mean": execution.summary.answer_relevance_mean,
                "expected_context_coverage_mean": execution.summary.expected_context_coverage_mean,
                "retrieval_empty_rate": execution.summary.retrieval_empty_rate,
                "cases_total": execution.summary.total_cases,
                "cases_evaluated": execution.evaluated_cases_count(),
                "cases_partial": execution.partial_cases_count(),
                "cases_skipped": execution.skipped_cases_count(),
            },
            official_metric_status={
                "faithfulness": "baseline_primary",
                "answer_relevance": (
                    "baseline_primary_with_low_interpretability_on_current_stack"
                    if answer_relevance_flat_zero
                    else "baseline_primary"
                ),
                "expected_context_coverage": "baseline_complementary_heuristic",
                "retrieval_empty_rate": "baseline_complementary_structural",
            },
            partial_or_blocked_metrics={
                "context_precision": "blocked_without_reference_answer",
                "context_recall": "blocked_without_reference_answer",
                "faithfulness": (
                    "partial_when_policy_pre_blocks_retrieval_or_context_is_empty"
                    if execution.summary.metric_case_counts.get("faithfulness", 0)
                    < execution.summary.total_cases
                    else "fully_computed"
                ),
            },
            methodology_notes=methodology_notes,
        )

    def as_artifact_payload(self) -> dict[str, object]:
        """Retorna o sumario da baseline em formato JSON serializavel."""

        return {
            "phase": "F4",
            "artifact_type": "baseline_summary",
            "run_id": self.run_id,
            "request_id": self.request_id,
            "experiment_name": self.experiment_name,
            "tenant_id": self.tenant_id,
            "dataset_version": self.dataset_version,
            "selected_cases_count": self.selected_cases_count,
            "dataset_cases_count": self.dataset_cases_count,
            "full_dataset_run": self.full_dataset_run,
            "evaluator_library": self.evaluator_library,
            "evaluator_library_version": self.evaluator_library_version,
            "evaluator_mode": self.evaluator_mode,
            "official_metrics": dict(self.official_metrics),
            "official_metric_status": dict(self.official_metric_status),
            "partial_or_blocked_metrics": dict(self.partial_or_blocked_metrics),
            "methodology_notes": list(self.methodology_notes),
        }


@dataclass(slots=True)
class OfflineHeuristicRagasLLM(BaseRagasLLM):
    """Judge deterministico local para executar metricas do Ragas sem provider externo."""

    def generate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: float = 1e-8,
        stop: list[str] | None = None,
        callbacks: Any = None,
    ) -> LLMResult:
        """Renderiza uma resposta JSON compativel com os prompts usados neste bloco."""

        del temperature, stop, callbacks
        prompt_text = prompt.to_string()
        output_text = self._dispatch_prompt(prompt_text)
        return LLMResult(
            generations=[[Generation(text=output_text) for _ in range(max(1, n))]]
        )

    async def agenerate_text(
        self,
        prompt: PromptValue,
        n: int = 1,
        temperature: float | None = None,
        stop: list[str] | None = None,
        callbacks: Any = None,
    ) -> LLMResult:
        """Executa a geracao assincroma reaproveitando a implementacao sincrona."""

        del temperature
        return self.generate_text(prompt=prompt, n=n, stop=stop, callbacks=callbacks)

    def is_finished(self, response: LLMResult) -> bool:
        """Sinaliza ao Ragas que o judge local sempre retorna payload completo."""

        del response
        return True

    def _dispatch_prompt(self, prompt_text: str) -> str:
        """Seleciona o formato de saida correto a partir do prompt do Ragas."""

        if "StatementGeneratorOutput" in prompt_text:
            payload = _extract_input_payload(prompt_text)
            answer = str(payload.get("answer", ""))
            return json.dumps(
                {"statements": _split_answer_into_statements(answer)},
                ensure_ascii=False,
            )

        if "NLIStatementOutput" in prompt_text:
            payload = _extract_input_payload(prompt_text)
            context = str(payload.get("context", ""))
            statements = [str(item) for item in payload.get("statements", [])]
            answers = []
            for statement in statements:
                verdict = _faithfulness_verdict(statement=statement, context=context)
                answers.append(
                    {
                        "statement": statement,
                        "reason": (
                            "Statement grounded in retrieved context."
                            if verdict
                            else "Statement not directly supported by retrieved context."
                        ),
                        "verdict": verdict,
                    }
                )
            return json.dumps({"statements": answers}, ensure_ascii=False)

        if "ResponseRelevanceOutput" in prompt_text:
            payload = _extract_input_payload(prompt_text)
            response = str(payload.get("response", ""))
            return json.dumps(
                {
                    "question": _build_question_from_response(response),
                    "noncommittal": _detect_noncommittal_response(response),
                },
                ensure_ascii=False,
            )

        raise ValueError("Prompt do Ragas nao suportado pelo judge offline atual.")


class OfflineHashRagasEmbeddings(BaseRagasEmbeddings):
    """Adapter de embeddings do Ragas baseado no hash embedding ja usado pelo projeto."""

    def __init__(self, dimensions: int = 32) -> None:
        super().__init__()
        self.run_config = RunConfig()
        self.embedding_function = HashEmbeddingFunction(dimensions=dimensions)

    def embed_query(self, text: str) -> list[float]:
        """Gera embedding sincrono de uma unica query."""

        return self.embedding_function([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Gera embeddings sincronos de uma lista de textos."""

        return self.embedding_function(texts)

    async def aembed_query(self, text: str) -> list[float]:
        """Gera embedding assincromo de uma unica query."""

        return self.embed_query(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Gera embeddings assincromos de uma lista de textos."""

        return self.embed_documents(texts)


@dataclass(slots=True)
class RagasOfflineMetricEvaluator:
    """Executa as metricas da Fase 4 usando Ragas com adapters locais deterministas."""

    stack_resolution: RagEvaluationStackResolution
    llm: BaseRagasLLM | None = None
    embeddings: BaseRagasEmbeddings | None = None
    evaluator_mode: str = "offline_heuristic_ragas"

    def __post_init__(self) -> None:
        """Garante que o executor use a stack primaria definida no bloco anterior."""

        if self.stack_resolution.metric_library != RagEvaluationLibraryName.RAGAS:
            raise ValueError("Este executor suporta apenas Ragas como stack primaria.")
        if self.llm is None:
            self.llm = OfflineHeuristicRagasLLM()
        if self.embeddings is None:
            self.embeddings = OfflineHashRagasEmbeddings()

    async def evaluate_case(
        self,
        case_input: RagEvaluationCaseInput,
    ) -> tuple[RagEvaluationCaseResult, dict[str, str]]:
        """Computa as metricas viaveis do caso e registra os skips observados."""

        skipped_metrics: dict[str, str] = {}
        metric_values: dict[str, float | None] = {
            "faithfulness": None,
            "answer_relevance": None,
            "context_precision": None,
            "context_recall": None,
        }

        metric_values["answer_relevance"], skipped_metrics = await self._score_metric(
            metric_name=RagEvaluationMetricName.ANSWER_RELEVANCE,
            case_input=case_input,
            skipped_metrics=skipped_metrics,
        )
        metric_values["faithfulness"], skipped_metrics = await self._score_metric(
            metric_name=RagEvaluationMetricName.FAITHFULNESS,
            case_input=case_input,
            skipped_metrics=skipped_metrics,
        )

        skipped_metrics = self._register_reference_metric_skip(
            metric_name=RagEvaluationMetricName.CONTEXT_PRECISION,
            case_input=case_input,
            skipped_metrics=skipped_metrics,
        )
        skipped_metrics = self._register_reference_metric_skip(
            metric_name=RagEvaluationMetricName.CONTEXT_RECALL,
            case_input=case_input,
            skipped_metrics=skipped_metrics,
        )

        case_result = build_rag_evaluation_case_result(
            case_input,
            faithfulness=metric_values["faithfulness"],
            answer_relevance=metric_values["answer_relevance"],
            context_precision=metric_values["context_precision"],
            context_recall=metric_values["context_recall"],
        )
        return case_result, skipped_metrics

    async def _score_metric(
        self,
        *,
        metric_name: RagEvaluationMetricName,
        case_input: RagEvaluationCaseInput,
        skipped_metrics: dict[str, str],
    ) -> tuple[float | None, dict[str, str]]:
        """Computa uma metrica obrigatoria do Ragas e captura skips ou falhas."""

        if not case_input.supports_metric(metric_name):
            missing_fields = ",".join(case_input.missing_fields_for_metric(metric_name))
            skipped_metrics[metric_name.value] = f"missing_fields:{missing_fields}"
            return None, skipped_metrics

        sample = SingleTurnSample(
            user_input=case_input.user_input,
            response=case_input.response,
            retrieved_contexts=list(case_input.retrieved_contexts),
            reference=case_input.reference_answer or None,
        )

        metric = self._build_ragas_metric(metric_name)
        try:
            raw_score = await metric.single_turn_ascore(sample)
        except Exception as exc:  # noqa: BLE001
            skipped_metrics[metric_name.value] = f"evaluation_error:{exc.__class__.__name__}"
            return None, skipped_metrics

        if raw_score is None or math.isnan(float(raw_score)):
            skipped_metrics[metric_name.value] = "metric_returned_nan"
            return None, skipped_metrics
        return round(float(raw_score), 4), skipped_metrics

    def _build_ragas_metric(self, metric_name: RagEvaluationMetricName) -> Any:
        """Instancia uma metrica do Ragas com os adapters locais configurados."""

        if metric_name == RagEvaluationMetricName.FAITHFULNESS:
            metric = deepcopy(faithfulness)
            metric.llm = self.llm
            return metric

        if metric_name == RagEvaluationMetricName.ANSWER_RELEVANCE:
            metric = deepcopy(answer_relevancy)
            metric.llm = self.llm
            metric.embeddings = self.embeddings
            return metric

        raise KeyError(f"Metrica do Ragas nao suportada neste bloco: {metric_name.value}")

    def _register_reference_metric_skip(
        self,
        *,
        metric_name: RagEvaluationMetricName,
        case_input: RagEvaluationCaseInput,
        skipped_metrics: dict[str, str],
    ) -> dict[str, str]:
        """Registra skip explicito das metricas de referencia ainda nao viaveis neste bloco."""

        if case_input.reference_answer:
            skipped_metrics[metric_name.value] = "metric_not_enabled_in_block"
            return skipped_metrics

        missing_fields = ",".join(case_input.missing_fields_for_metric(metric_name))
        skipped_metrics[metric_name.value] = f"missing_fields:{missing_fields}"
        return skipped_metrics


@dataclass(slots=True)
class MlflowRagEvaluationTracker:
    """Persiste a run experimental da Fase 4 no MLflow local."""

    tracking_config: MlflowTrackingConfig = MlflowTrackingConfig()

    def log_run(self, execution: RagEvaluationRunExecution) -> LoggedMlflowRun:
        """Registra tags, params, metricas e um relatorio JSON minimo da run."""

        import mlflow
        from mlflow.tracking import MlflowClient

        self.tracking_config.ensure_directories()
        tracking_uri = self.tracking_config.tracking_uri()
        mlflow.set_tracking_uri(tracking_uri)
        client = MlflowClient(tracking_uri=tracking_uri)

        experiment = client.get_experiment_by_name(self.tracking_config.experiment_name)
        if experiment is None:
            experiment_id = client.create_experiment(
                self.tracking_config.experiment_name,
                artifact_location=self.tracking_config.artifacts_dir.resolve().as_uri(),
            )
        else:
            experiment_id = experiment.experiment_id

        previous_rows = self._load_existing_comparison_rows(
            client=client,
            experiment_id=str(experiment_id),
            tenant_id=execution.tenant_id,
        )

        run_name = (
            f"rag_eval__{execution.tenant_id}__{execution.dataset.manifest.dataset_version}"
            f"__{execution.run_request_id[:8]}"
        )
        report_path = (
            self.tracking_config.reports_dir
            / f"{execution.run_request_id}_rag_evaluation_run.json"
        )
        comparison_snapshot_path = (
            self.tracking_config.reports_dir
            / f"{execution.run_request_id}_rag_evaluation_comparison.json"
        )
        comparison_csv_path = (
            self.tracking_config.reports_dir
            / f"{execution.run_request_id}_rag_evaluation_comparison.csv"
        )
        case_ranking_path = (
            self.tracking_config.reports_dir
            / f"{execution.run_request_id}_rag_evaluation_case_ranking.json"
        )
        baseline_summary_path = (
            self.tracking_config.reports_dir
            / f"{execution.run_request_id}_rag_evaluation_baseline_summary.json"
        )

        with mlflow.start_run(experiment_id=experiment_id, run_name=run_name) as run:
            mlflow.set_tags(execution.as_tracking_tags())
            mlflow.log_params(execution.as_tracking_params())
            mlflow.log_metrics(execution.as_tracking_metrics())
            current_row = execution.build_comparison_row(run_id=run.info.run_id)
            comparison_snapshot = RagEvaluationComparisonSnapshot.from_rows(
                experiment_name=self.tracking_config.experiment_name,
                tenant_id=execution.tenant_id,
                rows=(*previous_rows, current_row),
            )
            case_ranking = execution.build_case_ranking_artifact(run_id=run.info.run_id)
            baseline_summary = execution.build_baseline_summary_artifact(run_id=run.info.run_id)
            _write_json_file(report_path, execution.as_artifact_payload())
            _write_json_file(comparison_snapshot_path, comparison_snapshot.as_artifact_payload())
            comparison_snapshot.write_csv(comparison_csv_path)
            _write_json_file(case_ranking_path, case_ranking.as_artifact_payload())
            _write_json_file(baseline_summary_path, baseline_summary.as_artifact_payload())
            mlflow.log_artifact(str(report_path))
            mlflow.log_artifact(str(comparison_snapshot_path))
            mlflow.log_artifact(str(comparison_csv_path))
            mlflow.log_artifact(str(case_ranking_path))
            mlflow.log_artifact(str(baseline_summary_path))
            run_id = run.info.run_id

        return LoggedMlflowRun(
            experiment_id=str(experiment_id),
            run_id=run_id,
            tracking_uri=tracking_uri,
            report_path=report_path,
            comparison_snapshot_path=comparison_snapshot_path,
            comparison_csv_path=comparison_csv_path,
            case_ranking_path=case_ranking_path,
            baseline_summary_path=baseline_summary_path,
        )

    def _load_existing_comparison_rows(
        self,
        *,
        client: Any,
        experiment_id: str,
        tenant_id: str,
    ) -> tuple[RagEvaluationComparisonRow, ...]:
        """Busca runs anteriores do mesmo tenant para montar o snapshot comparativo."""

        prior_runs = client.search_runs(
            experiment_ids=[experiment_id],
            filter_string=f"tags.tenant_id = '{tenant_id}'",
            order_by=["attributes.start_time ASC"],
        )
        return tuple(
            RagEvaluationComparisonRow.from_mlflow_run(
                run=run,
                experiment_name=self.tracking_config.experiment_name,
            )
            for run in prior_runs
        )


@dataclass(slots=True)
class OfflineRagEvaluationExecutor:
    """Executa o benchmark da Fase 3 sobre o pipeline offline da Fase 4."""

    document_repository: FileDocumentRepository | None = None
    chroma_repository: TenantChromaRepository | None = None
    prompt_service: PromptService | None = None
    llm_service: LLMComposeService | None = None
    policy_guard: PolicyGuardService | None = None
    tenant_profile_service: TenantProfileService | None = None
    metric_evaluator: RagMetricEvaluator | None = None
    tracking_config: MlflowTrackingConfig = MlflowTrackingConfig()
    experiment_name: str = DEFAULT_PHASE4_EXPERIMENT_NAME
    reference_answer_builder: Callable[[BenchmarkCase], str] | None = None

    def __post_init__(self) -> None:
        """Inicializa os componentes offline reaproveitados do projeto."""

        self.document_repository = self.document_repository or FileDocumentRepository()
        self.chroma_repository = self.chroma_repository or TenantChromaRepository()
        self.prompt_service = self.prompt_service or PromptService()
        self.llm_service = self.llm_service or LLMComposeService(prompt_service=self.prompt_service)
        self.policy_guard = self.policy_guard or PolicyGuardService()
        self.tenant_profile_service = self.tenant_profile_service or TenantProfileService()
        if self.metric_evaluator is None:
            self.metric_evaluator = RagasOfflineMetricEvaluator(
                stack_resolution=resolve_rag_evaluation_stack()
            )

    async def execute_dataset(
        self,
        *,
        manifest_path: Path,
        tenant_id: str | None = None,
        case_ids: Sequence[str] | None = None,
        max_cases: int | None = None,
    ) -> RagEvaluationRunExecution:
        """Executa uma run completa do benchmark e devolve o agregado experimental."""

        dataset = load_benchmark_dataset(manifest_path)
        resolved_tenant_id = (tenant_id or dataset.manifest.tenant_id).strip()
        if dataset.manifest.tenant_id != resolved_tenant_id:
            raise ValueError("O manifest informado nao corresponde ao tenant_id solicitado.")

        selected_cases = _select_benchmark_cases(
            dataset=dataset,
            case_ids=case_ids,
            max_cases=max_cases,
        )
        if not selected_cases:
            raise ValueError("Nenhum caso elegivel foi selecionado para a avaliacao.")

        run_started_at = perf_counter()
        case_executions: list[RagEvaluationCaseExecution] = []
        for benchmark_case in selected_cases:
            case_executions.append(await self._execute_case(benchmark_case))

        total_latency_ms = round((perf_counter() - run_started_at) * 1000, 3)
        vectorstore_collection = self.chroma_repository.collection_name(resolved_tenant_id)
        vectorstore_fingerprint = self._build_vectorstore_fingerprint(resolved_tenant_id)
        observed_prompt_versions = tuple(
            sorted({case.prompt_version for case in case_executions if case.prompt_version})
        )
        primary_prompt_version = (
            observed_prompt_versions[0]
            if observed_prompt_versions
            else settings.PROMPT_BASE_VERSION
        )
        observed_provider = next(
            (case.model_provider for case in case_executions if case.model_provider),
            settings.LLM_PROVIDER,
        )
        observed_model = next(
            (case.model_name for case in case_executions if case.model_name),
            settings.LLM_MODEL,
        )
        run_request_id = f"req-rag-eval-{uuid4().hex[:12]}"
        tracking_run = build_phase2_tracking_run(
            tenant_id=resolved_tenant_id,
            request_id=run_request_id,
            dataset_version=dataset.manifest.dataset_version,
            prompt_version=primary_prompt_version,
            model_provider=observed_provider,
            model_name=observed_model,
            top_k=self.chroma_repository.artifact_resolver.retrieval_top_k_default(),
            latency_ms=total_latency_ms,
            estimated_cost=0.0,
            artifact_resolver=self.chroma_repository.artifact_resolver,
            chroma_repository=self.chroma_repository,
        )
        summary = build_rag_evaluation_run_summary(
            tenant_id=resolved_tenant_id,
            dataset_version=dataset.manifest.dataset_version,
            case_results=tuple(case.case_result for case in case_executions),
            stack_resolution=self.metric_evaluator.stack_resolution,
        )

        return RagEvaluationRunExecution(
            dataset=dataset,
            case_executions=tuple(case_executions),
            summary=summary,
            tracking_run=tracking_run,
            stack_resolution=self.metric_evaluator.stack_resolution,
            evaluator_mode=self.metric_evaluator.evaluator_mode,
            experiment_name=self.experiment_name,
            dataset_manifest_path=manifest_path,
            vectorstore_fingerprint=vectorstore_fingerprint,
            vectorstore_collection=vectorstore_collection,
            selected_case_ids=tuple(case.case_id for case in selected_cases),
            observed_prompt_versions=observed_prompt_versions,
            total_latency_ms=total_latency_ms,
        )

    async def execute_and_track(
        self,
        *,
        manifest_path: Path,
        tenant_id: str | None = None,
        case_ids: Sequence[str] | None = None,
        max_cases: int | None = None,
    ) -> tuple[RagEvaluationRunExecution, LoggedMlflowRun]:
        """Executa o benchmark offline e registra a run no MLflow local."""

        execution = await self.execute_dataset(
            manifest_path=manifest_path,
            tenant_id=tenant_id,
            case_ids=case_ids,
            max_cases=max_cases,
        )
        tracker = MlflowRagEvaluationTracker(tracking_config=self.tracking_config)
        logged_run = tracker.log_run(execution)
        return execution, logged_run

    async def _execute_case(self, benchmark_case: BenchmarkCase) -> RagEvaluationCaseExecution:
        """Executa o fluxo offline de um caso do benchmark."""

        case_request_id = f"case-{benchmark_case.case_id}-{uuid4().hex[:8]}"
        started_at = perf_counter()
        tenant_profile = self.tenant_profile_service.get_profile(benchmark_case.tenant_id)
        pre_decision = self.policy_guard.evaluate_pre(benchmark_case.input_query, tenant_profile)

        rag_response = self._build_policy_blocked_rag_response(benchmark_case)
        llm_result: LLMGenerationResponse
        initial_reason_code = ""

        if pre_decision.decision == "allow":
            rag_response = self._query_rag_offline(
                tenant_id=benchmark_case.tenant_id,
                query=benchmark_case.input_query,
            )
            if rag_response.status == "ready":
                llm_result = await self.llm_service.compose_answer(
                    tenant_profile=tenant_profile,
                    question=benchmark_case.input_query,
                    context_chunks=rag_response.chunks,
                )
            else:
                initial_reason_code = self._fallback_reason_from_rag(rag_response)
                llm_result = await self.llm_service.compose_fallback(
                    tenant_profile=tenant_profile,
                    question=benchmark_case.input_query,
                    reason_code=initial_reason_code,
                    policy_summary=rag_response.message,
                )
        else:
            initial_reason_code = self._primary_reason_code(pre_decision)
            llm_result = await self.llm_service.compose_fallback(
                tenant_profile=tenant_profile,
                question=benchmark_case.input_query,
                reason_code=initial_reason_code,
                policy_summary=pre_decision.summary,
            )

        post_decision = self.policy_guard.evaluate_post(
            PostPolicyInput(
                question=benchmark_case.input_query,
                candidate_response=llm_result.message,
                rag_response=rag_response,
            ),
            pre_decision=pre_decision,
        )

        final_llm_result = llm_result
        post_reason_code = self._primary_reason_code(post_decision)
        should_rewrite = post_decision.decision != "allow" and (
            llm_result.mode != "fallback" or post_reason_code != initial_reason_code
        )
        if should_rewrite:
            final_llm_result = await self.llm_service.compose_fallback(
                tenant_profile=tenant_profile,
                question=benchmark_case.input_query,
                reason_code=post_reason_code,
                policy_summary=post_decision.summary,
            )

        reference_answer = ""
        if self.reference_answer_builder is not None:
            reference_answer = self.reference_answer_builder(benchmark_case).strip()

        case_input = RagEvaluationCaseInput(
            benchmark_case=benchmark_case,
            response=final_llm_result.message,
            retrieved_contexts=tuple(chunk.text for chunk in rag_response.chunks),
            reference_answer=reference_answer,
        )
        case_result, skipped_metrics = await self.metric_evaluator.evaluate_case(case_input)
        latency_ms = round((perf_counter() - started_at) * 1000, 3)
        status = _classify_case_execution(case_result)

        return RagEvaluationCaseExecution(
            case_input=case_input,
            case_result=case_result,
            status=status,
            skipped_metrics=skipped_metrics,
            rag_status=rag_response.status,
            response_mode=final_llm_result.mode,
            prompt_version=final_llm_result.prompt_version,
            policy_version=post_decision.policy_version,
            model_provider=final_llm_result.provider,
            model_name=final_llm_result.model,
            request_id=case_request_id,
            latency_ms=latency_ms,
            pre_decision=pre_decision,
            post_decision=post_decision,
            retrieved_chunk_titles=tuple(chunk.title for chunk in rag_response.chunks),
            best_score=rag_response.best_score,
        )

    def _query_rag_offline(
        self,
        *,
        tenant_id: str,
        query: str,
    ) -> RagQueryResponse:
        """Executa retrieval offline sem tocar auditoria operacional nem depender do endpoint."""

        top_k = self.chroma_repository.artifact_resolver.retrieval_top_k_default()
        min_score = 0.0
        collection_name = self.chroma_repository.collection_name(tenant_id)
        documents_count = len(self.document_repository.list_documents(tenant_id))
        ingest_status = self.document_repository.read_ingest_status(tenant_id)
        chunks_count = int(ingest_status.get("chunks_count", 0) or 0)

        if documents_count == 0:
            return RagQueryResponse(
                tenant_id=tenant_id,
                query=query,
                status="knowledge_base_not_loaded",
                message=f"Base de conhecimento do tenant '{tenant_id}' ainda nao possui documentos.",
                chunks=[],
                total_chunks=0,
                best_score=0.0,
                params_used=RagQueryParamsUsed(
                    min_score=min_score,
                    top_k=top_k,
                    boost_enabled=False,
                    collection=collection_name,
                ),
            )
        if chunks_count == 0 or collection_name not in self.chroma_repository.list_collection_names():
            return RagQueryResponse(
                tenant_id=tenant_id,
                query=query,
                status="knowledge_base_not_loaded",
                message=(
                    f"Documentos do tenant '{tenant_id}' existem, mas a ingestao ainda nao foi executada."
                ),
                chunks=[],
                total_chunks=0,
                best_score=0.0,
                params_used=RagQueryParamsUsed(
                    min_score=min_score,
                    top_k=top_k,
                    boost_enabled=False,
                    collection=collection_name,
                ),
            )

        collection = self.chroma_repository.client.get_collection(name=collection_name)
        query_embedding = self.chroma_repository.embedding_function([query])[0]
        raw_result = collection.query(
            query_embeddings=[query_embedding],
            n_results=max(top_k * 3, top_k),
        )
        query_tokens = _tokenize(query)
        scored_chunks: list[RagRetrievedChunk] = []
        ids = raw_result.get("ids", [[]])[0]
        documents = raw_result.get("documents", [[]])[0]
        metadatas = raw_result.get("metadatas", [[]])[0]
        distances = raw_result.get("distances", [[]])[0]

        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            semantic_score = 0.0 if distance is None else 1 / (1 + max(float(distance), 0.0))
            lexical_score = _lexical_score(query_tokens=query_tokens, text=text)
            score = round(min(1.0, (lexical_score * 0.75) + (semantic_score * 0.25)), 4)
            if score < min_score:
                continue
            payload = metadata or {}
            scored_chunks.append(
                RagRetrievedChunk(
                    id=str(chunk_id),
                    text=str(text),
                    source=str(payload.get("source", "")),
                    title=str(payload.get("title", "")),
                    section=str(payload.get("section", "")),
                    score=score,
                    tags=_split_tags(str(payload.get("tags", ""))),
                )
            )

        scored_chunks.sort(key=lambda item: (-item.score, item.title, item.id))
        selected_chunks = scored_chunks[:top_k]
        if not selected_chunks:
            return RagQueryResponse(
                tenant_id=tenant_id,
                query=query,
                status="no_results",
                message=f"Nenhum chunk do tenant '{tenant_id}' atingiu o score minimo informado.",
                chunks=[],
                total_chunks=0,
                best_score=0.0,
                params_used=RagQueryParamsUsed(
                    min_score=min_score,
                    top_k=top_k,
                    boost_enabled=False,
                    collection=collection_name,
                ),
            )

        return RagQueryResponse(
            tenant_id=tenant_id,
            query=query,
            status="ready",
            message=f"Recuperados {len(selected_chunks)} chunks para o tenant '{tenant_id}'.",
            chunks=selected_chunks,
            total_chunks=len(selected_chunks),
            best_score=max(chunk.score for chunk in selected_chunks),
            params_used=RagQueryParamsUsed(
                min_score=min_score,
                top_k=top_k,
                boost_enabled=False,
                collection=collection_name,
            ),
        )

    def _build_policy_blocked_rag_response(self, benchmark_case: BenchmarkCase) -> RagQueryResponse:
        """Constroi a resposta tecnica de retrieval quando a policy_pre bloqueia o caso."""

        collection_name = self.chroma_repository.collection_name(benchmark_case.tenant_id)
        return RagQueryResponse(
            tenant_id=benchmark_case.tenant_id,
            query=benchmark_case.input_query,
            status="policy_pre_blocked",
            message="Retrieval nao executado porque a policy_pre bloqueou o request.",
            chunks=[],
            total_chunks=0,
            best_score=0.0,
            params_used=RagQueryParamsUsed(
                min_score=0.0,
                top_k=self.chroma_repository.artifact_resolver.retrieval_top_k_default(),
                boost_enabled=False,
                collection=collection_name,
            ),
        )

    def _fallback_reason_from_rag(self, rag_response: RagQueryResponse) -> str:
        """Traduz o status do retrieval no reason code de fallback esperado pelo pipeline."""

        if rag_response.status == "knowledge_base_not_loaded":
            return "NO_KNOWLEDGE_BASE"
        return "LOW_CONFIDENCE_RETRIEVAL"

    def _primary_reason_code(self, decision: PolicyDecision) -> str:
        """Retorna o primeiro reason code aplicavel da decisao de policy."""

        if decision.reason_codes:
            return decision.reason_codes[0]
        return "POLICY_POST_RESPONSE_REWRITE"

    def _build_vectorstore_fingerprint(self, tenant_id: str) -> str:
        """Gera um fingerprint reproduzivel da base vetorial avaliada."""

        collection_name = self.chroma_repository.collection_name(tenant_id)
        ingest_status = self.document_repository.read_ingest_status(tenant_id)
        documents = self.document_repository.list_documents(tenant_id)
        payload = {
            "tenant_id": tenant_id,
            "collection_name": collection_name,
            "retriever_version": self.chroma_repository.retriever_version(),
            "embedding_version": self.chroma_repository.embedding_version(),
            "documents_count": len(documents),
            "chunks_count": int(ingest_status.get("chunks_count", 0) or 0),
            "last_ingested_at": str(ingest_status.get("last_ingested_at", "")),
            "document_ids": [document.id for document in documents],
        }
        canonical_payload = json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()[:16]
        return f"vectorstore.{tenant_id}.{digest}"


def execute_rag_evaluation_sync(
    *,
    manifest_path: Path,
    tenant_id: str | None = None,
    case_ids: Sequence[str] | None = None,
    max_cases: int | None = None,
    executor: OfflineRagEvaluationExecutor | None = None,
) -> RagEvaluationRunExecution:
    """Conveniencia sincrona para executar a avaliacao offline da Fase 4."""

    runtime_executor = executor or OfflineRagEvaluationExecutor()
    return asyncio.run(
        runtime_executor.execute_dataset(
            manifest_path=manifest_path,
            tenant_id=tenant_id,
            case_ids=case_ids,
            max_cases=max_cases,
        )
    )


def execute_and_track_rag_evaluation_sync(
    *,
    manifest_path: Path,
    tenant_id: str | None = None,
    case_ids: Sequence[str] | None = None,
    max_cases: int | None = None,
    executor: OfflineRagEvaluationExecutor | None = None,
) -> tuple[RagEvaluationRunExecution, LoggedMlflowRun]:
    """Conveniencia sincrona para executar e registrar a run experimental."""

    runtime_executor = executor or OfflineRagEvaluationExecutor()
    return asyncio.run(
        runtime_executor.execute_and_track(
            manifest_path=manifest_path,
            tenant_id=tenant_id,
            case_ids=case_ids,
            max_cases=max_cases,
        )
    )


def _extract_input_payload(prompt_text: str) -> dict[str, Any]:
    """Extrai o ultimo payload JSON de entrada presente no prompt do Ragas."""

    if "input:" not in prompt_text or "Output:" not in prompt_text:
        raise ValueError("Prompt do Ragas sem bloco input/output reconhecivel.")
    raw_payload = prompt_text.rsplit("input:", 1)[1].rsplit("Output:", 1)[0].strip()
    return json.loads(raw_payload)


def _split_answer_into_statements(answer: str) -> list[str]:
    """Quebra a resposta em sentencas simples para a etapa de faithfulness."""

    import re

    normalized_answer = answer.strip()
    normalized_answer = re.sub(
        r"^de acordo com as informacoes institucionais da [^,]+,\s*",
        "",
        normalized_answer,
        flags=re.IGNORECASE,
    )
    normalized_answer = re.sub(
        r"se precisar de atendimento formal,.*$",
        "",
        normalized_answer,
        flags=re.IGNORECASE,
    )
    normalized_answer = re.sub(
        r"(?<=[a-z0-9])\s+(?=(?:A|O|Os|As|Pedidos|Solicitacoes|Documentos|Atendimento|Para|No|Na)\b)",
        ". ",
        normalized_answer,
    )

    normalized_sentences = []
    raw_parts = normalized_answer.replace("?", ".").replace("!", ".").split(".")
    for raw_part in raw_parts:
        statement = raw_part.strip()
        lowered_statement = statement.lower()
        if not statement:
            continue
        if any(snippet in lowered_statement for snippet in BOILERPLATE_RESPONSE_SNIPPETS):
            continue
        normalized_sentences.append(statement.rstrip(".") + ".")
    return normalized_sentences


def _faithfulness_verdict(*, statement: str, context: str) -> int:
    """Decide de forma heuristica se um statement esta ancorado no contexto recuperado."""

    statement_tokens = [
        token for token in _tokenize(statement) if token not in COMMON_STOPWORDS and len(token) >= 4
    ]
    if not statement_tokens:
        return 0

    context_tokens = set(_tokenize(context))
    matched_tokens = sum(1 for token in statement_tokens if token in context_tokens)
    if matched_tokens == 0:
        return 0
    overlap_ratio = matched_tokens / len(statement_tokens)
    return int(overlap_ratio >= 0.5)


def _build_question_from_response(response: str) -> str:
    """Gera uma pergunta sintetica para o score de answer_relevance do Ragas."""

    topic_tokens = [
        token
        for token in _tokenize(response)
        if token not in COMMON_STOPWORDS and len(token) >= 4
    ]
    if not topic_tokens:
        return "Qual e a orientacao institucional principal?"
    selected = " ".join(topic_tokens[:6])
    return f"Qual e a orientacao sobre {selected}?"


def _detect_noncommittal_response(response: str) -> int:
    """Marca respostas evasivas ou de baixa confianca para o score de answer_relevance."""

    lowered = response.lower()
    return int(any(hint in lowered for hint in NONCOMMITTAL_HINTS))


def _classify_case_execution(case_result: RagEvaluationCaseResult) -> RagEvaluationCaseStatus:
    """Classifica o caso conforme as metricas efetivamente computadas."""

    mandatory_values = (
        case_result.faithfulness,
        case_result.answer_relevance,
    )
    all_values = (
        case_result.faithfulness,
        case_result.answer_relevance,
        case_result.context_precision,
        case_result.context_recall,
        case_result.expected_context_coverage,
    )
    if all(value is not None for value in mandatory_values):
        return RagEvaluationCaseStatus.EVALUATED
    if any(value is not None for value in all_values):
        return RagEvaluationCaseStatus.PARTIAL
    return RagEvaluationCaseStatus.SKIPPED


def _select_benchmark_cases(
    *,
    dataset: LoadedBenchmarkDataset,
    case_ids: Sequence[str] | None,
    max_cases: int | None,
) -> tuple[BenchmarkCase, ...]:
    """Seleciona um subconjunto estavel de casos do dataset para a run."""

    selected_cases = list(dataset.cases)
    if case_ids:
        selected_ids = {case_id.strip() for case_id in case_ids if case_id.strip()}
        selected_cases = [case for case in selected_cases if case.case_id in selected_ids]
    if max_cases is not None:
        selected_cases = selected_cases[:max_cases]
    return tuple(selected_cases)


def _relative_to_repo(path: Path) -> str:
    """Renderiza caminho de forma estavel em relatorios e params experimentais."""

    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def _split_tags(raw_tags: str) -> list[str]:
    """Quebra o campo serializado de tags do Chroma no formato usado pelo runtime."""

    if not raw_tags:
        return []
    return [tag for tag in raw_tags.split("|") if tag]


def _tokenize(text: str) -> list[str]:
    """Tokeniza texto em formato compativel com o hash embedding do projeto."""

    import re

    return re.findall(TOKEN_PATTERN, text.lower())


def _lexical_score(*, query_tokens: list[str], text: str) -> float:
    """Calcula o componente lexical do score usado no retrieval offline."""

    if not query_tokens:
        return 0.0
    content_tokens = set(_tokenize(text))
    overlap = len(set(query_tokens) & content_tokens)
    return overlap / len(set(query_tokens))


def _build_methodology_notes(
    *,
    evaluator_mode: str,
    cases_with_methodology_limitations: int,
    skipped_metric_entries: int,
) -> tuple[str, ...]:
    """Consolida notas metodologicas minimas para rows e artifacts comparativos."""

    notes: list[str] = []
    if "heuristic" in evaluator_mode:
        notes.append("offline_heuristic_evaluator")
    if cases_with_methodology_limitations > 0:
        notes.append("benchmark_cases_with_missing_fields")
    if skipped_metric_entries > 0:
        notes.append("skipped_metrics_present")
    return tuple(notes)


def _build_comparison_snapshot_notes(
    rows: Sequence[RagEvaluationComparisonRow],
) -> tuple[str, ...]:
    """Agrega notas metodologicas do snapshot comparativo do experimento."""

    notes: list[str] = []
    if any(row.heuristic_evaluator for row in rows):
        notes.append("scores_from_offline_heuristic_ragas_are_not_external_semantic_judgments")
    if any(row.cases_with_methodology_limitations > 0 for row in rows):
        notes.append("runs_with_missing_fields_or_partial_metrics_remain_explicit")
    if len({row.dataset_version for row in rows if row.dataset_version}) > 1:
        notes.append("multiple_dataset_versions_present_in_same_experiment_snapshot")
    if len({row.evaluator_mode for row in rows if row.evaluator_mode}) > 1:
        notes.append("multiple_evaluator_modes_present_in_same_experiment_snapshot")
    return tuple(notes)


def _coerce_float(value: Any) -> float | None:
    """Converte um valor simples em float quando possivel."""

    if value in ("", None):
        return None
    return round(float(value), 4)


def _coerce_int(value: Any) -> int:
    """Converte um valor simples em inteiro sem propagar NaN textual."""

    if value in ("", None):
        return 0
    return int(round(float(value)))


def _format_mlflow_timestamp(timestamp_ms: int | None) -> str:
    """Converte o timestamp em milissegundos do MLflow para ISO UTC."""

    if not timestamp_ms:
        return ""
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat()


def _write_json_file(path: Path, payload: dict[str, object]) -> None:
    """Escreve um payload JSON com identacao estavel para artifacts da Fase 4."""

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
