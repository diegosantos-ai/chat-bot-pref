"""
Embedding providers for Pilot Atendimento RAG.

All external providers (gemini, openai, qwen) use OpenRouter embeddings API.
"""

from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Iterator, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ChromaDB-compatible aliases
Documents = List[str]
Embeddings = List[List[float]]

_OPENROUTER_API_URL = "https://openrouter.ai/api/v1/embeddings"
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""

    DEFAULT = "default"  # ChromaDB built-in (all-MiniLM-L6-v2)
    GEMINI = "gemini"  # Google Gemini Embedding via OpenRouter
    OPENAI = "openai"  # OpenAI text-embedding-3-large via OpenRouter
    QWEN = "qwen"  # Qwen3 via OpenRouter


# OpenRouter default model IDs for external providers.
DEFAULT_MODELS = {
    EmbeddingProvider.GEMINI: "google/gemini-embedding-001",
    EmbeddingProvider.OPENAI: "openai/text-embedding-3-large",
    EmbeddingProvider.QWEN: "qwen/qwen3-embedding-8b",
}

# Per-provider collection suffix to isolate incompatible embedding spaces.
COLLECTION_SUFFIX = {
    EmbeddingProvider.DEFAULT: "",
    EmbeddingProvider.GEMINI: "_gemini",
    EmbeddingProvider.OPENAI: "_openai",
    EmbeddingProvider.QWEN: "_qwen",
}


def _parse_provider(provider: str) -> EmbeddingProvider:
    """Parse provider string with safe fallback to default."""
    try:
        return EmbeddingProvider(provider)
    except ValueError:
        logger.warning(
            "Unknown embedding provider '%s'. Falling back to 'default'.",
            provider,
        )
        return EmbeddingProvider.DEFAULT


def _iter_batches(items: Documents, batch_size: int) -> Iterator[Documents]:
    """Yield batched slices while preserving item order."""
    if not items:
        return
    for i in range(0, len(items), max(1, batch_size)):
        yield items[i : i + max(1, batch_size)]


def resolve_embedding_model(
    provider: str | EmbeddingProvider,
    explicit_model: Optional[str] = None,
) -> str:
    """
    Resolve the effective model for an embedding provider.

    Priority:
    1. explicit_model argument
    2. EMBEDDING_MODEL_OVERRIDE
    3. EMBEDDING_MODEL_<PROVIDER>
    4. hardcoded DEFAULT_MODELS
    """
    prov = provider if isinstance(provider, EmbeddingProvider) else _parse_provider(provider)
    if prov == EmbeddingProvider.DEFAULT:
        return ""

    from app.settings import settings as _settings

    if explicit_model:
        return explicit_model

    if _settings.EMBEDDING_MODEL_OVERRIDE:
        return _settings.EMBEDDING_MODEL_OVERRIDE

    provider_overrides = {
        EmbeddingProvider.GEMINI: _settings.EMBEDDING_MODEL_GEMINI,
        EmbeddingProvider.OPENAI: _settings.EMBEDDING_MODEL_OPENAI,
        EmbeddingProvider.QWEN: _settings.EMBEDDING_MODEL_QWEN,
    }
    return provider_overrides.get(prov) or DEFAULT_MODELS[prov]


class OpenRouterEmbeddingFunction:
    """Embedding function backed by OpenRouter API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float = 60.0,
        max_retries: int = 3,
        batch_size: int = 32,
    ):
        if not api_key:
            raise ValueError(
                f"OPENROUTER_API_KEY is required for external embedding provider (model: {model})"
            )

        self._api_key = api_key
        self.model = model
        self._timeout_seconds = timeout_seconds if timeout_seconds > 0 else 60.0
        self._max_retries = max(1, max_retries)
        self._batch_size = max(1, batch_size)

    def name(self) -> str:
        """Compatibility hook expected by newer Chroma versions."""
        return "openrouter"

    def is_legacy(self) -> bool:
        """Marks this implementation as a legacy embedding function for Chroma."""
        return True

    def embed_documents(self, input: Documents) -> Embeddings:
        """Compatibility helper used by some Chroma code paths."""
        return self.__call__(input=input)

    def embed_query(self, input: str | Documents) -> Embeddings:
        """Compatibility helper used by query embedding flow in Chroma."""
        if isinstance(input, str):
            return self.__call__(input=[input])
        return self.__call__(input=input)

    def _request_embeddings(self, batch: Documents) -> Embeddings:
        """Request embeddings for a single batch with retry/backoff."""
        for attempt in range(1, self._max_retries + 1):
            try:
                response = httpx.post(
                    _OPENROUTER_API_URL,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"model": self.model, "input": batch},
                    timeout=self._timeout_seconds,
                )
                response.raise_for_status()

                payload = response.json()
                items = sorted(payload.get("data", []), key=lambda x: x["index"])
                embeddings = [item["embedding"] for item in items]
                if len(embeddings) != len(batch):
                    raise ValueError(
                        "OpenRouter returned inconsistent embedding count "
                        f"(expected={len(batch)}, received={len(embeddings)})"
                    )
                return embeddings

            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code if exc.response else 0
                is_retryable = status_code in _RETRYABLE_STATUS_CODES
                if attempt >= self._max_retries or not is_retryable:
                    raise

                backoff_seconds = min(5.0, 0.5 * (2 ** (attempt - 1)))
                logger.warning(
                    "OpenRouter embeddings failed with status %s (attempt %s/%s). "
                    "Retrying in %.1fs.",
                    status_code,
                    attempt,
                    self._max_retries,
                    backoff_seconds,
                )
                time.sleep(backoff_seconds)

            except (httpx.HTTPError, ValueError):
                if attempt >= self._max_retries:
                    raise

                backoff_seconds = min(5.0, 0.5 * (2 ** (attempt - 1)))
                logger.warning(
                    "OpenRouter embeddings request error (attempt %s/%s). Retrying in %.1fs.",
                    attempt,
                    self._max_retries,
                    backoff_seconds,
                )
                time.sleep(backoff_seconds)

        return []

    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []

        embeddings: Embeddings = []
        for batch in _iter_batches(input, self._batch_size):
            embeddings.extend(self._request_embeddings(batch))
        return embeddings


def get_embedding_function(
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
):
    """
    Factory for embedding functions.

    External providers use OpenRouter and return OpenRouterEmbeddingFunction.
    The default provider returns None so ChromaDB uses its built-in embeddings.
    """
    prov = _parse_provider(provider)
    if prov == EmbeddingProvider.DEFAULT:
        return None

    from app.settings import settings as _settings

    key = api_key or _settings.OPENROUTER_API_KEY
    resolved_model = resolve_embedding_model(prov, explicit_model=model)
    return OpenRouterEmbeddingFunction(
        api_key=key,
        model=resolved_model,
        timeout_seconds=_settings.EMBEDDING_REQUEST_TIMEOUT_SECONDS,
        max_retries=_settings.EMBEDDING_MAX_RETRIES,
        batch_size=_settings.EMBEDDING_BATCH_SIZE,
    )


def get_collection_name(base_name: str, provider: str) -> str:
    """
    Return ChromaDB collection name for the given provider.

    Each provider uses a distinct collection suffix because vector spaces differ.
    """
    prov = _parse_provider(provider)
    return f"{base_name}{COLLECTION_SUFFIX[prov]}"
