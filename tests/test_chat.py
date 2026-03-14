import json

from fastapi.testclient import TestClient

from app.api import chat as chat_api
from app.main import app
from app.services.chat_service import ChatService
from app.services.rag_service import RagService
from app.storage.audit_repository import FileAuditRepository
from app.storage.chat_repository import FileChatRepository
from app.storage.chroma_repository import TenantChromaRepository
from app.storage.document_repository import FileDocumentRepository
from app.tenant_context import get_tenant

client = TestClient(app)


def _build_rag_service(tmp_path) -> RagService:
    return RagService(
        document_repository=FileDocumentRepository(base_dir=tmp_path / "knowledge"),
        chroma_repository=TenantChromaRepository(base_dir=tmp_path / "chroma"),
    )


def _build_chat_service(tmp_path) -> ChatService:
    return ChatService(
        repository=FileChatRepository(base_dir=tmp_path / "runtime"),
        audit_repository=FileAuditRepository(base_dir=tmp_path / "runtime"),
        rag_service=_build_rag_service(tmp_path),
    )


def test_chat_requires_tenant_id() -> None:
    response = client.post("/api/chat", json={"message": "Oi"})

    assert response.status_code == 400
    assert response.json() == {"detail": "tenant_id obrigatório"}


def test_chat_returns_controlled_message_without_ingest(tmp_path) -> None:
    original_service = chat_api.chat_service
    chat_api.chat_service = _build_chat_service(tmp_path)

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
    assert "ainda nao possui informacoes carregadas" in payload["message"]
    assert payload["channel"] == "web"
    assert payload["session_id"]
    assert payload["request_id"]
    assert response.headers["X-Request-ID"] == payload["request_id"]


def test_chat_clears_tenant_context_after_request(tmp_path) -> None:
    original_service = chat_api.chat_service
    chat_api.chat_service = _build_chat_service(tmp_path)

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
    chat_api.chat_service = _build_chat_service(tmp_path)

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Teste persistencia"},
        )
    finally:
        chat_api.chat_service = original_service

    assert response.status_code == 200

    payload = response.json()
    output_file = tmp_path / "runtime" / "prefeitura-demo" / f"{payload['session_id']}.jsonl"
    assert output_file.exists()

    lines = output_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    record = json.loads(lines[0])
    assert record["tenant_id"] == "prefeitura-demo"
    assert record["request_id"] == payload["request_id"]
    assert record["user_message"] == "Teste persistencia"


def test_chat_persists_audit_trail_by_tenant(tmp_path) -> None:
    original_service = chat_api.chat_service
    chat_api.chat_service = _build_chat_service(tmp_path)

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Teste auditoria"},
        )
    finally:
        chat_api.chat_service = original_service

    assert response.status_code == 200

    payload = response.json()
    audit_file = tmp_path / "runtime" / "audit" / "prefeitura-demo" / f"{payload['session_id']}.jsonl"
    assert audit_file.exists()

    lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 6

    first_event = json.loads(lines[0])
    second_event = json.loads(lines[1])
    third_event = json.loads(lines[2])
    fourth_event = json.loads(lines[3])
    fifth_event = json.loads(lines[4])
    sixth_event = json.loads(lines[5])
    assert [event["event_type"] for event in [first_event, second_event, third_event, fourth_event, fifth_event, sixth_event]] == [
        "chat_request_received",
        "policy_pre_evaluated",
        "chat_retrieval_unavailable",
        "llm_composition_completed",
        "policy_post_evaluated",
        "chat_response_generated",
    ]
    assert all(event["request_id"] == payload["request_id"] for event in [first_event, second_event, third_event, fourth_event, fifth_event, sixth_event])
    assert third_event["payload"]["retrieved_count"] == "0"
    assert third_event["payload"]["status"] == "knowledge_base_not_loaded"
    assert second_event["policy_decision"]["stage"] == "policy_pre"
    assert fifth_event["policy_decision"]["stage"] == "policy_post"
    assert fifth_event["policy_decision"]["reason_codes"] == ["NO_KNOWLEDGE_BASE"]
    assert all(event["tenant_id"] == "prefeitura-demo" for event in [first_event, second_event, third_event, fourth_event, fifth_event, sixth_event])
    assert all(event["schema_version"] == "audit.v1" for event in [first_event, second_event, third_event, fourth_event, fifth_event, sixth_event])


def test_chat_uses_ingested_document_context_and_isolated_tenant(tmp_path) -> None:
    rag_service = _build_rag_service(tmp_path)
    rag_service.create_document(
        type("Request", (), {
            "tenant_id": "prefeitura-a",
            "title": "Horario Alvara",
            "content": "O setor de alvará atende das 8h às 17h.",
            "keywords": ["alvara", "horario"],
            "intents": ["INFO_REQUEST"],
        })()
    )
    rag_service.ingest(
        type("Request", (), {"tenant_id": "prefeitura-a", "reset_collection": True})()
    )

    original_service = chat_api.chat_service
    chat_api.chat_service = ChatService(
        repository=FileChatRepository(base_dir=tmp_path / "runtime"),
        audit_repository=FileAuditRepository(base_dir=tmp_path / "runtime"),
        rag_service=rag_service,
    )

    try:
        first_response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-a", "message": "Qual o horario do alvara?"},
        )
        second_response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-b", "message": "Qual o horario do alvara?"},
        )
    finally:
        chat_api.chat_service = original_service

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert "O setor de alvará atende das 8h às 17h" in first_response.json()["message"]
    assert "ainda nao possui informacoes carregadas" in second_response.json()["message"]
