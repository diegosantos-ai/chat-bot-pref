from app.llmops import ActiveArtifactResolver
from app.rag.retrieval_scoring import (
    BASELINE_RETRIEVAL_STRATEGY_NAME,
    HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
)
from app.storage.chroma_repository import TenantChromaRepository


class _FakeCollection:
    def count(self) -> int:
        return 2

    def query(self, *, query_embeddings, n_results):
        assert len(query_embeddings) == 1
        assert n_results >= 1
        return {
            "ids": [["chunk-sem"]],
            "documents": [["Texto sem relacao direta com o pedido."]],
            "metadatas": [[
                {
                    "document_id": "doc-sem",
                    "title": "Resultado Semantico",
                    "section": "section-1",
                    "source": "doc-sem.json",
                    "tags": "",
                }
            ]],
            "distances": [[0.05]],
        }

    def get(self, *, include):
        assert include == ["documents", "metadatas"]
        return {
            "ids": ["chunk-sem", "chunk-lex"],
            "documents": [
                "Texto sem relacao direta com o pedido.",
                "Horario do alvara funciona das 8h as 17h.",
            ],
            "metadatas": [
                {
                    "document_id": "doc-sem",
                    "title": "Resultado Semantico",
                    "section": "section-1",
                    "source": "doc-sem.json",
                    "tags": "",
                },
                {
                    "document_id": "doc-lex",
                    "title": "Resultado Lexical",
                    "section": "section-2",
                    "source": "doc-lex.json",
                    "tags": "",
                },
            ],
        }


def test_hybrid_strategy_adds_lexical_candidates_beyond_semantic_pool(tmp_path) -> None:
    repository = TenantChromaRepository(
        base_dir=tmp_path / "chroma",
        artifact_resolver=ActiveArtifactResolver(),
    )
    repository._get_collection_if_exists = lambda tenant_id: _FakeCollection()  # type: ignore[method-assign]

    baseline_chunks = repository.query_chunks(
        tenant_id="prefeitura-demo",
        query_text="horario alvara",
        limit=2,
        min_score=0.0,
        strategy_name=BASELINE_RETRIEVAL_STRATEGY_NAME,
    )
    hybrid_chunks = repository.query_chunks(
        tenant_id="prefeitura-demo",
        query_text="horario alvara",
        limit=2,
        min_score=0.0,
        strategy_name=HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
    )

    assert [chunk.title for chunk in baseline_chunks] == ["Resultado Semantico"]
    assert [chunk.title for chunk in hybrid_chunks] == [
        "Resultado Lexical",
        "Resultado Semantico",
    ]
