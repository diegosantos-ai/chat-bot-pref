"""Contratos offline da Fase 4 para avaliacao formal do pipeline RAG."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from importlib import metadata
from importlib.util import find_spec
import re
from typing import Final, Sequence

from app.audit import EXPERIMENT_TRACKING_BOUNDARY
from app.llmops.benchmark_dataset import BenchmarkCase

WHITESPACE_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s+")


class RagEvaluationLibraryName(StrEnum):
    """Identifica a biblioteca primaria de metricas da avaliacao formal."""

    RAGAS = "ragas"
    DEEPEVAL = "deepeval"


class RagEvaluationMetricScope(StrEnum):
    """Classifica se a metrica e obrigatoria ou complementar na fase."""

    MANDATORY = "mandatory"
    COMPLEMENTARY = "complementary"


class RagEvaluationMetricAggregation(StrEnum):
    """Describe como a metrica e agregada no nivel da run."""

    MEAN = "mean"
    RATE = "rate"


class RagEvaluationMetricName(StrEnum):
    """Enumera os sinais iniciais da avaliacao formal do RAG."""

    FAITHFULNESS = "faithfulness"
    ANSWER_RELEVANCE = "answer_relevance"
    CONTEXT_PRECISION = "context_precision"
    CONTEXT_RECALL = "context_recall"
    EXPECTED_CONTEXT_COVERAGE = "expected_context_coverage"
    RETRIEVAL_EMPTY = "retrieval_empty"


@dataclass(frozen=True, slots=True)
class RagEvaluationLibraryAvailability:
    """Representa a disponibilidade local de uma biblioteca de avaliacao."""

    library_name: RagEvaluationLibraryName
    available: bool
    version: str = ""
    detail: str = ""


@dataclass(frozen=True, slots=True)
class RagEvaluationStackResolution:
    """Consolida a stack escolhida para a avaliacao formal do RAG."""

    metric_library: RagEvaluationLibraryName
    metric_library_version: str
    tracking_target: str
    resolution_order: tuple[RagEvaluationLibraryName, ...]


@dataclass(frozen=True, slots=True)
class RagEvaluationMetricDefinition:
    """Formaliza o contrato de uma metrica da Fase 4."""

    metric_name: RagEvaluationMetricName
    scope: RagEvaluationMetricScope
    aggregation: RagEvaluationMetricAggregation
    provider_library: RagEvaluationLibraryName | None
    provider_metric_name: str | None
    required_case_fields: tuple[str, ...]
    description: str
    methodology_notes: tuple[str, ...]


DEFAULT_RAG_EVALUATION_LIBRARY_ORDER: Final[tuple[RagEvaluationLibraryName, ...]] = (
    RagEvaluationLibraryName.RAGAS,
    RagEvaluationLibraryName.DEEPEVAL,
)

PHASE4_RAG_EVALUATION_METRICS: Final[tuple[RagEvaluationMetricDefinition, ...]] = (
    RagEvaluationMetricDefinition(
        metric_name=RagEvaluationMetricName.FAITHFULNESS,
        scope=RagEvaluationMetricScope.MANDATORY,
        aggregation=RagEvaluationMetricAggregation.MEAN,
        provider_library=RagEvaluationLibraryName.RAGAS,
        provider_metric_name="faithfulness",
        required_case_fields=("user_input", "response", "retrieved_contexts"),
        description="Mede se a resposta se mantem fiel ao contexto efetivamente recuperado.",
        methodology_notes=(
            "Nao deve ser computada quando o retrieval vier vazio.",
            "Nota alta nao substitui leitura dos piores casos.",
        ),
    ),
    RagEvaluationMetricDefinition(
        metric_name=RagEvaluationMetricName.ANSWER_RELEVANCE,
        scope=RagEvaluationMetricScope.MANDATORY,
        aggregation=RagEvaluationMetricAggregation.MEAN,
        provider_library=RagEvaluationLibraryName.RAGAS,
        provider_metric_name="answer_relevancy",
        required_case_fields=("user_input", "response"),
        description="Mede se a resposta e relevante para a pergunta do usuario.",
        methodology_notes=(
            "O nome interno do contrato e answer_relevance para manter leitura consistente na fase.",
            "Na biblioteca Ragas 0.2.x a metrica equivalente se chama answer_relevancy.",
        ),
    ),
    RagEvaluationMetricDefinition(
        metric_name=RagEvaluationMetricName.CONTEXT_PRECISION,
        scope=RagEvaluationMetricScope.COMPLEMENTARY,
        aggregation=RagEvaluationMetricAggregation.MEAN,
        provider_library=RagEvaluationLibraryName.RAGAS,
        provider_metric_name="context_precision",
        required_case_fields=("user_input", "retrieved_contexts", "reference_answer"),
        description="Mede o quanto o contexto recuperado evita ruido frente a uma referencia explicita.",
        methodology_notes=(
            "Exige reference_answer textual; o dataset atual nao fornece esse campo como gabarito literal.",
            "Sem reference_answer explicita, a metrica deve ficar ausente e nao ser inferida silenciosamente.",
        ),
    ),
    RagEvaluationMetricDefinition(
        metric_name=RagEvaluationMetricName.CONTEXT_RECALL,
        scope=RagEvaluationMetricScope.COMPLEMENTARY,
        aggregation=RagEvaluationMetricAggregation.MEAN,
        provider_library=RagEvaluationLibraryName.RAGAS,
        provider_metric_name="context_recall",
        required_case_fields=("user_input", "retrieved_contexts", "reference_answer"),
        description="Mede o quanto o retrieval cobriu a referencia explicita necessaria para responder.",
        methodology_notes=(
            "Exige reference_answer textual; o dataset atual ainda precisa de curadoria adicional para isso.",
            "Nao deve ser usado como atalho para declarar cobertura sem referencia comparavel.",
        ),
    ),
    RagEvaluationMetricDefinition(
        metric_name=RagEvaluationMetricName.EXPECTED_CONTEXT_COVERAGE,
        scope=RagEvaluationMetricScope.COMPLEMENTARY,
        aggregation=RagEvaluationMetricAggregation.MEAN,
        provider_library=None,
        provider_metric_name=None,
        required_case_fields=("retrieved_contexts", "expected_context_terms"),
        description="Sinal derivado localmente da cobertura dos termos esperados no contexto recuperado.",
        methodology_notes=(
            "Usa matching textual simples sobre required_terms do benchmark atual.",
            "Serve como diagnostico inicial de grounding, nao como substituto de context_precision/context_recall.",
        ),
    ),
    RagEvaluationMetricDefinition(
        metric_name=RagEvaluationMetricName.RETRIEVAL_EMPTY,
        scope=RagEvaluationMetricScope.COMPLEMENTARY,
        aggregation=RagEvaluationMetricAggregation.RATE,
        provider_library=None,
        provider_metric_name=None,
        required_case_fields=(),
        description="Flag por caso que alimenta a taxa agregada de retrieval vazio da run.",
        methodology_notes=(
            "A taxa agregada deve ser lida junto do motivo do vazio: base ausente, score baixo ou ruido de consulta.",
            "E um sinal estrutural do pipeline, nao uma nota semantica de qualidade por si so.",
        ),
    ),
)

PHASE4_MANDATORY_RAG_EVALUATION_METRICS: Final[tuple[RagEvaluationMetricDefinition, ...]] = tuple(
    metric for metric in PHASE4_RAG_EVALUATION_METRICS if metric.scope == RagEvaluationMetricScope.MANDATORY
)

PHASE4_INITIAL_COMPLEMENTARY_RAG_EVALUATION_METRICS: Final[tuple[RagEvaluationMetricDefinition, ...]] = tuple(
    metric for metric in PHASE4_RAG_EVALUATION_METRICS if metric.scope == RagEvaluationMetricScope.COMPLEMENTARY
)


@dataclass(frozen=True, slots=True)
class RagEvaluationCaseInput:
    """Representa a entrada minima por caso da avaliacao formal."""

    benchmark_case: BenchmarkCase
    response: str
    retrieved_contexts: tuple[str, ...]
    reference_answer: str = ""

    def __post_init__(self) -> None:
        """Normaliza e valida os campos minimos do caso avaliado."""

        normalized_response = str(self.response).strip()
        if not normalized_response:
            raise ValueError("response obrigatoria para avaliar um caso do benchmark.")

        normalized_contexts = tuple(
            text.strip() for text in self.retrieved_contexts if str(text).strip()
        )
        normalized_reference_answer = str(self.reference_answer).strip()

        object.__setattr__(self, "response", normalized_response)
        object.__setattr__(self, "retrieved_contexts", normalized_contexts)
        object.__setattr__(self, "reference_answer", normalized_reference_answer)

    @property
    def case_id(self) -> str:
        """Retorna o identificador estavel do caso do benchmark."""

        return self.benchmark_case.case_id

    @property
    def tenant_id(self) -> str:
        """Retorna o tenant_id herdado do benchmark versionado."""

        return self.benchmark_case.tenant_id

    @property
    def user_input(self) -> str:
        """Retorna a pergunta avaliada do benchmark."""

        return self.benchmark_case.input_query

    @property
    def expected_context_terms(self) -> tuple[str, ...]:
        """Retorna os termos minimos esperados para grounding do caso."""

        return self.benchmark_case.expected_context_reference.required_terms

    def retrieval_empty(self) -> bool:
        """Indica se o caso terminou sem contexto recuperado."""

        return not self.retrieved_contexts

    def missing_fields_for_metric(
        self,
        metric_name: RagEvaluationMetricName,
    ) -> tuple[str, ...]:
        """Retorna os campos conceituais ausentes para uma metrica do catalogo."""

        metric_definition = get_rag_evaluation_metric(metric_name)
        missing_fields: list[str] = []

        for field_name in metric_definition.required_case_fields:
            if field_name == "user_input" and not self.user_input.strip():
                missing_fields.append(field_name)
            elif field_name == "response" and not self.response.strip():
                missing_fields.append(field_name)
            elif field_name == "retrieved_contexts" and self.retrieval_empty():
                missing_fields.append(field_name)
            elif field_name == "reference_answer" and not self.reference_answer:
                missing_fields.append(field_name)
            elif field_name == "expected_context_terms" and not self.expected_context_terms:
                missing_fields.append(field_name)

        return tuple(missing_fields)

    def supports_metric(self, metric_name: RagEvaluationMetricName) -> bool:
        """Informa se o caso possui os dados minimos para a metrica informada."""

        return not self.missing_fields_for_metric(metric_name)


@dataclass(frozen=True, slots=True)
class RagEvaluationCaseResult:
    """Representa a saida minima por caso da avaliacao formal."""

    case_input: RagEvaluationCaseInput
    faithfulness: float | None = None
    answer_relevance: float | None = None
    context_precision: float | None = None
    context_recall: float | None = None
    expected_context_coverage: float | None = None

    def __post_init__(self) -> None:
        """Valida consistencia entre valores informados e o contrato do caso."""

        self._validate_metric(RagEvaluationMetricName.FAITHFULNESS, self.faithfulness)
        self._validate_metric(RagEvaluationMetricName.ANSWER_RELEVANCE, self.answer_relevance)
        self._validate_metric(RagEvaluationMetricName.CONTEXT_PRECISION, self.context_precision)
        self._validate_metric(RagEvaluationMetricName.CONTEXT_RECALL, self.context_recall)
        self._validate_metric(
            RagEvaluationMetricName.EXPECTED_CONTEXT_COVERAGE,
            self.expected_context_coverage,
        )

    @property
    def retrieval_empty(self) -> bool:
        """Expõe a flag por caso usada no calculo agregado da taxa de vazio."""

        return self.case_input.retrieval_empty()

    def as_artifact_payload(self) -> dict[str, object]:
        """Retorna a carga serializavel minima do caso avaliado."""

        return {
            "case_id": self.case_input.case_id,
            "tenant_id": self.case_input.tenant_id,
            "faithfulness": self.faithfulness,
            "answer_relevance": self.answer_relevance,
            "context_precision": self.context_precision,
            "context_recall": self.context_recall,
            "expected_context_coverage": self.expected_context_coverage,
            "retrieval_empty": self.retrieval_empty,
        }

    def _validate_metric(
        self,
        metric_name: RagEvaluationMetricName,
        value: float | None,
    ) -> None:
        """Valida faixa numerica e pre-condicao minima de uma metrica."""

        if value is None:
            return
        if value < 0.0 or value > 1.0:
            raise ValueError(f"{metric_name.value} deve ficar entre 0.0 e 1.0.")
        if not self.case_input.supports_metric(metric_name):
            raise ValueError(
                f"{metric_name.value} nao pode ser preenchida sem {self.case_input.missing_fields_for_metric(metric_name)}."
            )


@dataclass(frozen=True, slots=True)
class RagEvaluationRunSummary:
    """Consolida as metricas agregadas minimas por run de avaliacao formal."""

    tenant_id: str
    dataset_version: str
    metric_library: RagEvaluationLibraryName
    metric_library_version: str
    tracking_target: str
    total_cases: int
    metric_case_counts: dict[str, int]
    faithfulness_mean: float | None
    answer_relevance_mean: float | None
    context_precision_mean: float | None
    context_recall_mean: float | None
    expected_context_coverage_mean: float | None
    retrieval_empty_rate: float

    def as_metrics(self) -> dict[str, float]:
        """Retorna o payload numerico minimo para tracking experimental por run."""

        metrics: dict[str, float] = {
            "retrieval_empty_rate": self.retrieval_empty_rate,
            "cases_total": float(self.total_cases),
        }
        optional_metrics = {
            "faithfulness_mean": self.faithfulness_mean,
            "answer_relevance_mean": self.answer_relevance_mean,
            "context_precision_mean": self.context_precision_mean,
            "context_recall_mean": self.context_recall_mean,
            "expected_context_coverage_mean": self.expected_context_coverage_mean,
        }
        for metric_name, value in optional_metrics.items():
            if value is not None:
                metrics[metric_name] = value
        return metrics

    def as_artifact_payload(self) -> dict[str, object]:
        """Retorna a carga serializavel do resumo agregado da run."""

        return {
            "tenant_id": self.tenant_id,
            "dataset_version": self.dataset_version,
            "metric_library": self.metric_library.value,
            "metric_library_version": self.metric_library_version,
            "tracking_target": self.tracking_target,
            "total_cases": self.total_cases,
            "metric_case_counts": dict(self.metric_case_counts),
            "metrics": self.as_metrics(),
        }


def inspect_rag_evaluation_libraries() -> tuple[RagEvaluationLibraryAvailability, ...]:
    """Inspeciona a disponibilidade local das bibliotecas previstas para avaliacao."""

    return tuple(_inspect_evaluation_library(library_name) for library_name in DEFAULT_RAG_EVALUATION_LIBRARY_ORDER)


def resolve_rag_evaluation_stack(
    preferred_order: Sequence[RagEvaluationLibraryName] = DEFAULT_RAG_EVALUATION_LIBRARY_ORDER,
) -> RagEvaluationStackResolution:
    """Resolve a stack preferencial de avaliacao sem instalar dependencia nova."""

    availability_by_library = {
        availability.library_name: availability for availability in inspect_rag_evaluation_libraries()
    }
    normalized_order = tuple(preferred_order)

    for library_name in normalized_order:
        availability = availability_by_library.get(library_name)
        if availability is not None and availability.available:
            return RagEvaluationStackResolution(
                metric_library=library_name,
                metric_library_version=availability.version,
                tracking_target=EXPERIMENT_TRACKING_BOUNDARY.storage_target,
                resolution_order=normalized_order,
            )

    unavailable_details = ", ".join(
        f"{availability.library_name.value}: {availability.detail or 'indisponivel'}"
        for availability in availability_by_library.values()
    )
    raise RuntimeError(
        "Nenhuma biblioteca de avaliacao formal esta disponivel no ambiente atual. "
        f"Detalhes: {unavailable_details}"
    )


def get_rag_evaluation_metric(
    metric_name: RagEvaluationMetricName,
) -> RagEvaluationMetricDefinition:
    """Recupera a definicao de uma metrica a partir do catalogo da fase."""

    for metric_definition in PHASE4_RAG_EVALUATION_METRICS:
        if metric_definition.metric_name == metric_name:
            return metric_definition
    raise KeyError(f"Metrica de avaliacao RAG desconhecida: {metric_name.value}")


def build_rag_evaluation_case_result(
    case_input: RagEvaluationCaseInput,
    *,
    faithfulness: float | None = None,
    answer_relevance: float | None = None,
    context_precision: float | None = None,
    context_recall: float | None = None,
    expected_context_coverage: float | None = None,
) -> RagEvaluationCaseResult:
    """Monta a saida minima por caso com a cobertura derivada quando possivel."""

    coverage_value = expected_context_coverage
    if coverage_value is None:
        coverage_value = compute_expected_context_coverage(case_input)

    return RagEvaluationCaseResult(
        case_input=case_input,
        faithfulness=faithfulness,
        answer_relevance=answer_relevance,
        context_precision=context_precision,
        context_recall=context_recall,
        expected_context_coverage=coverage_value,
    )


def build_rag_evaluation_run_summary(
    *,
    tenant_id: str,
    dataset_version: str,
    case_results: Sequence[RagEvaluationCaseResult],
    stack_resolution: RagEvaluationStackResolution | None = None,
) -> RagEvaluationRunSummary:
    """Agrega as metricas minimas de uma run offline de avaliacao formal."""

    normalized_tenant_id = tenant_id.strip()
    normalized_dataset_version = dataset_version.strip()
    if not normalized_tenant_id:
        raise ValueError("tenant_id obrigatorio para resumir uma run de avaliacao.")
    if not normalized_dataset_version:
        raise ValueError("dataset_version obrigatorio para resumir uma run de avaliacao.")
    if not case_results:
        raise ValueError("case_results deve conter ao menos um caso avaliado.")

    for result in case_results:
        if result.case_input.tenant_id != normalized_tenant_id:
            raise ValueError("Todos os casos da run devem respeitar o mesmo tenant_id.")

    resolution = stack_resolution or resolve_rag_evaluation_stack()

    faithfulness_values = [result.faithfulness for result in case_results if result.faithfulness is not None]
    answer_relevance_values = [
        result.answer_relevance for result in case_results if result.answer_relevance is not None
    ]
    context_precision_values = [
        result.context_precision for result in case_results if result.context_precision is not None
    ]
    context_recall_values = [result.context_recall for result in case_results if result.context_recall is not None]
    expected_context_coverage_values = [
        result.expected_context_coverage
        for result in case_results
        if result.expected_context_coverage is not None
    ]
    retrieval_empty_count = sum(1 for result in case_results if result.retrieval_empty)

    metric_case_counts = {
        "faithfulness": len(faithfulness_values),
        "answer_relevance": len(answer_relevance_values),
        "context_precision": len(context_precision_values),
        "context_recall": len(context_recall_values),
        "expected_context_coverage": len(expected_context_coverage_values),
        "retrieval_empty": retrieval_empty_count,
    }

    return RagEvaluationRunSummary(
        tenant_id=normalized_tenant_id,
        dataset_version=normalized_dataset_version,
        metric_library=resolution.metric_library,
        metric_library_version=resolution.metric_library_version,
        tracking_target=resolution.tracking_target,
        total_cases=len(case_results),
        metric_case_counts=metric_case_counts,
        faithfulness_mean=_mean_or_none(faithfulness_values),
        answer_relevance_mean=_mean_or_none(answer_relevance_values),
        context_precision_mean=_mean_or_none(context_precision_values),
        context_recall_mean=_mean_or_none(context_recall_values),
        expected_context_coverage_mean=_mean_or_none(expected_context_coverage_values),
        retrieval_empty_rate=round(retrieval_empty_count / len(case_results), 4),
    )


def compute_expected_context_coverage(
    case_input: RagEvaluationCaseInput,
) -> float | None:
    """Calcula a cobertura lexical simples dos termos esperados no contexto recuperado."""

    if not case_input.supports_metric(RagEvaluationMetricName.EXPECTED_CONTEXT_COVERAGE):
        return None

    normalized_terms = tuple(
        normalized_term
        for term in case_input.expected_context_terms
        if (normalized_term := _normalize_text(term))
    )
    if not normalized_terms:
        return None

    normalized_context = _normalize_text(" ".join(case_input.retrieved_contexts))
    matched_terms = sum(1 for term in normalized_terms if term in normalized_context)
    return round(matched_terms / len(normalized_terms), 4)


def _inspect_evaluation_library(
    library_name: RagEvaluationLibraryName,
) -> RagEvaluationLibraryAvailability:
    """Inspeciona um modulo de avaliacao sem acoplar o runtime a importacao dele."""

    module_name = library_name.value
    if find_spec(module_name) is None:
        return RagEvaluationLibraryAvailability(
            library_name=library_name,
            available=False,
            detail="modulo nao encontrado no ambiente atual",
        )

    try:
        version = metadata.version(module_name)
    except metadata.PackageNotFoundError:
        version = ""

    detail = "modulo disponivel"
    if not version:
        detail = "modulo disponivel sem versao identificada"

    return RagEvaluationLibraryAvailability(
        library_name=library_name,
        available=True,
        version=version,
        detail=detail,
    )


def _mean_or_none(values: Sequence[float | None]) -> float | None:
    """Calcula a media arredondada quando houver valores validos."""

    filtered_values = [value for value in values if value is not None]
    if not filtered_values:
        return None
    return round(sum(filtered_values) / len(filtered_values), 4)


def _normalize_text(value: str) -> str:
    """Normaliza texto para matching simples de cobertura lexical."""

    return WHITESPACE_PATTERN.sub(" ", value.strip().lower())
