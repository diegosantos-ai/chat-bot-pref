from fastapi.testclient import TestClient

from app.api import webhook as webhook_api
from app.main import app
from app.services.chat_service import ChatService
from app.storage.audit_repository import FileAuditRepository
from app.storage.chat_repository import FileChatRepository
from app.storage.chroma_repository import TenantChromaRepository
from app.tenant_resolver import TenantResolver

client = TestClient(app)


def _build_service(tmp_path) -> ChatService:
    return ChatService(
        repository=FileChatRepository(base_dir=tmp_path),
        audit_repository=FileAuditRepository(base_dir=tmp_path),
        knowledge_repository=TenantChromaRepository(base_dir=tmp_path / "chroma"),
    )


def test_webhook_accepts_explicit_tenant_id(tmp_path) -> None:
    original_service = webhook_api.chat_service
    original_resolver = webhook_api.tenant_resolver
    webhook_api.chat_service = _build_service(tmp_path)
    webhook_api.tenant_resolver = TenantResolver(page_tenant_map={})

    try:
        response = client.post(
            "/api/webhook",
            json={"tenant_id": "prefeitura-demo", "message": "Teste webhook"},
        )
    finally:
        webhook_api.chat_service = original_service
        webhook_api.tenant_resolver = original_resolver

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "prefeitura-demo"
    assert payload["channel"] == "webhook"


def test_webhook_resolves_tenant_by_page_id(tmp_path) -> None:
    original_service = webhook_api.chat_service
    original_resolver = webhook_api.tenant_resolver
    webhook_api.chat_service = _build_service(tmp_path)
    webhook_api.tenant_resolver = TenantResolver(
        page_tenant_map={"page-prefeitura-demo": "prefeitura-demo"}
    )

    try:
        response = client.post(
            "/api/webhook",
            json={"page_id": "page-prefeitura-demo", "message": "Teste page mapping"},
        )
    finally:
        webhook_api.chat_service = original_service
        webhook_api.tenant_resolver = original_resolver

    assert response.status_code == 200
    assert response.json()["tenant_id"] == "prefeitura-demo"


def test_webhook_rejects_unknown_page_id(tmp_path) -> None:
    original_service = webhook_api.chat_service
    original_resolver = webhook_api.tenant_resolver
    webhook_api.chat_service = _build_service(tmp_path)
    webhook_api.tenant_resolver = TenantResolver(page_tenant_map={})

    try:
        response = client.post(
            "/api/webhook",
            json={"page_id": "page-inexistente", "message": "Teste page mapping"},
        )
    finally:
        webhook_api.chat_service = original_service
        webhook_api.tenant_resolver = original_resolver

    assert response.status_code == 400
    assert response.json() == {"detail": "tenant_id não resolvido para page_id informado"}
