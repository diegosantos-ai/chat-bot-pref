from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, generate_latest


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


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST

