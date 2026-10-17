from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class TelegramLinkInitiateResponse(BaseModel):
    linking_token: str
    bot_username: str
    deep_link: str
    expires_at: datetime
    instructions: str = "Click the link or send /start <linking_token> to the Telegram bot to connect your account."

class TelegramWebhookUpdate(BaseModel):
    update_id: int = Field(..., description="Unique update identifier from Telegram")
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None

class TelegramWebhookResponse(BaseModel):
    ok: bool = True
    processed: bool = True
    action: Optional[str] = None
    message: Optional[str] = None
