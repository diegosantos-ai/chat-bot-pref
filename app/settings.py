import json
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Chat Pref API"
    VERSION: str = "0.1.0"
    ENV: str = "dev"
    DEBUG: bool = False
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:8000",
        ]
    )
    ALLOWED_HOSTS: list[str] = Field(
        default_factory=lambda: [
            "localhost",
            "127.0.0.1",
            "testserver",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on", "debug", "dev"}:
            return True
        if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
            return False
        raise ValueError("DEBUG deve ser booleano ou um alias reconhecido.")

    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_string_list(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return value
        if value is None:
            return []
        text = str(value).strip()
        if not text:
            return []
        if text.startswith("["):
            parsed = json.loads(text)
            if not isinstance(parsed, list):
                raise ValueError("Valor JSON deve ser uma lista.")
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in text.split(",") if item.strip()]


settings = Settings()
