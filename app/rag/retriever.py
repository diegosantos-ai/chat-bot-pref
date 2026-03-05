"""
RAG Retriever - Busca trechos relevantes por similaridade semantica.

Responsabilidades:
- Receber a query do usuario
- Buscar chunks mais relevantes no ChromaDB
- Aplicar filtros e reranking se necessario
- Retornar contexto estruturado para o composer
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import chromadb

from app.rag.ingest import get_chroma_client, ingest_base
from app.rag.boosts import get_total_boost
from app.rag.acronyms import extract_acronyms_from_query
from app.rag.embeddings import (
    get_embedding_function,
    get_collection_name,
    resolve_embedding_model,
)
from app.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """Representa um chunk recuperado do RAG."""

    id: str
    text: str
    source: str
    title: str
    section: str
    score: float  # 0-1, maior = mais relevante
    tags: list[str]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source,
            "title": self.title,
            "section": self.section,
            "score": self.score,
            "tags": self.tags,
        }


@dataclass
class RetrievalResult:
    """Resultado completo de uma busca RAG."""

    query: str
    chunks: list[RetrievedChunk]
    collection_name: str
    total_chunks_searched: int

    @property
    def has_results(self) -> bool:
        return len(self.chunks) > 0

    @property
    def best_score(self) -> float:
        if not self.chunks:
            return 0.0
        return max(c.score for c in self.chunks)

    @property
    def context_text(self) -> str:
        """Retorna texto concatenado dos chunks para usar como contexto."""
        if not self.chunks:
            return ""

        parts = []
        for chunk in self.chunks:
            header = f"[Fonte: {chunk.title}"
            if chunk.section:
                header += f" > {chunk.section}"
            header += "]"
            parts.append(f"{header}\n{chunk.text}")

        return "\n\n---\n\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "chunks": [c.to_dict() for c in self.chunks],
            "collection_name": self.collection_name,
            "total_chunks_searched": self.total_chunks_searched,
            "has_results": self.has_results,
            "best_score": self.best_score,
        }


class RAGRetriever:
    """
    Recuperador de contexto RAG usando ChromaDB.

    Estrategia de busca:
    1. Busca semantica por embedding similarity
    2. Filtra por score minimo
    3. Limita quantidade de chunks
    4. Ordena por relevancia
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,
        top_k: int = 5,
        min_score: float = 0.3,
        embedding_provider: Optional[str] = None,
    ):
        """
        Args:
            collection_name: Nome da collection ChromaDB (usa padrao se None)
            top_k: Numero maximo de chunks a retornar
            min_score: Score minimo para incluir chunk (0-1)
            embedding_provider: Provedor de embedding ("default", "gemini", "openai", "qwen")
        """
        self._embedding_provider = embedding_provider or settings.EMBEDDING_PROVIDER
        self._embedding_model = resolve_embedding_model(self._embedding_provider)
        base_name = collection_name or settings.RAG_COLLECTION_NAME
        self.collection_name = get_collection_name(base_name, self._embedding_provider)
        self.top_k = top_k
        self.min_score = min_score
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection: Optional[chromadb.Collection] = None

    def _resolve_base_path(self) -> Path:
        """
        Resolve local knowledge base path for auto-ingest.

        Tries current path layout first, then legacy layout.
        """
        candidates = [
            Path(settings.BASE_DIR) / "data" / "knowledge_base" / settings.RAG_BASE_ID,
            Path(settings.BASE_DIR) / "base" / settings.RAG_BASE_ID,  # legacy
        ]
        for path in candidates:
            if path.exists():
                return path
        return candidates[0]

    def _ensure_collection(self) -> chromadb.Collection:
        """Obtem ou cria conexao com a collection, ingerindo a base se faltar."""
        if self._collection is None:
            self._client = get_chroma_client()
            embedding_fn = get_embedding_function(self._embedding_provider)
            get_kwargs = {"name": self.collection_name}
            if embedding_fn is not None:
                get_kwargs["embedding_function"] = embedding_fn
            try:
                self._collection = self._client.get_collection(**get_kwargs)
            except Exception as exc:
                msg = str(exc).lower()
                if "does not exist" not in msg:
                    raise
                base_path = self._resolve_base_path()
                if not base_path.exists():
                    raise FileNotFoundError(
                        "Base de conhecimento nao encontrada para auto-ingest: "
                        f"{base_path}"
                    )
                logger.warning(
                    "Chroma collection %s ausente. Ingerindo base padrao em %s "
                    "(provider=%s, model=%s).",
                    self.collection_name,
                    base_path,
                    self._embedding_provider,
                    self._embedding_model or "chromadb-default",
                )
                ingest_base(base_path, embedding_provider=self._embedding_provider)
                self._collection = self._client.get_collection(**get_kwargs)
        return self._collection

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        filter_tags: Optional[list[str]] = None,
    ) -> RetrievalResult:
        """
        Busca chunks relevantes para a query.

        Args:
            query: Pergunta/texto do usuario
            top_k: Override do numero maximo de resultados
            min_score: Override do score minimo
            filter_tags: Filtrar apenas chunks com essas tags

        Returns:
            RetrievalResult com chunks encontrados
        """
        top_k = top_k if top_k is not None else self.top_k
        min_score = min_score if min_score is not None else self.min_score

        collection = self._ensure_collection()

        # Monta filtro de tags se especificado
        where_filter = None
        if filter_tags:
            where_filter = {
                "$or": [{"tags": {"$contains": tag}} for tag in filter_tags]
            }

        results = collection.query(
            query_texts=[query],
            n_results=top_k * 2,  # Busca mais para filtrar por score depois
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        chunks: list[RetrievedChunk] = []

        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i]
                score = 1 - distance  # Para cosine distance

                metadata = results["metadatas"][0][i]
                tags_str = metadata.get("tags", "")
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]

                chunk_text = results["documents"][0][i]

                # Aplica boost configurável (siglas, palavras-chave, categorias)
                boost = await get_total_boost(query, chunk_text, tags)
                if boost > 0:
                    original_score = score
                    score = min(1.0, score + boost)  # Limita em 1.0
                    logger.debug(
                        f"Boost aplicado em {chunk_id}: {original_score:.3f} -> {score:.3f}"
                    )

                # Filtra por score minimo APOS aplicar boost
                if score < min_score:
                    continue

                chunk = RetrievedChunk(
                    id=chunk_id,
                    text=chunk_text,
                    source=metadata.get("source", ""),
                    title=metadata.get("title", ""),
                    section=metadata.get("section", ""),
                    score=score,
                    tags=tags,
                )
                chunks.append(chunk)

        chunks.sort(key=lambda c: c.score, reverse=True)

        # BUSCA HÍBRIDA: Executa busca por siglas mesmo quando a semântica retorna vazio
        # ou quando nenhum chunk tem match de boost
        query_acronyms = extract_acronyms_from_query(query)

        if query_acronyms:
            # Verifica se há match de boost em algum chunk (loop async compatível)
            has_boost_match = False
            for chunk in chunks:
                boost = await get_total_boost(query, chunk.text, chunk.tags)
                if boost > 0:
                    has_boost_match = True
                    break

            # Busca por siglas se: (1) sem resultados semânticos, ou (2) sem match de boost
            if not chunks or not has_boost_match:
                logger.debug(
                    f"Buscando chunks por siglas: {query_acronyms} "
                    f"(chunks_semantic={len(chunks)}, has_boost_match={has_boost_match})"
                )

                # Busca chunks que contenham a sigla usando busca por texto
                acronym_chunks = self._retrieve_by_acronyms(
                    collection, query_acronyms, top_k=5
                )

                # Adiciona chunks encontrados (evitando duplicatas)
                existing_ids = {chunk.id for chunk in chunks}
                for ac_chunk in acronym_chunks:
                    if ac_chunk.id not in existing_ids:
                        # Aplica boost nas chunks de sigla
                        ac_chunk.score = min(1.0, ac_chunk.score + 0.2)
                        chunks.append(ac_chunk)
                        logger.debug(
                            f"Chunk adicionado por busca de siglas: {ac_chunk.id}"
                        )

        # Reordena após possível adição de chunks
        chunks.sort(key=lambda c: c.score, reverse=True)
        chunks = chunks[:top_k]

        return RetrievalResult(
            query=query,
            chunks=chunks,
            collection_name=self.collection_name,
            total_chunks_searched=collection.count(),
        )

    def _retrieve_by_acronyms(
        self, collection: chromadb.Collection, acronyms: list[str], top_k: int = 5
    ) -> list[RetrievedChunk]:
        """
        Busca chunks que contenham as siglas especificadas.

        Args:
            collection: Coleção ChromaDB
            acronyms: Lista de siglas a buscar
            top_k: Número máximo de chunks a retornar

        Returns:
            Lista de chunks contendo as siglas
        """
        chunks: list[RetrievedChunk] = []

        try:
            # Busca todos os chunks e filtra manualmente
            # Nota: ChromaDB não suporta busca por texto diretamente,
            # então buscamos mais resultados e filtramos
            all_results = collection.get(
                include=["documents", "metadatas"],
                limit=100,  # Busca um número razoável de chunks
            )

            if all_results["ids"]:
                for i, chunk_id in enumerate(all_results["ids"]):
                    chunk_text = all_results["documents"][i]
                    metadata = all_results["metadatas"][i]

                    # Verifica se o chunk contém alguma das siglas
                    chunk_upper = chunk_text.upper()
                    for acronym in acronyms:
                        if acronym.upper() in chunk_upper:
                            # Verifica se é palavra completa
                            idx = chunk_upper.find(acronym.upper())
                            if idx != -1:
                                before = idx == 0 or not chunk_upper[idx - 1].isalnum()
                                after = (
                                    idx + len(acronym) >= len(chunk_upper)
                                    or not chunk_upper[idx + len(acronym)].isalnum()
                                )

                                if before and after:
                                    tags_str = metadata.get("tags", "")
                                    tags = [
                                        t.strip()
                                        for t in tags_str.split(",")
                                        if t.strip()
                                    ]

                                    chunk = RetrievedChunk(
                                        id=chunk_id,
                                        text=chunk_text,
                                        source=metadata.get("source", ""),
                                        title=metadata.get("title", ""),
                                        section=metadata.get("section", ""),
                                        score=0.7,  # Score base alto para chunks de sigla
                                        tags=tags,
                                    )
                                    chunks.append(chunk)
                                    break  # Evita adicionar o mesmo chunk múltiplas vezes
        except Exception as e:
            logger.warning(f"Erro ao buscar chunks por siglas: {e}")

        return chunks[:top_k]

    def retrieve_by_tags(
        self,
        tags: list[str],
        top_k: Optional[int] = None,
    ) -> RetrievalResult:
        """
        Busca chunks por tags especificas (sem query semantica).
        """
        top_k = top_k or self.top_k
        collection = self._ensure_collection()

        where_filter = {"$or": [{"tags": {"$contains": tag}} for tag in tags]}

        results = collection.get(
            where=where_filter,
            include=["documents", "metadatas"],
            limit=top_k,
        )

        chunks: list[RetrievedChunk] = []
        if results["ids"]:
            for i, chunk_id in enumerate(results["ids"]):
                metadata = results["metadatas"][i]
                tags_str = metadata.get("tags", "")
                chunk_tags = [t.strip() for t in tags_str.split(",") if t.strip()]

                chunk = RetrievedChunk(
                    id=chunk_id,
                    text=results["documents"][i],
                    source=metadata.get("source", ""),
                    title=metadata.get("title", ""),
                    section=metadata.get("section", ""),
                    score=1.0,  # Score fixo para busca por tag
                    tags=chunk_tags,
                )
                chunks.append(chunk)

        return RetrievalResult(
            query=f"tags:{','.join(tags)}",
            chunks=chunks,
            collection_name=self.collection_name,
            total_chunks_searched=collection.count(),
        )


_default_retriever: Optional[RAGRetriever] = None


def get_retriever() -> RAGRetriever:
    """Retorna instancia padrao do retriever."""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = RAGRetriever()
    return _default_retriever


async def retrieve(query: str, **kwargs) -> RetrievalResult:
    """Atalho para busca rapida."""
    return await get_retriever().retrieve(query, **kwargs)


if __name__ == "__main__":
    import sys
    import asyncio

    if len(sys.argv) < 2:
        print("Uso: python -m app.rag.retriever '<query>'")
        print("Exemplo: python -m app.rag.retriever 'qual o horario de funcionamento?'")
        sys.exit(1)

    query = sys.argv[1]

    print(f"\n>> Buscando: '{query}'")
    print("-" * 50)

    result = asyncio.run(retrieve(query))

    print(f">> Resultados: {len(result.chunks)} chunks encontrados")
    print(f"   Collection: {result.collection_name}")
    print(f"   Total pesquisado: {result.total_chunks_searched}")
    print(f"   Melhor score: {result.best_score:.3f}")
    print()

    for i, chunk in enumerate(result.chunks, 1):
        print(f"--- Chunk {i} (score: {chunk.score:.3f}) ---")
        print(f"Fonte: {chunk.title} > {chunk.section}")
        print(f"Tags: {chunk.tags}")
        print(f"Texto:\n{chunk.text[:300]}...")
        print()
