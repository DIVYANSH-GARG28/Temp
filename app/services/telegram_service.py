import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from app.core.config import settings
from app.core.exceptions import AppException
from app.repositories.telegram_repository import telegram_repo
from app.repositories.user_repository import user_repo
from app.schemas.telegram import (
    TelegramLinkInitiateResponse,
    TelegramWebhookResponse,
    TelegramWebhookUpdate,
)
from app.services.mentorship_service import mentorship_service

logger = logging.getLogger(__name__)

class TelegramService:
    async def initiate_link(self, user_id: str) -> TelegramLinkInitiateResponse:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        await telegram_repo.create_linking_token(user_id, token, expires_at)

        bot_username = settings.TELEGRAM_BOT_USERNAME
        deep_link = f"https://t.me/{bot_username}?start=link_{token}"

        return TelegramLinkInitiateResponse(
            linking_token=token,
            bot_username=bot_username,
            deep_link=deep_link,
            expires_at=expires_at,
        )

    async def handle_webhook(
        self,
        update: TelegramWebhookUpdate,
        secret_token: Optional[str] = None,
    ) -> TelegramWebhookResponse:
        # Validate secret header if configured
        if settings.TELEGRAM_WEBHOOK_SECRET:
            if secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
                logger.warning("Invalid Telegram webhook secret token received.")
                raise AppException(
                    code="UNAUTHORIZED_WEBHOOK",
                    message="Invalid webhook secret token header.",
                    status_code=401,
                )

        # Deduplicate update_id
        is_new = await telegram_repo.record_update(update.update_id)
        if not is_new:
            logger.info("Telegram update %d is a duplicate. Skipping.", update.update_id)
            return TelegramWebhookResponse(ok=True, processed=False, message="Duplicate update ignored")

        # 1. Process message commands (account linking)
        if update.message:
            text = update.message.get("text", "")
            chat = update.message.get("chat", {})
            chat_id = str(chat.get("id"))

            if text.startswith("/start link_"):
                token = text.replace("/start link_", "").strip()
                record = await telegram_repo.find_and_consume_token(token)
                if not record:
                    return TelegramWebhookResponse(
                        ok=True,
                        processed=True,
                        action="link_account_failed",
                        message="Linking token is invalid, expired, or already used.",
                    )
                
                user_id = record["user_id"]
                await user_repo.update_telegram_chat_id(user_id, chat_id)
                logger.info("Successfully linked Telegram chat_id %s to user %s", chat_id, user_id)
                return TelegramWebhookResponse(
                    ok=True,
                    processed=True,
                    action="link_account_success",
                    message="Account linked successfully with Telegram.",
                )

        # 2. Process callback queries (mentor accept / decline)
        if update.callback_query:
            callback_data = update.callback_query.get("data", "")
            from_user = update.callback_query.get("from", {})
            from_chat_id = str(from_user.get("id"))

            # Format: 'action:accept:<request_id>' or 'action:decline:<request_id>'
            parts = callback_data.split(":")
            if len(parts) == 3 and parts[0] == "action":
                action = parts[1]
                req_id = parts[2]

                # Identify user by telegram_chat_id
                user = await user_repo.get_by_telegram_chat_id(from_chat_id)
                if not user:
                    return TelegramWebhookResponse(
                        ok=True,
                        processed=True,
                        action="unauthorized_telegram_user",
                        message="Telegram account not linked to any connectED user.",
                    )

                accept = (action == "accept")
                try:
                    await mentorship_service.respond_to_request(
                        mentor_id=user["id"],
                        request_id=req_id,
                        accept=accept,
                    )
                    return TelegramWebhookResponse(
                        ok=True,
                        processed=True,
                        action=f"mentorship_{action}",
                        message=f"Mentorship request successfully {action}ed.",
                    )
                except AppException as exc:
                    return TelegramWebhookResponse(
                        ok=True,
                        processed=True,
                        action=f"mentorship_{action}_error",
                        message=exc.message,
                    )

        return TelegramWebhookResponse(ok=True, processed=True, message="Update handled")

telegram_service = TelegramService()
