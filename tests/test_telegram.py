import json

from fastapi.testclient import TestClient

from app.api import telegram as telegram_api
from app.main import app
from app.services.chat_service import ChatService
from app.services.rag_service import RagService
from app.services.telegram_service import TelegramBotClient, TelegramDeliveryResult, TelegramService
from app.storage.audit_repository import FileAuditRepository
from app.storage.chat_repository import FileChatRepository
from app.storage.chroma_repository import TenantChromaRepository
from app.storage.document_repository import FileDocumentRepository

client = TestClient(app)


class FakeTelegramBotClient(TelegramBotClient):
    def __init__(self) -> None:
        super().__init__(delivery_mode="dry_run")
        self.deliveries: list[dict[str, str]] = []

    async def send_message(
        self,
        *,
        chat_id: str,
        text: str,
        reply_to_message_id: str | None = None,
    ) -> TelegramDeliveryResult:
        self.deliveries.append(
            {
                "chat_id": chat_id,
                "text": text,
                "reply_to_message_id": reply_to_message_id or "",
            }
        )
        return TelegramDeliveryResult(
            status="dry_run",
            external_message_id=reply_to_message_id or "",
            detail="Entrega Telegram simulada com sucesso em modo dry_run.",
        )


def _build_telegram_service(tmp_path, *, default_tenant_id: str = "prefeitura-vila-serena") -> tuple[TelegramService, FakeTelegramBotClient]:
    rag_service = RagService(
        document_repository=FileDocumentRepository(base_dir=tmp_path / "knowledge"),
        chroma_repository=TenantChromaRepository(base_dir=tmp_path / "chroma"),
    )
    chat_service = ChatService(
        repository=FileChatRepository(base_dir=tmp_path / "runtime"),
        audit_repository=FileAuditRepository(base_dir=tmp_path / "runtime"),
        rag_service=rag_service,
    )
    bot_client = FakeTelegramBotClient()
    return (
        TelegramService(
            chat_service=chat_service,
            bot_client=bot_client,
            default_tenant_id=default_tenant_id,
            chat_tenant_map={},
        ),
        bot_client,
    )


def _telegram_update() -> dict:
    return {
        "update_id": "900001",
        "message": {
            "message_id": "700001",
            "date": 1710000000,
            "chat": {
                "id": "55119990001",
                "type": "private",
                "username": "vila_serena_demo",
            },
            "from": {
                "id": "55119990001",
                "is_bot": False,
                "first_name": "Demo",
                "username": "vila_serena_demo",
            },
            "text": "Qual o horario do alvara?",
        },
    }


def test_telegram_webhook_rejects_invalid_secret(tmp_path) -> None:
    original_service = telegram_api.telegram_service
    original_secret = telegram_api.settings.TELEGRAM_WEBHOOK_SECRET
    telegram_api.telegram_service, _ = _build_telegram_service(tmp_path)
    telegram_api.settings.TELEGRAM_WEBHOOK_SECRET = "telegram-demo-secret"

    try:
        response = client.post("/api/telegram/webhook", json=_telegram_update())
    finally:
        telegram_api.telegram_service = original_service
        telegram_api.settings.TELEGRAM_WEBHOOK_SECRET = original_secret

    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid telegram secret"}


def test_telegram_webhook_processes_demo_tenant_and_audit(tmp_path) -> None:
    original_service = telegram_api.telegram_service
    original_secret = telegram_api.settings.TELEGRAM_WEBHOOK_SECRET
    telegram_service, bot_client = _build_telegram_service(tmp_path)
    telegram_api.telegram_service = telegram_service
    telegram_api.settings.TELEGRAM_WEBHOOK_SECRET = "telegram-demo-secret"

    try:
        response = client.post(
            "/api/telegram/webhook",
            json=_telegram_update(),
            headers={"X-Telegram-Bot-Api-Secret-Token": "telegram-demo-secret"},
        )
    finally:
        telegram_api.telegram_service = original_service
        telegram_api.settings.TELEGRAM_WEBHOOK_SECRET = original_secret

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "processed"
    assert payload["tenant_id"] == "prefeitura-vila-serena"
    assert payload["channel"] == "telegram"
    assert payload["outbound_status"] == "dry_run"
    assert payload["session_id"] == "telegram-55119990001"

    assert len(bot_client.deliveries) == 1
    assert bot_client.deliveries[0]["chat_id"] == "55119990001"
    assert bot_client.deliveries[0]["reply_to_message_id"] == "700001"

    audit_file = (
        tmp_path
        / "runtime"
        / "audit"
        / "prefeitura-vila-serena"
        / f"{payload['session_id']}.jsonl"
    )
    assert audit_file.exists()

    lines = [json.loads(line) for line in audit_file.read_text(encoding="utf-8").strip().splitlines()]
    assert len(lines) == 5
    assert {line["event_type"] for line in lines} == {
        "telegram_update_received",
        "chat_request_received",
        "chat_retrieval_unavailable",
        "chat_response_generated",
        "telegram_message_delivery",
    }
    assert all(line["request_id"] == payload["request_id"] for line in lines)
    assert all(line["tenant_id"] == "prefeitura-vila-serena" for line in lines)
    assert all(line["payload"]["telegram_chat_id"] == "55119990001" for line in lines)
    assert all(line["payload"]["telegram_message_id"] == "700001" for line in lines)
    assert all(line["payload"]["telegram_update_id"] == "900001" for line in lines)


def test_telegram_webhook_requires_tenant_resolution(tmp_path) -> None:
    original_service = telegram_api.telegram_service
    original_secret = telegram_api.settings.TELEGRAM_WEBHOOK_SECRET
    telegram_service, _ = _build_telegram_service(tmp_path, default_tenant_id="")
    telegram_api.telegram_service = telegram_service
    telegram_api.settings.TELEGRAM_WEBHOOK_SECRET = ""

    try:
        response = client.post("/api/telegram/webhook", json=_telegram_update())
    finally:
        telegram_api.telegram_service = original_service
        telegram_api.settings.TELEGRAM_WEBHOOK_SECRET = original_secret

    assert response.status_code == 400
    assert "tenant_id nao resolvido" in response.json()["detail"]
