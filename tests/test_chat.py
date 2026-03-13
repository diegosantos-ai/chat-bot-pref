from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_requires_tenant_id() -> None:
    response = client.post("/api/chat", json={"message": "Oi"})

    assert response.status_code == 400
    assert response.json() == {"detail": "tenant_id obrigatório"}


def test_chat_returns_minimal_response() -> None:
    response = client.post(
        "/api/chat",
        json={"tenant_id": "prefeitura-demo", "message": "Qual o horario?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "prefeitura-demo"
    assert payload["message"] == "Fluxo mínimo ativo para o tenant 'prefeitura-demo'."
    assert payload["channel"] == "web"
    assert payload["session_id"]
