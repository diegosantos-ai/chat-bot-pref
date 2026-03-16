from fastapi.testclient import TestClient

from app.api import rag as rag_api
from app.main import app
from app.rag.query_transformation import (
    NO_QUERY_TRANSFORM_STRATEGY_NAME,
    TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME,
)
from app.rag.retrieval_scoring import (
    BASELINE_RETRIEVAL_STRATEGY_NAME,
    HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
)
from app.services.rag_service import RagService
from app.storage.chroma_repository import TenantChromaRepository
from app.storage.document_repository import FileDocumentRepository

client = TestClient(app)


def _build_rag_service(tmp_path) -> RagService:
    return RagService(
        document_repository=FileDocumentRepository(base_dir=tmp_path / "knowledge"),
        chroma_repository=TenantChromaRepository(base_dir=tmp_path / "chroma"),
    )


def test_rag_status_reports_empty_base(tmp_path) -> None:
    original_service = rag_api.rag_service
    rag_api.rag_service = _build_rag_service(tmp_path)

    try:
        response = client.get("/api/rag/status", params={"tenant_id": "prefeitura-demo"})
    finally:
        rag_api.rag_service = original_service

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "prefeitura-demo"
    assert payload["documents_count"] == 0
    assert payload["chunks_count"] == 0
    assert payload["ready"] is False
    assert payload["message"] == "Base de conhecimento do tenant 'prefeitura-demo' ainda não possui documentos."


def test_rag_document_crud_ingest_and_query_by_tenant(tmp_path) -> None:
    original_service = rag_api.rag_service
    rag_api.rag_service = _build_rag_service(tmp_path)

    try:
        create_response = client.post(
            "/api/rag/documents",
            json={
                "tenant_id": "prefeitura-demo",
                "title": "Horario Alvara",
                "content": "O setor de alvará atende das 8h às 17h.\n\nLeve documento com foto.",
                "keywords": ["alvara", "horario"],
                "intents": ["INFO_REQUEST"],
            },
        )
        document_id = create_response.json()["id"]

        list_response = client.get(
            "/api/rag/documents",
            params={"tenant_id": "prefeitura-demo"},
        )
        get_response = client.get(
            f"/api/rag/documents/{document_id}",
            params={"tenant_id": "prefeitura-demo"},
        )
        update_response = client.put(
            f"/api/rag/documents/{document_id}",
            json={
                "tenant_id": "prefeitura-demo",
                "content": "O setor de alvará atende das 8h às 17h.\n\nLeve documento com foto e comprovante.",
            },
        )
        ingest_response = client.post(
            "/api/rag/ingest",
            json={"tenant_id": "prefeitura-demo", "reset_collection": True},
        )
        query_response = client.post(
            "/api/rag/query",
            json={
                "tenant_id": "prefeitura-demo",
                "query": "Qual o horario do alvara?",
                "min_score": 0.1,
                "top_k": 3,
                "boost_enabled": False,
            },
        )
        other_tenant_query = client.post(
            "/api/rag/query",
            json={
                "tenant_id": "prefeitura-b",
                "query": "Qual o horario do alvara?",
                "min_score": 0.1,
                "top_k": 3,
                "boost_enabled": False,
            },
        )
        delete_response = client.delete(
            f"/api/rag/documents/{document_id}",
            params={"tenant_id": "prefeitura-demo"},
        )
    finally:
        rag_api.rag_service = original_service

    assert create_response.status_code == 200
    assert list_response.status_code == 200
    assert get_response.status_code == 200
    assert update_response.status_code == 200
    assert ingest_response.status_code == 200
    assert query_response.status_code == 200
    assert other_tenant_query.status_code == 200
    assert delete_response.status_code == 200

    assert list_response.json()["documents_count"] == 1
    assert get_response.json()["title"] == "Horario Alvara"
    assert "comprovante" in update_response.json()["content"]
    assert ingest_response.json()["chunks_count"] == 2
    assert ingest_response.json()["ready"] is True
    assert query_response.json()["status"] == "ready"
    assert query_response.json()["params_used"]["strategy_name"] == BASELINE_RETRIEVAL_STRATEGY_NAME
    assert (
        query_response.json()["params_used"]["query_transformation"]["strategy_name"]
        == NO_QUERY_TRANSFORM_STRATEGY_NAME
    )
    assert query_response.json()["params_used"]["query_transformation"]["applied"] is False
    assert (
        query_response.json()["params_used"]["query_transformation"]["retrieval_query"]
        == "Qual o horario do alvara?"
    )
    assert query_response.json()["chunks"][0]["title"] == "Horario Alvara"
    assert other_tenant_query.json()["status"] == "knowledge_base_not_loaded"


def test_rag_query_supports_explicit_strategies_and_rejects_unknown_values(tmp_path) -> None:
    original_service = rag_api.rag_service
    rag_api.rag_service = _build_rag_service(tmp_path)

    try:
        client.post(
            "/api/rag/documents",
            json={
                "tenant_id": "prefeitura-demo",
                "title": "Horario Alvara",
                "content": "O setor de alvara atende das 8h as 17h.\n\nLeve documento com foto.",
                "keywords": ["alvara", "horario"],
                "intents": ["INFO_REQUEST"],
            },
        )
        client.post(
            "/api/rag/ingest",
            json={"tenant_id": "prefeitura-demo", "reset_collection": True},
        )
        hybrid_response = client.post(
            "/api/rag/query",
            json={
                "tenant_id": "prefeitura-demo",
                "query": "Qual o horario do alvara?",
                "min_score": 0.1,
                "top_k": 3,
                "boost_enabled": False,
                "strategy_name": HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
            },
        )
        expanded_response = client.post(
            "/api/rag/query",
            json={
                "tenant_id": "prefeitura-demo",
                "query": "Qual o horario?",
                "min_score": 0.1,
                "top_k": 3,
                "boost_enabled": False,
                "strategy_name": HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME,
                "query_transform_strategy_name": TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME,
            },
        )
        invalid_response = client.post(
            "/api/rag/query",
            json={
                "tenant_id": "prefeitura-demo",
                "query": "Qual o horario do alvara?",
                "strategy_name": "strategy.inexistente",
            },
        )
        invalid_query_transform_response = client.post(
            "/api/rag/query",
            json={
                "tenant_id": "prefeitura-demo",
                "query": "Qual o horario?",
                "query_transform_strategy_name": "query_transform.inexistente",
            },
        )
    finally:
        rag_api.rag_service = original_service

    assert hybrid_response.status_code == 200
    assert (
        hybrid_response.json()["params_used"]["strategy_name"]
        == HYBRID_FULL_COLLECTION_LEXICAL_STRATEGY_NAME
    )
    assert expanded_response.status_code == 200
    assert (
        expanded_response.json()["params_used"]["query_transformation"]["strategy_name"]
        == TENANT_KEYWORD_QUERY_EXPANSION_STRATEGY_NAME
    )
    assert expanded_response.json()["params_used"]["query_transformation"]["applied"] is True
    assert expanded_response.json()["query"] == "Qual o horario?"
    assert (
        expanded_response.json()["params_used"]["query_transformation"]["original_query"]
        == "Qual o horario?"
    )
    assert (
        expanded_response.json()["params_used"]["query_transformation"]["retrieval_query"]
        == "Qual o horario? alvara"
    )
    assert expanded_response.json()["params_used"]["query_transformation"]["added_terms"] == ["alvara"]
    assert invalid_response.status_code == 400
    assert "nao suportada" in invalid_response.json()["detail"]
    assert invalid_query_transform_response.status_code == 400
    assert "query transformation" in invalid_query_transform_response.json()["detail"]


def test_rag_reset_removes_current_and_legacy_collections(tmp_path) -> None:
    service = _build_rag_service(tmp_path)
    original_service = rag_api.rag_service
    rag_api.rag_service = service

    try:
        client.post(
            "/api/rag/documents",
            json={
                "tenant_id": "prefeitura-demo",
                "title": "Servico de Saude",
                "content": "A UBS atende das 7h às 19h.",
                "keywords": ["saude"],
                "intents": ["INFO_REQUEST"],
            },
        )
        client.post(
            "/api/rag/ingest",
            json={"tenant_id": "prefeitura-demo", "reset_collection": True},
        )

        legacy_collection_name = "chat_pref__prefeitura_demo"
        service.chroma_repository.client.get_or_create_collection(
            legacy_collection_name,
            embedding_function=service.chroma_repository.embedding_function,
        )

        response = client.post(
            "/api/rag/reset",
            json={
                "tenant_id": "prefeitura-demo",
                "purge_documents": True,
                "remove_legacy_collections": True,
            },
        )
    finally:
        rag_api.rag_service = original_service

    assert response.status_code == 200
    payload = response.json()
    assert payload["removed_documents_count"] == 1
    assert legacy_collection_name in payload["removed_collections"]
    assert service.chroma_repository.count_chunks("prefeitura-demo") == 0
    assert service.document_repository.list_documents("prefeitura-demo") == []
