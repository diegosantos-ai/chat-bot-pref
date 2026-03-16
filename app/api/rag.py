from fastapi import APIRouter
from fastapi import HTTPException

from app.contracts.dto import (
    RagDocumentContent,
    RagDocumentCreateRequest,
    RagDocumentListResponse,
    RagDocumentUpdateRequest,
    RagIngestRequest,
    RagIngestResponse,
    RagQueryRequest,
    RagQueryResponse,
    RagResetRequest,
    RagResetResponse,
    RagStatusResponse,
)
from app.services.rag_service import RagDocumentNotFoundError, RagService

router = APIRouter(prefix="/api", tags=["RAG"])
rag_service = RagService()


def _require_tenant(tenant_id: str | None) -> str:
    normalized = str(tenant_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="tenant_id obrigatório")
    return normalized


@router.get("/rag/status", response_model=RagStatusResponse)
async def rag_status(tenant_id: str | None = None) -> RagStatusResponse:
    return rag_service.status(_require_tenant(tenant_id))


@router.get("/rag/documents", response_model=RagDocumentListResponse)
async def list_documents(tenant_id: str | None = None) -> RagDocumentListResponse:
    return rag_service.list_documents(_require_tenant(tenant_id))


@router.get("/rag/documents/{document_id}", response_model=RagDocumentContent)
async def get_document(document_id: str, tenant_id: str | None = None) -> RagDocumentContent:
    try:
        return rag_service.get_document(_require_tenant(tenant_id), document_id)
    except RagDocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="documento não encontrado") from exc


@router.post("/rag/documents", response_model=RagDocumentContent)
async def create_document(request: RagDocumentCreateRequest) -> RagDocumentContent:
    request.tenant_id = _require_tenant(request.tenant_id)
    return rag_service.create_document(request)


@router.put("/rag/documents/{document_id}", response_model=RagDocumentContent)
async def update_document(
    document_id: str,
    request: RagDocumentUpdateRequest,
) -> RagDocumentContent:
    request.tenant_id = _require_tenant(request.tenant_id)
    try:
        return rag_service.update_document(document_id, request)
    except RagDocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="documento não encontrado") from exc


@router.delete("/rag/documents/{document_id}")
async def delete_document(document_id: str, tenant_id: str | None = None) -> dict[str, str]:
    try:
        rag_service.delete_document(_require_tenant(tenant_id), document_id)
    except RagDocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="documento não encontrado") from exc
    return {"status": "deleted"}


@router.post("/rag/ingest", response_model=RagIngestResponse)
async def ingest_documents(request: RagIngestRequest) -> RagIngestResponse:
    request.tenant_id = _require_tenant(request.tenant_id)
    return rag_service.ingest(request)


@router.post("/rag/reset", response_model=RagResetResponse)
async def reset_rag(request: RagResetRequest) -> RagResetResponse:
    request.tenant_id = _require_tenant(request.tenant_id)
    return rag_service.reset(request)


@router.post("/rag/query", response_model=RagQueryResponse)
async def query_rag(request: RagQueryRequest) -> RagQueryResponse:
    request.tenant_id = _require_tenant(request.tenant_id)
    try:
        return rag_service.query(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
