"""Reranking controlado aplicado apos a recuperacao inicial."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence
from typing import TYPE_CHECKING

from app.rag.retrieval_scoring import compute_lexical_overlap_score, tokenize_retrieval_text

if TYPE_CHECKING:
    from app.storage.chroma_repository import RetrievedChunk

NO_RERANK_STRATEGY_NAME = "no_rerank_v1"
HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME = "heuristic_post_retrieval_rerank_v1"


@dataclass(frozen=True, slots=True)
class RerankScoreWeights:
    """Representa os pesos ativos do reranking heuristico."""

    retrieval_score: float
    title_overlap: float
    tag_overlap: float
    text_density: float

    def __post_init__(self) -> None:
        """Valida os pesos declarados para evitar configuracao silenciosa invalida."""

        weights = (
            self.retrieval_score,
            self.title_overlap,
            self.tag_overlap,
            self.text_density,
        )
        if any(weight < 0 for weight in weights):
            raise ValueError("Os pesos do reranking nao podem ser negativos.")
        if all(weight == 0 for weight in weights):
            raise ValueError("Ao menos um peso do reranking deve ser maior que zero.")


@dataclass(frozen=True, slots=True)
class RerankingConfig:
    """Representa os parametros ativos da etapa de reranking."""

    max_candidates: int
    score_weights: RerankScoreWeights

    def __post_init__(self) -> None:
        """Valida os parametros minimos da etapa de reranking."""

        if self.max_candidates < 1:
            raise ValueError("max_candidates do reranking deve ser maior ou igual a 1.")


@dataclass(frozen=True, slots=True)
class RerankingResult:
    """Representa o resultado tecnico da etapa de reranking."""

    strategy_name: str
    applied: bool
    input_query: str
    reranked_candidates: int
    total_candidates: int
    max_candidates: int
    score_weights: RerankScoreWeights


def build_identity_reranking(
    *,
    query_text: str,
    strategy_name: str,
    total_candidates: int,
    config: RerankingConfig,
) -> RerankingResult:
    """Retorna um resultado sem alteracao da ordem recuperada."""

    return RerankingResult(
        strategy_name=strategy_name,
        applied=False,
        input_query=query_text,
        reranked_candidates=0,
        total_candidates=total_candidates,
        max_candidates=config.max_candidates,
        score_weights=config.score_weights,
    )


class RerankingService:
    """Aplica reranking heuristico de forma opt-in e rastreavel."""

    def rerank_chunks(
        self,
        *,
        query_text: str,
        chunks: Sequence[RetrievedChunk],
        strategy_name: str,
        config: RerankingConfig,
    ) -> tuple[list[RetrievedChunk], RerankingResult]:
        """Reranqueia os candidatos recuperados sem alterar o eixo de retrieval base."""

        total_candidates = len(chunks)
        if strategy_name == NO_RERANK_STRATEGY_NAME:
            return list(chunks), build_identity_reranking(
                query_text=query_text,
                strategy_name=strategy_name,
                total_candidates=total_candidates,
                config=config,
            )
        if strategy_name != HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME:
            raise ValueError(f"strategy_name de reranking nao suportada: {strategy_name}")

        query_tokens = tuple(dict.fromkeys(tokenize_retrieval_text(query_text)))
        if not query_tokens or not chunks:
            return list(chunks), build_identity_reranking(
                query_text=query_text,
                strategy_name=strategy_name,
                total_candidates=total_candidates,
                config=config,
            )

        reranked_candidates = min(total_candidates, config.max_candidates)
        candidates_to_rerank = list(chunks[:reranked_candidates])
        remaining_candidates = list(chunks[reranked_candidates:])

        reranked_chunks = [
            self._rerank_chunk(
                query_tokens=query_tokens,
                chunk=chunk,
                weights=config.score_weights,
            )
            for chunk in candidates_to_rerank
        ]
        reranked_chunks.sort(
            key=lambda item: (
                -item.score,
                -(item.rerank_score or 0.0),
                -(item.retrieval_score or 0.0),
                item.title,
                item.chunk_id,
            )
        )

        return reranked_chunks + remaining_candidates, RerankingResult(
            strategy_name=strategy_name,
            applied=True,
            input_query=query_text,
            reranked_candidates=reranked_candidates,
            total_candidates=total_candidates,
            max_candidates=config.max_candidates,
            score_weights=config.score_weights,
        )

    def _rerank_chunk(
        self,
        *,
        query_tokens: Sequence[str],
        chunk: RetrievedChunk,
        weights: RerankScoreWeights,
    ) -> RetrievedChunk:
        """Calcula o score final do reranking para um chunk recuperado."""

        retrieval_score = chunk.retrieval_score if chunk.retrieval_score is not None else chunk.score
        rerank_signal = self._compute_rerank_signal(
            query_tokens=query_tokens,
            chunk=chunk,
            weights=weights,
        )
        final_score = round(
            min(1.0, (retrieval_score * weights.retrieval_score) + rerank_signal),
            4,
        )
        return replace(
            chunk,
            score=final_score,
            retrieval_score=retrieval_score,
            rerank_score=rerank_signal,
        )

    def _compute_rerank_signal(
        self,
        *,
        query_tokens: Sequence[str],
        chunk: RetrievedChunk,
        weights: RerankScoreWeights,
    ) -> float:
        """Calcula o sinal heuristico adicional do reranking pos-recuperacao."""

        title_overlap = compute_lexical_overlap_score(
            query_tokens=query_tokens,
            text=chunk.title,
        )
        tag_overlap = compute_lexical_overlap_score(
            query_tokens=query_tokens,
            text=" ".join(chunk.tags),
        )
        text_density = self._compute_text_density_score(
            query_tokens=query_tokens,
            text=chunk.text,
        )
        return round(
            (title_overlap * weights.title_overlap)
            + (tag_overlap * weights.tag_overlap)
            + (text_density * weights.text_density),
            4,
        )

    def _compute_text_density_score(
        self,
        *,
        query_tokens: Sequence[str],
        text: str,
    ) -> float:
        """Calcula densidade de match lexical para o reranking heuristico."""

        content_tokens = tokenize_retrieval_text(text)
        if not content_tokens:
            return 0.0
        unique_query_tokens = {token for token in query_tokens if token}
        if not unique_query_tokens:
            return 0.0
        overlap_count = len(unique_query_tokens.intersection(content_tokens))
        return overlap_count / len(content_tokens)
