from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # MongoDB Connection
    MONGODB_URI: str = "mongodb://127.0.0.1:27017"
    MONGODB_DATABASE: str = "connected"

    # Security & Authentication
    JWT_SECRET_KEY: str = "development-secret-key-must-be-changed-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None
    TELEGRAM_BOT_USERNAME: str = "connectED_bot"

    # External services & Webhooks
    N8N_WEBHOOK_URL: Optional[str] = None
    N8N_WEBHOOK_SECRET: Optional[str] = None
    N8N_WEBHOOK_REQUIRE_AUTH: bool = False
    OUTBOX_MAX_RETRIES: int = 3
    OUTBOX_TIMEOUT_SECONDS: float = 5.0
    OUTBOX_LEASE_SECONDS: int = 30
    AI_SERVICE_URL: Optional[str] = None
    GRAPH_SERVICE_URL: Optional[str] = None

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v

settings = Settings()
