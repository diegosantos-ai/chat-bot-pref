from datetime import datetime, timezone
import re

from app.contracts.dto import (
    RagDocumentContent,
    RagDocumentCreateRequest,
    RagDocumentListResponse,
    RagDocumentRecord,
    RagDocumentSummary,
    RagDocumentUpdateRequest,
    RagIngestRequest,
    RagIngestResponse,
    RagQueryParamsUsed,
    RagQueryRequest,
    RagQueryResponse,
    RagResetRequest,
    RagResetResponse,
    RagRetrievedChunk,
    RagStatusResponse,
)
from app.llmops import ActiveArtifactResolver
from app.storage.chroma_repository import IngestChunk
from app.storage.chroma_repository import TenantChromaRepository
from app.storage.document_repository import FileDocumentRepository

CHUNK_SPLIT_PATTERN = re.compile(r"\n\s*\n+")


class RagDocumentNotFoundError(FileNotFoundError):
    pass


class RagService:
    def __init__(
        self,
        document_repository: FileDocumentRepository | None = None,
        chroma_repository: TenantChromaRepository | None = None,
        artifact_resolver: ActiveArtifactResolver | None = None,
    ) -> None:
        self.artifact_resolver = artifact_resolver or ActiveArtifactResolver()
        self.document_repository = document_repository or FileDocumentRepository()
        self.chroma_repository = chroma_repository or TenantChromaRepository(
            artifact_resolver=self.artifact_resolver
        )

    def list_documents(self, tenant_id: str) -> RagDocumentListResponse:
        documents = self.document_repository.list_documents(tenant_id)
        status = self.status(tenant_id)
        return RagDocumentListResponse(
            tenant_id=tenant_id,
            source_dir=str(self.document_repository.source_dir(tenant_id)),
            collection_name=self.chroma_repository.collection_name(tenant_id),
            ready=status.ready,
            documents_count=len(documents),
            chunks_count=status.chunks_count,
            last_ingested_at=status.last_ingested_at,
            documents=[self._to_document_summary(document) for document in documents],
        )

    def get_document(self, tenant_id: str, document_id: str) -> RagDocumentContent:
        record = self.document_repository.get_document(tenant_id, document_id)
        if record is None:
            raise RagDocumentNotFoundError(document_id)
        return self._to_document_content(record)

    def create_document(self, request: RagDocumentCreateRequest) -> RagDocumentContent:
        record = RagDocumentRecord(
            tenant_id=request.tenant_id or "",
            title=request.title,
            content=request.content,
            keywords=request.keywords,
            intents=request.intents,
        )
        self.document_repository.save_document(record)
        return self._to_document_content(record)

    def update_document(
        self,
        document_id: str,
        request: RagDocumentUpdateRequest,
    ) -> RagDocumentContent:
        record = self.document_repository.get_document(request.tenant_id or "", document_id)
        if record is None:
            raise RagDocumentNotFoundError(document_id)

        updated_record = record.model_copy(
            update={
                "title": request.title or record.title,
                "content": request.content or record.content,
                "keywords": request.keywords if request.keywords is not None else record.keywords,
                "intents": request.intents if request.intents is not None else record.intents,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self.document_repository.save_document(updated_record)
        return self._to_document_content(updated_record)

    def delete_document(self, tenant_id: str, document_id: str) -> None:
        if not self.document_repository.delete_document(tenant_id, document_id):
            raise RagDocumentNotFoundError(document_id)

    def status(self, tenant_id: str) -> RagStatusResponse:
        documents = self.document_repository.list_documents(tenant_id)
        chunks_count = self.chroma_repository.count_chunks(tenant_id)
        ingest_status = self.document_repository.read_ingest_status(tenant_id)
        last_ingested_at = self._parse_datetime(ingest_status.get("last_ingested_at"))
        ready = chunks_count > 0
        return RagStatusResponse(
            tenant_id=tenant_id,
            collection_name=self.chroma_repository.collection_name(tenant_id),
            source_dir=str(self.document_repository.source_dir(tenant_id)),
            documents_count=len(documents),
            chunks_count=chunks_count,
            ready=ready,
            last_ingested_at=last_ingested_at,
            message=self._status_message(tenant_id, len(documents), chunks_count),
        )

    def ingest(self, request: RagIngestRequest) -> RagIngestResponse:
        tenant_id = request.tenant_id or ""
        documents = self.document_repository.list_documents(tenant_id)
        removed_collections: list[str] = []
        if request.reset_collection:
            removed_collections.extend(self.chroma_repository.reset_tenant_collection(tenant_id))
            removed_collections.extend(self.chroma_repository.remove_legacy_collections(tenant_id))

        chunks = self._build_chunks(documents)
        ingested_chunks = self.chroma_repository.ingest_chunks(tenant_id, chunks)
        status_payload = {
            "last_ingested_at": datetime.now(timezone.utc).isoformat(),
            "documents_count": len(documents),
            "chunks_count": ingested_chunks,
            "removed_collections": removed_collections,
        }
        self.document_repository.write_ingest_status(tenant_id, status_payload)
        ready = ingested_chunks > 0
        return RagIngestResponse(
            tenant_id=tenant_id,
            collection_name=self.chroma_repository.collection_name(tenant_id),
            source_dir=str(self.document_repository.source_dir(tenant_id)),
            documents_count=len(documents),
            chunks_count=ingested_chunks,
            ready=ready,
            reset_collection=request.reset_collection,
            last_ingested_at=self._parse_datetime(status_payload["last_ingested_at"]),
            message=self._ingest_message(tenant_id, len(documents), ingested_chunks),
        )

    def reset(self, request: RagResetRequest) -> RagResetResponse:
        tenant_id = request.tenant_id or ""
        removed_collections = self.chroma_repository.reset_tenant_collection(tenant_id)
        if request.remove_legacy_collections:
            removed_collections.extend(self.chroma_repository.remove_legacy_collections(tenant_id))
        removed_documents_count = 0
        if request.purge_documents:
            removed_documents_count = self.document_repository.reset_documents(tenant_id)
        self.document_repository.write_ingest_status(
            tenant_id,
            {
                "last_ingested_at": None,
                "documents_count": 0 if request.purge_documents else len(self.document_repository.list_documents(tenant_id)),
                "chunks_count": 0,
                "removed_collections": removed_collections,
            },
        )
        return RagResetResponse(
            tenant_id=tenant_id,
            collection_name=self.chroma_repository.collection_name(tenant_id),
            removed_collections=removed_collections,
            removed_documents_count=removed_documents_count,
            source_dir=str(self.document_repository.source_dir(tenant_id)),
            message=self._reset_message(tenant_id, removed_collections, removed_documents_count),
        )

    def query(self, request: RagQueryRequest) -> RagQueryResponse:
        tenant_id = request.tenant_id or ""
        status = self.status(tenant_id)
        chunks = self.chroma_repository.query_chunks(
            tenant_id=tenant_id,
            query_text=request.query,
            limit=request.top_k,
            min_score=request.min_score,
        )
        if not status.ready or not chunks:
            message = status.message if not status.ready else (
                f"Nenhum chunk do tenant '{tenant_id}' atingiu o score mínimo informado."
            )
            query_status = "knowledge_base_not_loaded" if not status.ready else "no_results"
            return RagQueryResponse(
                tenant_id=tenant_id,
                query=request.query,
                status=query_status,
                message=message,
                chunks=[],
                total_chunks=0,
                best_score=0.0,
                params_used=RagQueryParamsUsed(
                    min_score=request.min_score,
                    top_k=request.top_k,
                    boost_enabled=request.boost_enabled,
                    collection=self.chroma_repository.collection_name(tenant_id),
                    strategy_name=self.artifact_resolver.retrieval_strategy_name(),
                ),
            )

        response_chunks = [
            RagRetrievedChunk(
                id=chunk.chunk_id,
                text=chunk.text,
                source=chunk.source,
                title=chunk.title,
                section=chunk.section,
                score=chunk.score,
                tags=chunk.tags,
            )
            for chunk in chunks
        ]
        return RagQueryResponse(
            tenant_id=tenant_id,
            query=request.query,
            status="ready",
            message=f"Recuperados {len(response_chunks)} chunks para o tenant '{tenant_id}'.",
            chunks=response_chunks,
            total_chunks=len(response_chunks),
            best_score=max(chunk.score for chunk in response_chunks),
            params_used=RagQueryParamsUsed(
                min_score=request.min_score,
                top_k=request.top_k,
                boost_enabled=request.boost_enabled,
                collection=self.chroma_repository.collection_name(tenant_id),
                strategy_name=self.artifact_resolver.retrieval_strategy_name(),
            ),
        )

    def _build_chunks(self, documents: list[RagDocumentRecord]) -> list[IngestChunk]:
        chunks: list[IngestChunk] = []
        section_id_template = self.artifact_resolver.chunk_section_id_template()
        for document in documents:
            for index, section in enumerate(self._split_content(document.content), start=1):
                section_id = section_id_template.format(index=index)
                chunks.append(
                    IngestChunk(
                        chunk_id=f"{document.id}:{section_id}",
                        document_id=document.id,
                        title=document.title,
                        section=section_id,
                        source=f"{document.id}.json",
                        text=section,
                        tags=document.keywords + document.intents,
                    )
                )
        return chunks

    def _split_content(self, content: str) -> list[str]:
        split_strategy = self.artifact_resolver.chunk_split_strategy()
        if split_strategy != "double_newline_paragraphs":
            raise ValueError(f"split_strategy nao suportada no runtime atual: {split_strategy}")

        parts = [part.strip() for part in CHUNK_SPLIT_PATTERN.split(content) if part.strip()]
        if not parts:
            empty_fallback = self.artifact_resolver.chunk_empty_content_fallback()
            if empty_fallback != "full_content":
                raise ValueError(
                    f"empty_content_fallback nao suportado no runtime atual: {empty_fallback}"
                )
            return [content.strip()]
        return parts

    def _to_document_summary(self, document: RagDocumentRecord) -> RagDocumentSummary:
        return RagDocumentSummary(
            id=document.id,
            tenant_id=document.tenant_id,
            title=document.title,
            file=f"{document.id}.json",
            tags=document.keywords,
            intents=document.intents,
            updated_at=document.updated_at,
        )

    def _to_document_content(self, document: RagDocumentRecord) -> RagDocumentContent:
        return RagDocumentContent(
            id=document.id,
            tenant_id=document.tenant_id,
            title=document.title,
            file=f"{document.id}.json",
            content=document.content,
            keywords=document.keywords,
            intents=document.intents,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    def _status_message(self, tenant_id: str, documents_count: int, chunks_count: int) -> str:
        if documents_count == 0:
            return (
                f"Base de conhecimento do tenant '{tenant_id}' ainda não possui documentos."
            )
        if chunks_count == 0:
            return (
                f"Documentos do tenant '{tenant_id}' existem, mas a ingestão ainda não foi executada."
            )
        return f"Base de conhecimento do tenant '{tenant_id}' pronta para consulta."

    def _ingest_message(self, tenant_id: str, documents_count: int, chunks_count: int) -> str:
        if documents_count == 0:
            return (
                f"Ingestão concluída sem chunks: o tenant '{tenant_id}' não possui documentos cadastrados."
            )
        return (
            f"Ingestão concluída para o tenant '{tenant_id}' com {documents_count} documento(s) e {chunks_count} chunk(s)."
        )

    def _reset_message(
        self,
        tenant_id: str,
        removed_collections: list[str],
        removed_documents_count: int,
    ) -> str:
        return (
            f"Reset concluído para o tenant '{tenant_id}'. "
            f"Collections removidas: {len(removed_collections)}. "
            f"Documentos removidos: {removed_documents_count}."
        )

    def _parse_datetime(self, value: object) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(str(value))
