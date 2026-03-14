from pathlib import Path

from app.contracts.dto import RagIngestRequest, RagQueryRequest
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
    assert validation["documents_count"] == 11
    assert all(item["ok"] for item in validation["criteria"])
    assert managerial_report["status"] == "passed"
    assert managerial_report["criteria_passed"] == managerial_report["criteria_total"] == 5


def test_demo_knowledge_base_bundle_validation_passes() -> None:
    service = DemoTenantService()

    validation = service.validate_knowledge_base_bundle(_manifest_path())
    retrieval_checks = service.load_retrieval_checks(_manifest_path())

    assert validation["status"] == "passed"
    assert validation["documents_count"] == 11
    assert validation["retrieval_checks_count"] == 8
    assert len(retrieval_checks) == 8
    assert all(item["ok"] for item in validation["criteria"])


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
    assert summary["documents_count"] == 11
    assert len(documents) == 11
    assert ingest_status["documents_count"] == 11
    assert "prefeitura-vila-serena/tenant.json" in ingest_status["source_bundle"]
    assert ingest_response.ready is True
    assert ingest_response.documents_count == 11
    assert ingest_response.chunks_count >= 18


def test_demo_phase10_managerial_report_passes() -> None:
    service = DemoTenantService()

    report = service.build_phase10_managerial_report(
        _manifest_path(),
        runtime_validation={
            "llm_adapter_validation": {"ok": True, "evidence": "provider=mock | prompt_versions=['base_v1','fallback_v1']"},
            "prompt_policy_validation": {"ok": True, "evidence": "prompt_versions=['base_v1','fallback_v1'] | policy_versions=['policy_v1']"},
            "composition_validation": {"ok": True, "evidence": "SCN-01 | prompt=base_v1 | rubric=12"},
            "policy_validation": {"ok": True, "evidence": "scenarios_with_policy=5/5 | policy_versions=['policy_v1']"},
            "scenario_validation": {"ok": True, "evidence": "scenarios_passed=5/5"},
            "audit_validation": {"ok": True, "evidence": "request_ids_correlated=True | scenarios=5"},
            "scope_validation": {"ok": True, "evidence": "transactional_claims_blocked=True | checked_scenarios=5"},
        },
    )

    assert report["status"] == "passed"
    assert report["criteria_passed"] == report["criteria_total"] == 7


def test_demo_knowledge_base_controlled_retrieval_checks_pass(tmp_path) -> None:
    tenant_id = "prefeitura-vila-serena"
    knowledge_dir = tmp_path / "knowledge"
    chroma_dir = tmp_path / "chroma"

    service = DemoTenantService()
    service.bootstrap_bundle(
        manifest_path=_manifest_path(),
        target_base_dir=knowledge_dir,
        purge_documents=True,
    )

    rag_service = RagService(
        document_repository=FileDocumentRepository(base_dir=knowledge_dir),
        chroma_repository=TenantChromaRepository(base_dir=chroma_dir),
    )
    rag_service.ingest(RagIngestRequest(tenant_id=tenant_id, reset_collection=True))

    checks = service.load_retrieval_checks(_manifest_path())
    assert len(checks) == 8

    for check in checks:
        response = rag_service.query(
            RagQueryRequest(
                tenant_id=tenant_id,
                query=check.question,
                top_k=8,
                min_score=0.1,
                boost_enabled=False,
            )
        )
        assert response.status == "ready"
        assert any(
            check.expected_title_contains.lower() in chunk.title.lower()
            and all(term.lower() in chunk.text.lower() for term in check.expected_terms)
            for chunk in response.chunks
        )
