from pathlib import Path

from app.contracts.dto import RagIngestRequest
from app.services.demo_tenant_service import DemoTenantService
from app.services.rag_service import RagService
from app.storage.chroma_repository import TenantChromaRepository
from app.storage.document_repository import FileDocumentRepository


def _manifest_path() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "tenants"
        / "prefeitura-vila-serena"
        / "tenant.json"
    )


def test_demo_tenant_bundle_validation_passes() -> None:
    service = DemoTenantService()

    validation = service.validate_bundle(_manifest_path())
    managerial_report = service.build_managerial_report(_manifest_path())

    assert validation["status"] == "passed"
    assert validation["tenant_id"] == "prefeitura-vila-serena"
    assert validation["documents_count"] == 3
    assert all(item["ok"] for item in validation["criteria"])
    assert managerial_report["status"] == "passed"
    assert managerial_report["criteria_passed"] == managerial_report["criteria_total"] == 5


def test_demo_tenant_bootstrap_and_ingest(tmp_path) -> None:
    tenant_id = "prefeitura-vila-serena"
    knowledge_dir = tmp_path / "knowledge"
    chroma_dir = tmp_path / "chroma"

    service = DemoTenantService()
    summary = service.bootstrap_bundle(
        manifest_path=_manifest_path(),
        target_base_dir=knowledge_dir,
        purge_documents=True,
    )

    document_repository = FileDocumentRepository(base_dir=knowledge_dir)
    documents = document_repository.list_documents(tenant_id)
    ingest_status = document_repository.read_ingest_status(tenant_id)

    rag_service = RagService(
        document_repository=document_repository,
        chroma_repository=TenantChromaRepository(base_dir=chroma_dir),
    )
    ingest_response = rag_service.ingest(
        RagIngestRequest(tenant_id=tenant_id, reset_collection=True)
    )

    assert summary["tenant_id"] == tenant_id
    assert summary["documents_count"] == 3
    assert len(documents) == 3
    assert ingest_status["documents_count"] == 3
    assert "prefeitura-vila-serena/tenant.json" in ingest_status["source_bundle"]
    assert ingest_response.ready is True
    assert ingest_response.documents_count == 3
    assert ingest_response.chunks_count >= 3
