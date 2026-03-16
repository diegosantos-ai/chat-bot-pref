from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from time import perf_counter

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, generate_latest

from app.observability.phase6_contracts import PipelineStageName


REGISTRY = CollectorRegistry()

CHAT_REQUESTS_TOTAL = Counter(
    "chatpref_chat_requests_total",
    "Total de requests processados pelo fluxo principal de chat.",
    labelnames=("channel",),
    registry=REGISTRY,
)

POLICY_DECISIONS_TOTAL = Counter(
    "chatpref_policy_decisions_total",
    "Decisoes tomadas pelos guardrails pre e post.",
    labelnames=("stage", "decision", "reason_code", "channel"),
    registry=REGISTRY,
)

RETRIEVAL_TOTAL = Counter(
    "chatpref_retrieval_total",
    "Status do retrieval do tenant demonstrativo.",
    labelnames=("status", "channel"),
    registry=REGISTRY,
)

LLM_COMPOSITIONS_TOTAL = Counter(
    "chatpref_llm_compositions_total",
    "Total de composicoes e fallbacks executados pelo adaptador LLM.",
    labelnames=("provider", "mode", "channel"),
    registry=REGISTRY,
)

LLM_COMPOSE_LATENCY_SECONDS = Histogram(
    "chatpref_llm_compose_latency_seconds",
    "Latencia da composicao ou fallback do adaptador LLM.",
    labelnames=("provider", "mode", "channel"),
    registry=REGISTRY,
)

PIPELINE_STAGE_LATENCY_SECONDS = Histogram(
    "chatpref_pipeline_stage_latency_seconds",
    "Latencia por estagio do pipeline transacional por tenant.",
    labelnames=("tenant_id", "stage_name", "channel", "status"),
    registry=REGISTRY,
)

PIPELINE_ESTIMATED_COST_USD_TOTAL = Counter(
    "chatpref_pipeline_estimated_cost_usd_total",
    "Custo operacional estimado acumulado por tenant e estagio do pipeline.",
    labelnames=("tenant_id", "stage_name", "channel", "status", "llm_provider", "llm_model"),
    registry=REGISTRY,
)


def record_chat_request(*, channel: str) -> None:
    CHAT_REQUESTS_TOTAL.labels(channel=channel or "unknown").inc()


def record_policy_decision(
    *,
    stage: str,
    decision: str,
    reason_codes: list[str],
    channel: str,
) -> None:
    normalized_reason_codes = reason_codes or [""]
    for reason_code in normalized_reason_codes:
        POLICY_DECISIONS_TOTAL.labels(
            stage=stage or "unknown",
            decision=decision or "unknown",
            reason_code=reason_code,
            channel=channel or "unknown",
        ).inc()


def record_retrieval(*, status: str, channel: str) -> None:
    RETRIEVAL_TOTAL.labels(status=status or "unknown", channel=channel or "unknown").inc()


def record_llm_composition(
    *,
    provider: str,
    mode: str,
    channel: str,
    latency_seconds: float,
) -> None:
    labels = {
        "provider": provider or "unknown",
        "mode": mode or "unknown",
        "channel": channel or "unknown",
    }
    LLM_COMPOSITIONS_TOTAL.labels(**labels).inc()
    LLM_COMPOSE_LATENCY_SECONDS.labels(**labels).observe(max(latency_seconds, 0.0))


def record_pipeline_stage_latency(
    *,
    tenant_id: str,
    stage_name: str | PipelineStageName,
    channel: str,
    status: str,
    latency_seconds: float,
) -> None:
    """Registra a latencia de um estagio do pipeline com labels de baixa cardinalidade."""

    resolved_stage_name = stage_name.value if isinstance(stage_name, PipelineStageName) else stage_name
    PIPELINE_STAGE_LATENCY_SECONDS.labels(
        tenant_id=tenant_id or "unknown",
        stage_name=resolved_stage_name or "unknown",
        channel=channel or "unknown",
        status=status or "unknown",
    ).observe(max(latency_seconds, 0.0))


def record_pipeline_estimated_cost(
    *,
    tenant_id: str,
    stage_name: str | PipelineStageName,
    channel: str,
    status: str,
    estimated_cost_usd: float,
    llm_provider: str = "",
    llm_model: str = "",
) -> None:
    """Registra custo operacional estimado por tenant e estagio sem labels de alta cardinalidade."""

    resolved_stage_name = stage_name.value if isinstance(stage_name, PipelineStageName) else stage_name
    PIPELINE_ESTIMATED_COST_USD_TOTAL.labels(
        tenant_id=tenant_id or "unknown",
        stage_name=resolved_stage_name or "unknown",
        channel=channel or "unknown",
        status=status or "unknown",
        llm_provider=llm_provider or "unknown",
        llm_model=llm_model or "unknown",
    ).inc(max(estimated_cost_usd, 0.0))


@contextmanager
def track_pipeline_stage_latency(
    *,
    tenant_id: str,
    stage_name: str | PipelineStageName,
    channel: str,
    default_status: str = "ok",
    error_status: str = "error",
) -> Iterator[Callable[[str], None]]:
    """Mede latencia por estagio e permite ajustar o status final do ponto instrumentado."""

    started_at = perf_counter()
    status = default_status

    def set_status(next_status: str) -> None:
        nonlocal status
        normalized = str(next_status).strip()
        if normalized:
            status = normalized

    try:
        yield set_status
    except Exception:
        status = error_status
        raise
    finally:
        latency_seconds = perf_counter() - started_at
        record_pipeline_stage_latency(
            tenant_id=tenant_id,
            stage_name=stage_name,
            channel=channel,
            status=status,
            latency_seconds=latency_seconds,
        )


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST

