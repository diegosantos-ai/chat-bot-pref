import json

from fastapi.testclient import TestClient

from app.api import chat as chat_api
from app.main import app
from app.services.chat_service import ChatService
from app.services.rag_service import RagService
from app.settings import settings
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


def test_metrics_endpoint_exposes_phase11_series(tmp_path, monkeypatch) -> None:
    original_service = chat_api.chat_service
    original_data_dir = settings.DATA_DIR
    settings.DATA_DIR = str(tmp_path / "runtime")
    chat_api.chat_service = _build_chat_service(tmp_path)

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Qual o horario do alvara?"},
            headers={"X-Request-ID": "req-phase11-metrics"},
        )
        metrics_response = client.get("/metrics")
    finally:
        chat_api.chat_service = original_service
        settings.DATA_DIR = original_data_dir

    assert response.status_code == 200
    assert metrics_response.status_code == 200
    payload = metrics_response.text
    assert "chatpref_chat_requests_total" in payload
    assert "chatpref_policy_decisions_total" in payload
    assert "chatpref_retrieval_total" in payload
    assert "chatpref_llm_compositions_total" in payload
    assert "chatpref_llm_compose_latency_seconds" in payload
    assert "chatpref_pipeline_stage_latency_seconds" in payload
    assert 'tenant_id="prefeitura-demo"' in payload
    assert 'stage_name="policy_pre"' in payload
    assert 'stage_name="query_expansion"' in payload
    assert 'stage_name="retrieval"' in payload
    assert 'stage_name="composer"' in payload
    assert 'stage_name="policy_post"' in payload
    assert 'stage_name="response_final"' in payload


def test_structured_logs_include_request_id_and_event_type(tmp_path) -> None:
    original_service = chat_api.chat_service
    original_data_dir = settings.DATA_DIR
    settings.DATA_DIR = str(tmp_path / "runtime")
    chat_api.chat_service = _build_chat_service(tmp_path)

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Teste logs estruturados"},
            headers={"X-Request-ID": "req-phase11-logs"},
        )
    finally:
        chat_api.chat_service = original_service
        settings.DATA_DIR = original_data_dir

    assert response.status_code == 200
    log_file = tmp_path / "runtime" / "logs" / "prefeitura-demo" / "req-phase11-logs.jsonl"
    assert log_file.exists()
    log_lines = [
        json.loads(line)
        for line in log_file.read_text(encoding="utf-8").strip().splitlines()
        if line.strip()
    ]
    assert any(
        line.get("event_name") == "chat.process.started"
        and line.get("request_id") == "req-phase11-logs"
        for line in log_lines
    )
    assert any(
        line.get("event_name") == "audit.event.persisted"
        and line.get("event_type") == "policy_post_evaluated"
        and line.get("request_id") == "req-phase11-logs"
        for line in log_lines
    )


def test_trace_file_contains_pipeline_spans_by_request_id(tmp_path) -> None:
    original_service = chat_api.chat_service
    original_data_dir = settings.DATA_DIR
    settings.DATA_DIR = str(tmp_path / "runtime")
    chat_api.chat_service = _build_chat_service(tmp_path)

    try:
        response = client.post(
            "/api/chat",
            json={"tenant_id": "prefeitura-demo", "message": "Qual o horario do alvara?"},
            headers={"X-Request-ID": "req-phase11-trace"},
        )
    finally:
        chat_api.chat_service = original_service
        settings.DATA_DIR = original_data_dir

    assert response.status_code == 200

    trace_file = tmp_path / "runtime" / "traces" / "prefeitura-demo" / "req-phase11-trace.jsonl"
    assert trace_file.exists()

    spans = [
        json.loads(line)
        for line in trace_file.read_text(encoding="utf-8").strip().splitlines()
        if line.strip()
    ]
    span_names = {item["name"] for item in spans}
    assert {
        "http.request",
        "chat.process",
        "policy_pre",
        "retrieval",
        "compose",
        "policy_post",
        "response",
    }.issubset(span_names)
    assert all(item["request_id"] == "req-phase11-trace" for item in spans)
    assert all(item["tenant_id"] == "prefeitura-demo" for item in spans if item["tenant_id"])
