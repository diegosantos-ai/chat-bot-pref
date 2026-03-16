"""Contratos minimos da Fase 6 para observabilidade de qualidade, latencia e custo por tenant."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class ObservabilitySignalLayer(StrEnum):
    """Classifica em qual camada arquitetural o sinal pertence."""

    OPERATIONAL_METRIC = "operational_metric"
    AUDIT_SIGNAL = "audit_signal"
    EXPERIMENT_TRACKING_SIGNAL = "experiment_tracking_signal"
    CONTRACT_ONLY = "contract_only"


class ObservabilityMetricType(StrEnum):
    """Define o tipo tecnico da metrica operacional planejada."""

    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"


class PipelineStageName(StrEnum):
    """Nomeia os estagios observaveis do pipeline de atendimento."""

    REQUEST_ENTRY = "request_entry"
    CLASSIFICATION = "classification"
    POLICY_PRE = "policy_pre"
    QUERY_EXPANSION = "query_expansion"
    RETRIEVAL = "retrieval"
    COMPOSER = "composer"
    POLICY_POST = "policy_post"
    RESPONSE_FINAL = "response_final"
    FALLBACK = "fallback"
    BLOCKED = "blocked"


class ContractStatus(StrEnum):
    """Indica se o sinal esta ativo, apenas definido ou fora do runtime atual."""

    ACTIVE = "active"
    PLANNED = "planned"
    NOT_APPLICABLE_CURRENT_RUNTIME = "not_applicable_current_runtime"


@dataclass(frozen=True, slots=True)
class MetricDimensions:
    """Agrupa dimensoes obrigatorias, opcionais e proibidas para uma metrica."""

    required: tuple[str, ...]
    optional: tuple[str, ...]
    prohibited: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Phase6MetricDefinition:
    """Define o contrato minimo de uma metrica da Fase 6."""

    name: str
    layer: ObservabilitySignalLayer
    metric_type: ObservabilityMetricType
    stage_name: PipelineStageName
    description: str
    dimensions: MetricDimensions
    status: ContractStatus
    source_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Phase6InstrumentationPoint:
    """Mapeia um ponto natural de instrumentacao sem impor implementacao imediata."""

    stage_name: PipelineStageName
    source_path: str
    purpose: str
    status: ContractStatus
    notes: str = ""


PHASE6_OPERATIONAL_DIMENSIONS_BASE: Final[MetricDimensions] = MetricDimensions(
    required=("tenant_id", "stage_name"),
    optional=(
        "channel",
        "status",
        "result",
        "reason_code",
        "retrieval_strategy_name",
        "query_transform_strategy_name",
        "rerank_strategy_name",
        "llm_provider",
        "llm_model",
    ),
    prohibited=(
        "message",
        "user_message",
        "assistant_message",
        "document_text",
        "full_name",
        "email",
        "phone",
        "cpf",
        "token_raw",
    ),
)


PHASE6_MINIMAL_METRICS: Final[tuple[Phase6MetricDefinition, ...]] = (
    Phase6MetricDefinition(
        name="chatpref_pipeline_requests_total",
        layer=ObservabilitySignalLayer.OPERATIONAL_METRIC,
        metric_type=ObservabilityMetricType.COUNTER,
        stage_name=PipelineStageName.REQUEST_ENTRY,
        description="Total de requisicoes aceitas para processamento no pipeline por tenant.",
        dimensions=PHASE6_OPERATIONAL_DIMENSIONS_BASE,
        status=ContractStatus.PLANNED,
        source_paths=(
            "app/observability/middleware.py:RequestObservabilityMiddleware.dispatch",
            "app/services/chat_service.py:process",
        ),
    ),
    Phase6MetricDefinition(
        name="chatpref_pipeline_stage_latency_seconds",
        layer=ObservabilitySignalLayer.OPERATIONAL_METRIC,
        metric_type=ObservabilityMetricType.HISTOGRAM,
        stage_name=PipelineStageName.RETRIEVAL,
        description="Latencia por estagio do pipeline com recorte por tenant e etapa.",
        dimensions=PHASE6_OPERATIONAL_DIMENSIONS_BASE,
        status=ContractStatus.PLANNED,
        source_paths=(
            "app/services/chat_service.py:policy_pre",
            "app/services/chat_service.py:retrieval",
            "app/services/chat_service.py:compose",
            "app/services/chat_service.py:policy_post",
            "app/services/chat_service.py:response",
        ),
    ),
    Phase6MetricDefinition(
        name="chatpref_pipeline_estimated_cost_usd_total",
        layer=ObservabilitySignalLayer.OPERATIONAL_METRIC,
        metric_type=ObservabilityMetricType.COUNTER,
        stage_name=PipelineStageName.COMPOSER,
        description="Custo estimado acumulado do estagio de composicao/fallback por tenant.",
        dimensions=PHASE6_OPERATIONAL_DIMENSIONS_BASE,
        status=ContractStatus.PLANNED,
        source_paths=(
            "app/services/llm_service.py:compose_answer",
            "app/services/llm_service.py:compose_fallback",
        ),
    ),
    Phase6MetricDefinition(
        name="chatpref_pipeline_fallback_total",
        layer=ObservabilitySignalLayer.OPERATIONAL_METRIC,
        metric_type=ObservabilityMetricType.COUNTER,
        stage_name=PipelineStageName.FALLBACK,
        description="Total de respostas em modo fallback por tenant e motivo principal.",
        dimensions=PHASE6_OPERATIONAL_DIMENSIONS_BASE,
        status=ContractStatus.PLANNED,
        source_paths=(
            "app/services/chat_service.py:_compose_fallback_with_span",
            "app/observability/metrics.py:record_llm_composition",
        ),
    ),
    Phase6MetricDefinition(
        name="chatpref_pipeline_policy_block_total",
        layer=ObservabilitySignalLayer.OPERATIONAL_METRIC,
        metric_type=ObservabilityMetricType.COUNTER,
        stage_name=PipelineStageName.BLOCKED,
        description="Total de bloqueios de policy_pre ou policy_post por tenant.",
        dimensions=PHASE6_OPERATIONAL_DIMENSIONS_BASE,
        status=ContractStatus.PLANNED,
        source_paths=(
            "app/services/chat_service.py:policy_pre",
            "app/services/chat_service.py:policy_post",
            "app/observability/metrics.py:record_policy_decision",
        ),
    ),
    Phase6MetricDefinition(
        name="chatpref_pipeline_retrieval_empty_total",
        layer=ObservabilitySignalLayer.OPERATIONAL_METRIC,
        metric_type=ObservabilityMetricType.COUNTER,
        stage_name=PipelineStageName.RETRIEVAL,
        description="Total de retrieval sem chunks uteis por tenant.",
        dimensions=PHASE6_OPERATIONAL_DIMENSIONS_BASE,
        status=ContractStatus.PLANNED,
        source_paths=(
            "app/services/rag_service.py:query",
            "app/observability/metrics.py:record_retrieval",
        ),
    ),
    Phase6MetricDefinition(
        name="audit_v1_pipeline_events_total",
        layer=ObservabilitySignalLayer.AUDIT_SIGNAL,
        metric_type=ObservabilityMetricType.COUNTER,
        stage_name=PipelineStageName.RESPONSE_FINAL,
        description="Contagem derivavel dos eventos audit.v1 por tenant (nao exposta em /metrics).",
        dimensions=MetricDimensions(
            required=("tenant_id", "event_type"),
            optional=("request_id", "session_id", "channel", "policy_stage", "decision"),
            prohibited=PHASE6_OPERATIONAL_DIMENSIONS_BASE.prohibited,
        ),
        status=ContractStatus.ACTIVE,
        source_paths=(
            "app/services/chat_service.py:_append_event",
            "app/storage/audit_repository.py:append_event",
        ),
    ),
    Phase6MetricDefinition(
        name="tracking_run_latency_ms",
        layer=ObservabilitySignalLayer.EXPERIMENT_TRACKING_SIGNAL,
        metric_type=ObservabilityMetricType.GAUGE,
        stage_name=PipelineStageName.RESPONSE_FINAL,
        description="Latencia por run no tracking experimental (fora do runtime transacional).",
        dimensions=MetricDimensions(
            required=("tenant_id", "run_id"),
            optional=(
                "dataset_version",
                "retrieval_strategy_name",
                "query_transform_strategy_name",
                "rerank_strategy_name",
            ),
            prohibited=PHASE6_OPERATIONAL_DIMENSIONS_BASE.prohibited,
        ),
        status=ContractStatus.ACTIVE,
        source_paths=(
            "app/llmops/tracking_integration.py:build_phase2_tracking_run",
            "app/llmops/rag_evaluation_runner.py:as_tracking_metrics",
        ),
    ),
    Phase6MetricDefinition(
        name="chatpref_pipeline_classification_latency_seconds",
        layer=ObservabilitySignalLayer.CONTRACT_ONLY,
        metric_type=ObservabilityMetricType.HISTOGRAM,
        stage_name=PipelineStageName.CLASSIFICATION,
        description="Metrica reservada para classificacao quando o estagio existir no runtime.",
        dimensions=PHASE6_OPERATIONAL_DIMENSIONS_BASE,
        status=ContractStatus.NOT_APPLICABLE_CURRENT_RUNTIME,
        source_paths=("app/classifier/",),
    ),
)


PHASE6_INSTRUMENTATION_CANDIDATES: Final[tuple[Phase6InstrumentationPoint, ...]] = (
    Phase6InstrumentationPoint(
        stage_name=PipelineStageName.REQUEST_ENTRY,
        source_path="app/observability/middleware.py:RequestObservabilityMiddleware.dispatch",
        purpose="Capturar inicio/fim do request HTTP e correlacao por request_id.",
        status=ContractStatus.ACTIVE,
    ),
    Phase6InstrumentationPoint(
        stage_name=PipelineStageName.POLICY_PRE,
        source_path="app/services/chat_service.py:process",
        purpose="Registrar decisao policy_pre e preparar metrica de latencia da etapa.",
        status=ContractStatus.ACTIVE,
    ),
    Phase6InstrumentationPoint(
        stage_name=PipelineStageName.QUERY_EXPANSION,
        source_path="app/services/rag_service.py:query",
        purpose="Registrar estrategia e aplicacao da transformacao de query.",
        status=ContractStatus.ACTIVE,
    ),
    Phase6InstrumentationPoint(
        stage_name=PipelineStageName.RETRIEVAL,
        source_path="app/services/rag_service.py:query",
        purpose="Capturar latencia, status e resultado vazio do retrieval por tenant.",
        status=ContractStatus.ACTIVE,
    ),
    Phase6InstrumentationPoint(
        stage_name=PipelineStageName.COMPOSER,
        source_path="app/services/chat_service.py:_compose_with_span",
        purpose="Capturar latencia e metadados de composicao/fallback do provedor LLM.",
        status=ContractStatus.ACTIVE,
    ),
    Phase6InstrumentationPoint(
        stage_name=PipelineStageName.POLICY_POST,
        source_path="app/services/chat_service.py:process",
        purpose="Registrar decisao policy_post e possivel reescrita de resposta.",
        status=ContractStatus.ACTIVE,
    ),
    Phase6InstrumentationPoint(
        stage_name=PipelineStageName.RESPONSE_FINAL,
        source_path="app/storage/chat_repository.py:append_exchange",
        purpose="Fixar o ponto final do runtime com persistencia correlacionada.",
        status=ContractStatus.ACTIVE,
    ),
    Phase6InstrumentationPoint(
        stage_name=PipelineStageName.FALLBACK,
        source_path="app/services/chat_service.py:_compose_fallback_with_span",
        purpose="Separar fallback por razao e permitir leitura de taxa por tenant.",
        status=ContractStatus.ACTIVE,
    ),
    Phase6InstrumentationPoint(
        stage_name=PipelineStageName.BLOCKED,
        source_path="app/services/chat_service.py:process",
        purpose="Explicitar bloqueios de policy sem misturar com tracking experimental.",
        status=ContractStatus.ACTIVE,
    ),
    Phase6InstrumentationPoint(
        stage_name=PipelineStageName.CLASSIFICATION,
        source_path="app/classifier/",
        purpose="Reservar estagio de classificacao para futura instrumentacao quando ativo.",
        status=ContractStatus.NOT_APPLICABLE_CURRENT_RUNTIME,
        notes="No runtime atual nao ha modulo de classificacao ativo no caminho transacional.",
    ),
)
