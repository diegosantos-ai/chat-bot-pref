import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction

from app.llmops import ActiveArtifactResolver
from app.rag.retrieval_scoring import (
    build_candidate_pool_size,
    compute_weighted_retrieval_score,
    tokenize_retrieval_text,
)
from app.settings import settings


@dataclass(frozen=True)
class IngestChunk:
    chunk_id: str
    document_id: str
    title: str
    section: str
    source: str
    text: str
    tags: list[str]


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    title: str
    section: str
    source: str
    text: str
    tags: list[str]
    score: float


class HashEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self, dimensions: int = 32) -> None:
        self.dimensions = dimensions

    def __call__(self, input: Documents) -> list[list[float]]:
        return [self._embed(text) for text in input]

    @staticmethod
    def name() -> str:
        return settings.RAG_EMBEDDING_VERSION

    def get_config(self) -> dict[str, int]:
        return {"dimensions": self.dimensions}

    @staticmethod
    def build_from_config(config: dict[str, int]) -> "HashEmbeddingFunction":
        return HashEmbeddingFunction(dimensions=int(config.get("dimensions", 32)))

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = tokenize_retrieval_text(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:2], "big") % self.dimensions
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector

        return [round(value / norm, 8) for value in vector]


class TenantChromaRepository:
    def __init__(
        self,
        base_dir: str | Path | None = None,
        collection_prefix: str | None = None,
        legacy_prefixes: list[str] | None = None,
        artifact_resolver: ActiveArtifactResolver | None = None,
    ) -> None:
        self.artifact_resolver = artifact_resolver or ActiveArtifactResolver()
        self.base_dir = Path(base_dir or settings.CHROMA_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.collection_prefix = collection_prefix or settings.CHROMA_COLLECTION_PREFIX
        self.legacy_prefixes = legacy_prefixes or settings.CHROMA_LEGACY_COLLECTION_PREFIXES
        self.client = chromadb.PersistentClient(path=str(self.base_dir))
        self.embedding_function = HashEmbeddingFunction()

    def retriever_version(self) -> str:
        """Retorna a versão lógica da estratégia de retrieval usada no runtime atual."""

        return self.artifact_resolver.resolve_retrieval_config().version

    def embedding_version(self) -> str:
        """Retorna a versão lógica do embedding usado no runtime atual."""

        return self.artifact_resolver.retrieval_embedding_version() or self.embedding_function.name()

    def collection_name(self, tenant_id: str) -> str:
        normalized_tenant = self._normalize_tenant(tenant_id)
        return f"{self.collection_prefix}__{normalized_tenant}"

    def list_collection_names(self) -> list[str]:
        return [collection.name for collection in self.client.list_collections()]

    def collection_stats(self) -> list[tuple[str, int]]:
        stats: list[tuple[str, int]] = []
        for collection_name in self.list_collection_names():
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
            )
            stats.append((collection_name, collection.count()))
        return stats

    def count_chunks(self, tenant_id: str) -> int:
        collection = self._get_collection_if_exists(tenant_id)
        if collection is None:
            return 0
        return collection.count()

    def ingest_chunks(self, tenant_id: str, chunks: list[IngestChunk]) -> int:
        if not chunks:
            return 0
        collection = self._get_or_create_collection(tenant_id)
        collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "tenant_id": tenant_id,
                    "document_id": chunk.document_id,
                    "title": chunk.title,
                    "section": chunk.section,
                    "source": chunk.source,
                    "tags": "|".join(chunk.tags),
                }
                for chunk in chunks
            ],
        )
        return len(chunks)

    def query_chunks(
        self,
        tenant_id: str,
        query_text: str,
        limit: int,
        min_score: float,
    ) -> list[RetrievedChunk]:
        collection = self._get_collection_if_exists(tenant_id)
        if collection is None or collection.count() == 0:
            return []

        result = collection.query(
            query_texts=[query_text],
            n_results=build_candidate_pool_size(
                top_k=limit,
                multiplier=self.artifact_resolver.retrieval_candidate_pool_multiplier(),
            ),
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        query_tokens = tokenize_retrieval_text(query_text)
        score_weights = self.artifact_resolver.retrieval_score_weights()
        scored_results: list[RetrievedChunk] = []
        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            score = compute_weighted_retrieval_score(
                query_tokens=query_tokens,
                text=text,
                distance=distance,
                weights=score_weights,
            )
            if score < min_score:
                continue
            scored_results.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=str((metadata or {}).get("document_id", "")),
                    title=str((metadata or {}).get("title", "")),
                    section=str((metadata or {}).get("section", "")),
                    source=str((metadata or {}).get("source", "")),
                    text=text,
                    tags=self._split_tags(str((metadata or {}).get("tags", ""))),
                    score=score,
                )
            )

        scored_results.sort(key=lambda item: (-item.score, item.title, item.chunk_id))
        return scored_results[:limit]

    def reset_tenant_collection(self, tenant_id: str) -> list[str]:
        removed_collections: list[str] = []
        current_name = self.collection_name(tenant_id)
        if current_name in self.list_collection_names():
            self.client.delete_collection(current_name)
            removed_collections.append(current_name)
        return removed_collections

    def remove_legacy_collections(self, tenant_id: str | None = None) -> list[str]:
        normalized_tenant = self._normalize_tenant(tenant_id) if tenant_id is not None else None
        current_collection_name = (
            self.collection_name(tenant_id) if tenant_id is not None else None
        )
        removed_collections: list[str] = []
        for collection_name in self.list_collection_names():
            if current_collection_name is not None and collection_name == current_collection_name:
                continue
            if not any(collection_name.startswith(f"{prefix}__") for prefix in self.legacy_prefixes):
                continue
            if normalized_tenant is not None and not collection_name.endswith(f"__{normalized_tenant}"):
                continue
            self.client.delete_collection(collection_name)
            removed_collections.append(collection_name)
        return removed_collections

    def _get_collection_if_exists(self, tenant_id: str):
        collection_name = self.collection_name(tenant_id)
        if collection_name not in self.list_collection_names():
            return None
        return self.client.get_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
        )

    def _get_or_create_collection(self, tenant_id: str):
        return self.client.get_or_create_collection(
            name=self.collection_name(tenant_id),
            embedding_function=self.embedding_function,
        )

    def _normalize_tenant(self, tenant_id: str) -> str:
        normalized_tenant = re.sub(r"[^a-z0-9]+", "_", tenant_id.lower()).strip("_")
        if not normalized_tenant:
            raise ValueError("tenant_id inválido para collection")
        if len(normalized_tenant) < 3:
            normalized_tenant = f"tnt_{normalized_tenant}"
        return normalized_tenant

    def _split_tags(self, raw_tags: str) -> list[str]:
        if not raw_tags:
            return []
        return [tag for tag in raw_tags.split("|") if tag]
