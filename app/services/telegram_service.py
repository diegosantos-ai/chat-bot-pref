from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import httpx

from app.contracts.dto import (
    AuditEventRecord,
    ChatRequest,
    TelegramMessage,
    TelegramWebhookRequest,
    TelegramWebhookResponse,
)
from app.services.chat_service import ChatService
from app.settings import settings
from app.storage.audit_repository import FileAuditRepository
from app.tenant_context import clear_tenant, set_tenant


class TelegramTenantResolutionError(RuntimeError):
    pass


class TelegramDeliveryError(RuntimeError):
    pass


@dataclass
class TelegramDeliveryResult:
    status: str
    external_message_id: str = ""
    detail: str = ""


class TelegramBotClient:
    def __init__(
        self,
        *,
        bot_token: str | None = None,
        api_base_url: str | None = None,
        delivery_mode: str | None = None,
    ) -> None:
        self.bot_token = (bot_token or settings.TELEGRAM_BOT_TOKEN).strip()
        self.api_base_url = (api_base_url or settings.TELEGRAM_API_BASE_URL).rstrip("/")
        self.delivery_mode = (delivery_mode or settings.TELEGRAM_DELIVERY_MODE).strip().lower()

    async def send_message(
        self,
        *,
        chat_id: str,
        text: str,
        reply_to_message_id: str | None = None,
    ) -> TelegramDeliveryResult:
        if self.delivery_mode == "disabled":
            return TelegramDeliveryResult(
                status="disabled",
                detail="Entrega Telegram desabilitada por TELEGRAM_DELIVERY_MODE=disabled.",
            )

        if self.delivery_mode == "dry_run":
            return TelegramDeliveryResult(
                status="dry_run",
                external_message_id=reply_to_message_id or "",
                detail="Entrega Telegram simulada com sucesso em modo dry_run.",
            )

        if not self.bot_token:
            raise TelegramDeliveryError(
                "TELEGRAM_BOT_TOKEN obrigatório para TELEGRAM_DELIVERY_MODE=api."
            )

        payload: dict[str, int | str] = {
            "chat_id": self._coerce_telegram_id(chat_id),
            "text": text,
        }
        if reply_to_message_id:
            payload["reply_to_message_id"] = self._coerce_telegram_id(reply_to_message_id)

        url = f"{self.api_base_url}/bot{self.bot_token}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise TelegramDeliveryError(f"Falha ao enviar resposta ao Telegram: {exc}") from exc

        body = response.json()
        if not body.get("ok"):
            description = str(body.get("description", "Telegram retornou erro na entrega."))
            raise TelegramDeliveryError(description)

        result = body.get("result", {})
        return TelegramDeliveryResult(
            status="sent",
            external_message_id=str(result.get("message_id", "")).strip(),
            detail="Resposta entregue ao Telegram com sucesso.",
        )

    def _coerce_telegram_id(self, value: str) -> int | str:
        normalized = str(value).strip()
        numeric = normalized.lstrip("-")
        if numeric.isdigit():
            return int(normalized)
        return normalized


class TelegramService:
    def __init__(
        self,
        *,
        chat_service: ChatService | None = None,
        audit_repository: FileAuditRepository | None = None,
        bot_client: TelegramBotClient | None = None,
        default_tenant_id: str | None = None,
        chat_tenant_map: dict[str, str] | None = None,
    ) -> None:
        self.chat_service = chat_service or ChatService()
        self.audit_repository = audit_repository or self.chat_service.audit_repository
        self.bot_client = bot_client or TelegramBotClient()
        self.default_tenant_id = (
            (default_tenant_id if default_tenant_id is not None else settings.TELEGRAM_DEFAULT_TENANT_ID)
            .strip()
        )
        self.chat_tenant_map = {
            str(key).strip(): str(value).strip()
            for key, value in (
                chat_tenant_map if chat_tenant_map is not None else settings.TELEGRAM_CHAT_TENANT_MAP
            ).items()
            if str(key).strip() and str(value).strip()
        }

    async def handle_update(self, update: TelegramWebhookRequest) -> TelegramWebhookResponse:
        message = self._resolve_supported_message(update)
        if message is None or not message.text:
            return TelegramWebhookResponse(
                status="ignored",
                update_id=update.update_id,
                chat_id=message.chat.id if message else None,
                inbound_message_id=message.message_id if message else None,
                outbound_status="ignored",
                detail="Update ignorado porque nao contem mensagem de texto suportada.",
            )

        tenant_id = self._resolve_tenant(message.chat.id)
        request_id = str(uuid4())
        session_id = self._build_session_id(message.chat.id)
        audit_context = self._build_audit_context(update, message)

        self._append_event(
            request_id=request_id,
            tenant_id=tenant_id,
            session_id=session_id,
            event_type="telegram_update_received",
            payload={
                **audit_context,
                "text": message.text,
            },
        )

        set_tenant(tenant_id)
        try:
            chat_response = await self.chat_service.process(
                ChatRequest(
                    tenant_id=tenant_id,
                    session_id=session_id,
                    message=message.text,
                    channel="telegram",
                ),
                request_id=request_id,
                session_id=session_id,
                audit_context=audit_context,
            )
        finally:
            clear_tenant()

        try:
            delivery = await self.bot_client.send_message(
                chat_id=message.chat.id,
                text=chat_response.message,
                reply_to_message_id=message.message_id,
            )
        except TelegramDeliveryError as exc:
            self._append_event(
                request_id=request_id,
                tenant_id=tenant_id,
                session_id=session_id,
                event_type="telegram_message_delivery_failed",
                payload={
                    **audit_context,
                    "delivery_status": "failed",
                    "detail": str(exc),
                },
            )
            raise

        self._append_event(
            request_id=request_id,
            tenant_id=tenant_id,
            session_id=session_id,
            event_type="telegram_message_delivery",
            payload={
                **audit_context,
                "delivery_status": delivery.status,
                "external_message_id": delivery.external_message_id,
                "detail": delivery.detail,
            },
        )

        return TelegramWebhookResponse(
            status="processed",
            request_id=request_id,
            tenant_id=tenant_id,
            session_id=session_id,
            update_id=update.update_id,
            chat_id=message.chat.id,
            inbound_message_id=message.message_id,
            outbound_status=delivery.status,
            detail=delivery.detail,
        )

    def _resolve_supported_message(self, update: TelegramWebhookRequest) -> TelegramMessage | None:
        return update.message or update.edited_message

    def _resolve_tenant(self, chat_id: str) -> str:
        normalized_chat_id = str(chat_id).strip()
        if normalized_chat_id in self.chat_tenant_map:
            return self.chat_tenant_map[normalized_chat_id]
        if self.default_tenant_id:
            return self.default_tenant_id
        raise TelegramTenantResolutionError(
            "tenant_id nao resolvido para o chat do Telegram. Configure TELEGRAM_DEFAULT_TENANT_ID ou TELEGRAM_CHAT_TENANT_MAP."
        )

    def _build_session_id(self, chat_id: str) -> str:
        return f"telegram-{str(chat_id).strip()}"

    def _build_audit_context(
        self,
        update: TelegramWebhookRequest,
        message: TelegramMessage,
    ) -> dict[str, str]:
        sender = message.from_user
        context = {
            "channel": "telegram",
            "telegram_update_id": update.update_id,
            "telegram_chat_id": message.chat.id,
            "telegram_message_id": message.message_id,
            "telegram_chat_type": message.chat.type,
        }
        if sender is not None:
            if sender.username:
                context["telegram_username"] = sender.username
            if sender.first_name:
                context["telegram_first_name"] = sender.first_name
            context["telegram_user_id"] = sender.id
        return context

    def _append_event(
        self,
        *,
        request_id: str,
        tenant_id: str,
        session_id: str,
        event_type: str,
        payload: dict[str, str],
    ) -> None:
        normalized_payload = {
            str(key).strip(): str(value).strip()
            for key, value in payload.items()
            if str(key).strip() and str(value).strip()
        }
        self.audit_repository.append_event(
            AuditEventRecord(
                request_id=request_id,
                tenant_id=tenant_id,
                session_id=session_id,
                channel="telegram",
                event_type=event_type,
                payload=normalized_payload,
            )
        )
