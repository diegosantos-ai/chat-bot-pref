import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction

from app.contracts.dto import ChatExchangeRecord
from app.settings import settings

TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


@dataclass(frozen=True)
class RetrievedContext:
    document_id: str
    content: str
    distance: float | None
    metadata: dict[str, str]
    token_overlap: int


class HashEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self, dimensions: int = 32) -> None:
        self.dimensions = dimensions

    def __call__(self, input: Documents) -> list[list[float]]:
        return [self._embed(text) for text in input]

    @staticmethod
    def name() -> str:
        return "hash-embedding-v1"

    def get_config(self) -> dict[str, int]:
        return {"dimensions": self.dimensions}

    @staticmethod
    def build_from_config(config: dict[str, int]) -> "HashEmbeddingFunction":
        return HashEmbeddingFunction(dimensions=int(config.get("dimensions", 32)))

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = _tokenize(text)
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
    ) -> None:
        self.base_dir = Path(base_dir or settings.CHROMA_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.collection_prefix = collection_prefix or settings.CHROMA_COLLECTION_PREFIX
        self.client = chromadb.PersistentClient(path=str(self.base_dir))
        self.embedding_function = HashEmbeddingFunction()

    def collection_name(self, tenant_id: str) -> str:
        normalized_tenant = re.sub(r"[^a-z0-9]+", "_", tenant_id.lower()).strip("_")
        if not normalized_tenant:
            raise ValueError("tenant_id inválido para collection")
        return f"{self.collection_prefix}__{normalized_tenant}"

    def upsert_exchange(self, record: ChatExchangeRecord) -> str:
        collection = self._get_collection(record.tenant_id)
        document_id = f"{record.session_id}:{record.request_id}"
        collection.upsert(
            ids=[document_id],
            documents=[record.user_message],
            metadatas=[
                {
                    "tenant_id": record.tenant_id,
                    "session_id": record.session_id,
                    "request_id": record.request_id,
                    "channel": record.channel,
                }
            ],
        )
        return document_id

    def query_context(
        self,
        tenant_id: str,
        query_text: str,
        limit: int = 1,
    ) -> list[RetrievedContext]:
        collection = self._get_collection(tenant_id)
        if collection.count() == 0:
            return []

        result = collection.query(
            query_texts=[query_text],
            n_results=max(limit * 3, limit),
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        contexts: list[RetrievedContext] = []
        for document_id, content, metadata, distance in zip(ids, documents, metadatas, distances):
            token_overlap = self._token_overlap(query_text, content)
            if token_overlap == 0:
                continue
            contexts.append(
                RetrievedContext(
                    document_id=document_id,
                    content=content,
                    distance=distance,
                    metadata={key: str(value) for key, value in (metadata or {}).items()},
                    token_overlap=token_overlap,
                )
            )

        contexts.sort(
            key=lambda item: (
                -item.token_overlap,
                item.distance if item.distance is not None else float("inf"),
                item.document_id,
            )
        )
        return contexts[:limit]

    def _get_collection(self, tenant_id: str):
        return self.client.get_or_create_collection(
            name=self.collection_name(tenant_id),
            embedding_function=self.embedding_function,
        )

    def _token_overlap(self, query_text: str, content: str) -> int:
        query_tokens = set(_tokenize(query_text))
        content_tokens = set(_tokenize(content))
        return len(query_tokens & content_tokens)
