
import os
import pytest
import httpx
import json
from unittest.mock import AsyncMock, patch

_host = os.getenv("APP_HOST", "localhost")
if _host in {"0.0.0.0", "::"}:
    _host = "localhost"
_port = os.getenv("APP_PORT", "8000")
BASE_URL = os.getenv("API_BASE_URL", f"http://{_host}:{_port}")

@pytest.mark.asyncio
async def test_analytics_summary():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/analytics/summary")
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/json'
        try:
            response.json()
        except json.JSONDecodeError:
            assert False, "Response is not a valid JSON"

@pytest.mark.asyncio
async def test_api_chat():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        payload = {"session_id": "test_session", "message": "Qual o telefone da prefeitura?", "channel": "web", "surface_type": "inbox"}
        response = await client.post("/api/chat", json=payload)
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/json'
        try:
            response.json()
        except json.JSONDecodeError:
            assert False, "Response is not a valid JSON"
        assert "message" in response.json()

@pytest.mark.asyncio
async def test_webhook_meta():
    # Mock the WebhookHandler class
    with patch("app.api.webhook.WebhookHandler") as MockWebhookHandler:
        mock_handler = AsyncMock()
        MockWebhookHandler.return_value = mock_handler
        mock_handler.verify_webhook_signature.return_value = True
        mock_handler.handle_incoming_message.return_value = None

        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            payload = {"object": "page", "entry": [{"id": "test_page", "time": 1672531200, "messaging": [{"sender": {"id": "test_sender"}, "recipient": {"id": "test_recipient"}, "timestamp": 1672531200, "message": {"mid": "test_mid", "text": "hello"}}]}]}
            response = await client.post("/webhook/meta", json=payload, headers={"X-Hub-Signature": "test_signature"})
            assert response.status_code == 200
