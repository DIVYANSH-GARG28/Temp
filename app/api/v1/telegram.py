from typing import Optional
from fastapi import APIRouter, Depends, Header, status
from app.api.deps import get_current_user
from app.schemas.telegram import (
    TelegramLinkInitiateResponse,
    TelegramWebhookResponse,
    TelegramWebhookUpdate,
)
from app.services.telegram_service import telegram_service

router = APIRouter(tags=["Telegram Integration"])

@router.post("/telegram/link/initiate", response_model=TelegramLinkInitiateResponse, status_code=status.HTTP_200_OK)
async def initiate_telegram_link(current_user: dict = Depends(get_current_user)):
    """Generate a single-use, time-limited linking token for connecting Telegram."""
    return await telegram_service.initiate_link(current_user["id"])

@router.post("/webhooks/telegram", response_model=TelegramWebhookResponse, status_code=status.HTTP_200_OK)
async def telegram_webhook(
    update: TelegramWebhookUpdate,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None, alias="X-Telegram-Bot-Api-Secret-Token"),
):
    """Receive Telegram bot updates (linking commands, mentor accept/decline callbacks)."""
    return await telegram_service.handle_webhook(
        update=update,
        secret_token=x_telegram_bot_api_secret_token,
    )
