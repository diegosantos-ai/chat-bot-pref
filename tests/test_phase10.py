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


def _load_audit_events(tmp_path, tenant_id: str, session_id: str) -> list[dict]:
    audit_file = tmp_path / "runtime" / "audit" / tenant_id / f"{session_id}.jsonl"
    assert audit_file.exists()
    return [
        json.loads(line)
        for line in audit_file.read_text(encoding="utf-8").strip().splitlines()
        if line.strip()
    ]


def test_chat_propagates_x_request_id_header(tmp_path) -> None:
    original_service = chat_api.chat_service
    chat_api.chat_service = _build_chat_service(tmp_path)

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Qual o horario?"},
            headers={"X-Request-ID": "req-phase10-001"},
        )
    finally:
        chat_api.chat_service = original_service

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-phase10-001"
    assert response.json()["request_id"] == "req-phase10-001"


def test_policy_pre_blocks_out_of_scope_request(tmp_path) -> None:
    original_service = chat_api.chat_service
    chat_api.chat_service = _build_chat_service(tmp_path)

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Me diga onde investir meu dinheiro"},
        )
    finally:
        chat_api.chat_service = original_service

    assert response.status_code == 200
    payload = response.json()
    assert "apenas com orientacoes institucionais" in payload["message"]

    events = _load_audit_events(tmp_path, "prefeitura-demo", payload["session_id"])
    event_types = [event["event_type"] for event in events]
    assert "chat_retrieval_skipped" in event_types
    pre_event = next(event for event in events if event["event_type"] == "policy_pre_evaluated")
    assert pre_event["policy_decision"]["decision"] == "block"
    assert pre_event["policy_decision"]["reason_codes"] == ["OUT_OF_SCOPE"]


def test_policy_post_falls_back_on_low_confidence_retrieval(tmp_path) -> None:
    rag_service = _build_rag_service(tmp_path)
    rag_service.create_document(
        type("Request", (), {
            "tenant_id": "prefeitura-demo",
            "title": "Horario Alvara",
            "content": "O setor de alvará atende das 8h às 17h.",
            "keywords": ["alvara", "horario"],
            "intents": ["INFO_REQUEST"],
        })()
    )
    rag_service.ingest(
        type("Request", (), {"tenant_id": "prefeitura-demo", "reset_collection": True})()
    )

    original_service = chat_api.chat_service
    chat_api.chat_service = ChatService(
        repository=FileChatRepository(base_dir=tmp_path / "runtime"),
        audit_repository=FileAuditRepository(base_dir=tmp_path / "runtime"),
        rag_service=rag_service,
    )

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Tem estacionamento no centro?"},
        )
    finally:
        chat_api.chat_service = original_service

    assert response.status_code == 200
    payload = response.json()
    assert "Nao encontrei contexto institucional suficiente" in payload["message"]

    events = _load_audit_events(tmp_path, "prefeitura-demo", payload["session_id"])
    post_event = next(event for event in events if event["event_type"] == "policy_post_evaluated")
    composition_event = next(event for event in events if event["event_type"] == "llm_composition_completed")
    rewrite_event = next(event for event in events if event["event_type"] == "llm_response_rewritten")
    assert post_event["policy_decision"]["decision"] == "fallback"
    assert post_event["policy_decision"]["reason_codes"] == ["LOW_CONFIDENCE_RETRIEVAL"]
    assert composition_event["payload"]["prompt_version"] == "base_v1"
    assert rewrite_event["payload"]["prompt_version"] == "fallback_v1"


def test_short_greeting_uses_clarifying_low_confidence_message(tmp_path) -> None:
    rag_service = _build_rag_service(tmp_path)
    rag_service.create_document(
        type("Request", (), {
            "tenant_id": "prefeitura-demo",
            "title": "Horario Alvara",
            "content": "O setor de alvará atende das 8h às 17h.",
            "keywords": ["alvara", "horario"],
            "intents": ["INFO_REQUEST"],
        })()
    )
    rag_service.ingest(
        type("Request", (), {"tenant_id": "prefeitura-demo", "reset_collection": True})()
    )

    original_service = chat_api.chat_service
    chat_api.chat_service = ChatService(
        repository=FileChatRepository(base_dir=tmp_path / "runtime"),
        audit_repository=FileAuditRepository(base_dir=tmp_path / "runtime"),
        rag_service=rag_service,
    )

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Oi"},
        )
    finally:
        chat_api.chat_service = original_service

    assert response.status_code == 200
    payload = response.json()
    assert "Posso orientar sobre servicos e informacoes institucionais" in payload["message"]
    assert "Descreva o assunto ou servico" in payload["message"]

    events = _load_audit_events(tmp_path, "prefeitura-demo", payload["session_id"])
    post_event = next(event for event in events if event["event_type"] == "policy_post_evaluated")
    rewrite_event = next(event for event in events if event["event_type"] == "llm_response_rewritten")
    assert post_event["policy_decision"]["decision"] == "fallback"
    assert post_event["policy_decision"]["reason_codes"] == ["LOW_CONFIDENCE_RETRIEVAL"]
    assert rewrite_event["payload"]["prompt_version"] == "fallback_v1"


def test_supported_question_uses_base_prompt_and_allows_policy_post(tmp_path) -> None:
    rag_service = _build_rag_service(tmp_path)
    rag_service.create_document(
        type("Request", (), {
            "tenant_id": "prefeitura-demo",
            "title": "Horario Alvara",
            "content": "O setor de alvará atende das 8h às 17h.",
            "keywords": ["alvara", "horario"],
            "intents": ["INFO_REQUEST"],
        })()
    )
    rag_service.ingest(
        type("Request", (), {"tenant_id": "prefeitura-demo", "reset_collection": True})()
    )

    original_service = chat_api.chat_service
    chat_api.chat_service = ChatService(
        repository=FileChatRepository(base_dir=tmp_path / "runtime"),
        audit_repository=FileAuditRepository(base_dir=tmp_path / "runtime"),
        rag_service=rag_service,
    )

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Qual o horario do alvara?"},
        )
    finally:
        chat_api.chat_service = original_service

    assert response.status_code == 200
    payload = response.json()
    assert "O setor de alvará atende das 8h às 17h" in payload["message"]

    events = _load_audit_events(tmp_path, "prefeitura-demo", payload["session_id"])
    composition_event = next(event for event in events if event["event_type"] == "llm_composition_completed")
    post_event = next(event for event in events if event["event_type"] == "policy_post_evaluated")
    assert composition_event["payload"]["prompt_version"] == "base_v1"
    assert composition_event["payload"]["provider"] == "mock"
    assert post_event["policy_decision"]["decision"] == "allow"
