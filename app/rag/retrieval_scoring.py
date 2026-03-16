"""Helpers pequenos para scoring e corte do retrieval atual."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence

TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
BASELINE_RETRIEVAL_STRATEGY_NAME = "semantic_candidates_with_lexical_rescoring_v1"
HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME = (
    "semantic_plus_full_collection_lexical_candidates_v1"
)


@dataclass(frozen=True, slots=True)
class RetrievalScoreWeights:
    """Representa os pesos ativos do score combinado do retrieval."""

    lexical: float
    semantic: float

    def __post_init__(self) -> None:
        """Valida os pesos declarados para evitar configuracao silenciosa invalida."""

        if self.lexical < 0 or self.semantic < 0:
            raise ValueError("Os pesos de retrieval nao podem ser negativos.")
        if self.lexical == 0 and self.semantic == 0:
            raise ValueError("Ao menos um peso de retrieval deve ser maior que zero.")


def tokenize_retrieval_text(text: str) -> list[str]:
    """Tokeniza texto do retrieval de forma compativel com o embedding hash atual."""

    return TOKEN_PATTERN.findall(text.lower())


def build_candidate_pool_size(*, top_k: int, multiplier: int) -> int:
    """Calcula o tamanho do pool inicial de candidatos antes do corte final."""

    if top_k < 1:
        raise ValueError("top_k deve ser maior ou igual a 1.")
    if multiplier < 1:
        raise ValueError("candidate_pool_multiplier deve ser maior ou igual a 1.")
    return max(top_k * multiplier, top_k)


def compute_lexical_overlap_score(*, query_tokens: Sequence[str], text: str) -> float:
    """Calcula a sobreposicao lexical simples entre query e conteudo do chunk."""

    unique_query_tokens = {token for token in query_tokens if token}
    if not unique_query_tokens:
        return 0.0
    content_tokens = set(tokenize_retrieval_text(text))
    overlap = len(unique_query_tokens & content_tokens)
    return overlap / len(unique_query_tokens)


def compute_weighted_retrieval_score(
    *,
    query_tokens: Sequence[str],
    text: str,
    distance: float | None,
    weights: RetrievalScoreWeights,
) -> float:
    """Combina score lexical e score semantico do baseline atual."""

    unique_query_tokens = {token for token in query_tokens if token}
    if not unique_query_tokens:
        return 0.0

    lexical_score = compute_lexical_overlap_score(query_tokens=tuple(unique_query_tokens), text=text)
    semantic_score = 0.0 if distance is None else 1 / (1 + max(float(distance), 0.0))
    combined_score = (lexical_score * weights.lexical) + (semantic_score * weights.semantic)
    return round(min(1.0, combined_score), 4)
