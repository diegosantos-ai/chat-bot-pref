from app.llmops import ActiveArtifactResolver
from app.rag.reranking import (
    HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME,
    NO_RERANK_STRATEGY_NAME,
    RerankingService,
)
from app.storage.chroma_repository import RetrievedChunk


def _build_chunks() -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk_id="chunk-base",
            document_id="doc-1",
            title="Atendimento Geral",
            section="section-1",
            source="doc-1.json",
            text="Horario de atendimento em texto generico.",
            tags=["servico"],
            score=0.81,
            retrieval_score=0.81,
            rerank_score=None,
        ),
        RetrievedChunk(
            chunk_id="chunk-rerank",
            document_id="doc-2",
            title="Horario do Alvara",
            section="section-1",
            source="doc-2.json",
            text="Informacoes sobre o alvara e horario de atendimento.",
            tags=["alvara", "horario"],
            score=0.62,
            retrieval_score=0.62,
            rerank_score=None,
        ),
    ]


def test_reranking_disabled_preserves_original_order() -> None:
    service = RerankingService()
    resolver = ActiveArtifactResolver()

    reranked_chunks, result = service.rerank_chunks(
        query_text="horario alvara",
        chunks=_build_chunks(),
        strategy_name=NO_RERANK_STRATEGY_NAME,
        config=resolver.reranking_config(),
    )

    assert [chunk.title for chunk in reranked_chunks] == [
        "Atendimento Geral",
        "Horario do Alvara",
    ]
    assert result.strategy_name == NO_RERANK_STRATEGY_NAME
    assert result.applied is False
    assert result.reranked_candidates == 0


def test_heuristic_reranking_reorders_candidates_after_retrieval() -> None:
    service = RerankingService()
    resolver = ActiveArtifactResolver()

    reranked_chunks, result = service.rerank_chunks(
        query_text="horario alvara",
        chunks=_build_chunks(),
        strategy_name=HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME,
        config=resolver.reranking_config(),
    )

    assert [chunk.title for chunk in reranked_chunks] == [
        "Horario do Alvara",
        "Atendimento Geral",
    ]
    assert result.strategy_name == HEURISTIC_POST_RETRIEVAL_RERANK_STRATEGY_NAME
    assert result.applied is True
    assert result.reranked_candidates == 2
    assert reranked_chunks[0].retrieval_score == 0.62
    assert reranked_chunks[0].rerank_score is not None
