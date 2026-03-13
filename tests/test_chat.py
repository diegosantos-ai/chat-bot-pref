import json

from fastapi.testclient import TestClient

from app.api import chat as chat_api
from app.main import app
from app.services.chat_service import ChatService
from app.storage.audit_repository import FileAuditRepository
from app.storage.chat_repository import FileChatRepository
from app.storage.chroma_repository import TenantChromaRepository
from app.tenant_context import get_tenant

client = TestClient(app)


def _build_service(tmp_path) -> ChatService:
    return ChatService(
        repository=FileChatRepository(base_dir=tmp_path),
        audit_repository=FileAuditRepository(base_dir=tmp_path),
        knowledge_repository=TenantChromaRepository(base_dir=tmp_path / "chroma"),
    )


def test_chat_requires_tenant_id() -> None:
    response = client.post("/api/chat", json={"message": "Oi"})

    assert response.status_code == 400
    assert response.json() == {"detail": "tenant_id obrigatório"}


def test_chat_returns_minimal_response(tmp_path) -> None:
    original_service = chat_api.chat_service
    chat_api.chat_service = _build_service(tmp_path)

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Qual o horario?"},
        )
    finally:
        chat_api.chat_service = original_service

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "prefeitura-demo"
    assert payload["message"] == "Fluxo mínimo ativo para o tenant 'prefeitura-demo'."
    assert payload["channel"] == "web"
    assert payload["session_id"]
    assert payload["request_id"]


def test_chat_clears_tenant_context_after_request(tmp_path) -> None:
    original_service = chat_api.chat_service
    chat_api.chat_service = _build_service(tmp_path)

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Teste de contexto"},
        )
    finally:
        chat_api.chat_service = original_service

    assert response.status_code == 200
    assert get_tenant() is None


def test_chat_persists_exchange_by_tenant(tmp_path) -> None:
    original_service = chat_api.chat_service
    chat_api.chat_service = _build_service(tmp_path)

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Teste persistencia"},
        )
    finally:
        chat_api.chat_service = original_service

    assert response.status_code == 200

    payload = response.json()
    output_file = tmp_path / "prefeitura-demo" / f"{payload['session_id']}.jsonl"
    assert output_file.exists()

    lines = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    record = json.loads(lines[0])
    assert record["tenant_id"] == "prefeitura-demo"
    assert record["request_id"] == payload["request_id"]
    assert record["user_message"] == "Teste persistencia"


def test_chat_persists_audit_trail_by_tenant(tmp_path) -> None:
    original_service = chat_api.chat_service
    chat_api.chat_service = _build_service(tmp_path)

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Teste auditoria"},
        )
    finally:
        chat_api.chat_service = original_service

    assert response.status_code == 200

    payload = response.json()
    audit_file = tmp_path / "audit" / "prefeitura-demo" / f"{payload['session_id']}.jsonl"
    assert audit_file.exists()

    lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3

    first_event = json.loads(lines[0])
    second_event = json.loads(lines[1])
    third_event = json.loads(lines[2])
    assert first_event["event_type"] == "chat_request_received"
    assert second_event["event_type"] == "chat_retrieval_completed"
    assert third_event["event_type"] == "chat_response_generated"
    assert first_event["request_id"] == payload["request_id"]
    assert second_event["request_id"] == payload["request_id"]
    assert third_event["request_id"] == payload["request_id"]
    assert second_event["payload"]["retrieved_count"] == "0"
    assert first_event["tenant_id"] == "prefeitura-demo"
    assert second_event["tenant_id"] == "prefeitura-demo"
    assert third_event["tenant_id"] == "prefeitura-demo"


def test_chat_retrieves_context_only_from_same_tenant(tmp_path) -> None:
    original_service = chat_api.chat_service
    chat_api.chat_service = _build_service(tmp_path)

    try:
        first_response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-a", "message": "Alvara atende 8h 17h"},
        )
        second_response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-a", "message": "Qual horario alvara 17h"},
        )
        third_response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-b", "message": "Qual horario alvara 17h"},
        )
    finally:
        chat_api.chat_service = original_service

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert third_response.status_code == 200

    assert "Contexto recuperado: Alvara atende 8h 17h" in second_response.json()["message"]
    assert third_response.json()["message"] == "Fluxo mínimo ativo para o tenant 'prefeitura-b'."
