from fastapi import APIRouter, Header, HTTPException

from app.contracts.dto import TelegramWebhookRequest, TelegramWebhookResponse
from app.services.telegram_service import (
    TelegramDeliveryError,
    TelegramService,
    TelegramTenantResolutionError,
)
from app.settings import settings

router = APIRouter(prefix="/api/telegram", tags=["Telegram"])
telegram_service = TelegramService()


@router.post("/webhook", response_model=TelegramWebhookResponse)
async def telegram_webhook(
    update: TelegramWebhookRequest,
    telegram_secret: str | None = Header(
        default=None,
        alias="X-Telegram-Bot-Api-Secret-Token",
    ),
) -> TelegramWebhookResponse:
    if settings.TELEGRAM_WEBHOOK_SECRET and telegram_secret != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid telegram secret")

    try:
        return await telegram_service.handle_update(update)
    except TelegramTenantResolutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TelegramDeliveryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
