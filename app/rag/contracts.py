"""Contratos mínimos da Fase 1 para versionamento e instrumentação do RAG."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.settings import settings


@dataclass(frozen=True, slots=True)
class RagArtifactVersions:
    """Agrupa as versões mínimas de retrieval e embeddings exigidas pela Fase 1."""

    retriever_version: str
    embedding_version: str

    def __post_init__(self) -> None:
        """Garante que o versionamento mínimo do RAG permaneça explícito."""

        if not self.retriever_version.strip():
            raise ValueError("retriever_version obrigatório para a Fase 1.")
        if not self.embedding_version.strip():
            raise ValueError("embedding_version obrigatório para a Fase 1.")

    def as_params(self) -> dict[str, str]:
        """Retorna as versões do RAG no formato esperado pelo tracking experimental."""

        return {
            "retriever_version": self.retriever_version,
            "embedding_version": self.embedding_version,
        }


@dataclass(frozen=True, slots=True)
class RagInstrumentationPoint:
    """Descreve um ponto mínimo de instrumentação do fluxo RAG para a Fase 1."""

    name: str
    source_path: str
    purpose: str
    required_fields: tuple[str, ...]


PHASE1_RAG_ARTIFACT_VERSIONS: Final[RagArtifactVersions] = RagArtifactVersions(
    retriever_version=settings.RAG_RETRIEVER_VERSION,
    embedding_version=settings.RAG_EMBEDDING_VERSION,
)

PHASE1_RAG_INSTRUMENTATION_POINTS: Final[tuple[RagInstrumentationPoint, ...]] = (
    RagInstrumentationPoint(
        name="tenant_collection_resolution",
        source_path="app/storage/chroma_repository.py:collection_name",
        purpose="Resolver collection isolável por tenant antes de ingestão ou query.",
        required_fields=("tenant_id", "collection_name", "retriever_version"),
    ),
    RagInstrumentationPoint(
        name="retrieval_query_execution",
        source_path="app/services/rag_service.py:query",
        purpose="Mapear o contexto mínimo da query RAG usada em experimentação offline.",
        required_fields=("tenant_id", "query", "top_k", "min_score", "retriever_version", "embedding_version"),
    ),
    RagInstrumentationPoint(
        name="retrieval_result_summary",
        source_path="app/storage/chroma_repository.py:query_chunks",
        purpose="Registrar o resumo técnico dos resultados e scores sem confundir com auditoria operacional.",
        required_fields=("tenant_id", "limit", "score", "document_id", "embedding_version"),
    ),
)
