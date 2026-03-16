"""Metodologia minima de custo estimado operacional da Fase 6."""

from __future__ import annotations

from dataclasses import dataclass
import math

from app.settings import settings


@dataclass(frozen=True, slots=True)
class EstimatedOperationalCost:
    """Representa o resultado de custo operacional estimado por etapa."""

    estimated_cost_usd: float
    status: str
    method: str
    input_tokens_estimated: int = 0
    output_tokens_estimated: int = 0


def estimate_llm_operational_cost(
    *,
    provider: str,
    input_text: str,
    output_text: str,
) -> EstimatedOperationalCost:
    """Estima custo de LLM com heuristica explicita quando nao ha token real no runtime."""

    normalized_provider = (provider or "").strip().lower()
    if normalized_provider == "mock":
        return EstimatedOperationalCost(
            estimated_cost_usd=0.0,
            status="non_billed",
            method="mock_provider_non_billed_v1",
        )

    chars_per_token = max(settings.LLM_COST_ESTIMATION_CHARS_PER_TOKEN, 1)
    input_tokens = _estimate_tokens_from_text(input_text, chars_per_token)
    output_tokens = _estimate_tokens_from_text(output_text, chars_per_token)

    input_cost = (input_tokens / 1000.0) * settings.LLM_COST_ESTIMATION_INPUT_USD_PER_1K_TOKENS
    output_cost = (output_tokens / 1000.0) * settings.LLM_COST_ESTIMATION_OUTPUT_USD_PER_1K_TOKENS
    estimated_cost_usd = round(input_cost + output_cost, 8)

    return EstimatedOperationalCost(
        estimated_cost_usd=estimated_cost_usd,
        status="estimated",
        method="chars_per_token_heuristic_v1",
        input_tokens_estimated=input_tokens,
        output_tokens_estimated=output_tokens,
    )


def estimate_retrieval_operational_cost() -> EstimatedOperationalCost:
    """Retorna custo operacional do retrieval no runtime atual local (nao faturado por chamada)."""

    return EstimatedOperationalCost(
        estimated_cost_usd=0.0,
        status="non_billed",
        method="local_chroma_runtime_non_billed_v1",
    )


def _estimate_tokens_from_text(text: str, chars_per_token: int) -> int:
    normalized_text = (text or "").strip()
    if not normalized_text:
        return 0
    return max(math.ceil(len(normalized_text) / chars_per_token), 1)
