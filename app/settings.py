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
    DATA_DIR: str = "data/runtime"
    KNOWLEDGE_BASE_DIR: str = "data/knowledge_base"
    CHROMA_DIR: str = "data/chroma"
    CHROMA_COLLECTION_PREFIX: str = "chat_pref_docs"
    CHROMA_LEGACY_COLLECTION_PREFIXES: list[str] = Field(default_factory=lambda: ["chat_pref"])
    WEBHOOK_PAGE_TENANT_MAP: dict[str, str] = Field(default_factory=dict)
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    TELEGRAM_API_BASE_URL: str = "https://api.telegram.org"
    TELEGRAM_DEFAULT_TENANT_ID: str = ""
    TELEGRAM_CHAT_TENANT_MAP: dict[str, str] = Field(default_factory=dict)
    TELEGRAM_DELIVERY_MODE: str = "dry_run"
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

    @field_validator(
        "WEBHOOK_PAGE_TENANT_MAP",
        "TELEGRAM_CHAT_TENANT_MAP",
        mode="before",
    )
    @classmethod
    def parse_string_dict(cls, value: Any) -> dict[str, str]:
        if isinstance(value, dict):
            return {
                str(key).strip(): str(item).strip()
                for key, item in value.items()
                if str(key).strip() and str(item).strip()
            }
        if value is None:
            return {}
        text = str(value).strip()
        if not text:
            return {}
        if text.startswith("{"):
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("Valor JSON deve ser um objeto.")
            return {
                str(key).strip(): str(item).strip()
                for key, item in parsed.items()
                if str(key).strip() and str(item).strip()
            }

        pairs: dict[str, str] = {}
        for chunk in text.split(","):
            key, separator, item = chunk.partition("=")
            if not separator:
                raise ValueError("WEBHOOK_PAGE_TENANT_MAP deve usar o formato page_id=tenant_id.")
            normalized_key = key.strip()
            normalized_item = item.strip()
            if normalized_key and normalized_item:
                pairs[normalized_key] = normalized_item
        return pairs

    @field_validator("TELEGRAM_BOT_TOKEN", "TELEGRAM_WEBHOOK_SECRET", "TELEGRAM_DEFAULT_TENANT_ID", mode="before")
    @classmethod
    def parse_optional_string(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("TELEGRAM_DELIVERY_MODE", mode="before")
    @classmethod
    def parse_telegram_delivery_mode(cls, value: Any) -> str:
        normalized = str(value or "").strip().lower()
        if not normalized:
            return "dry_run"
        if normalized not in {"api", "dry_run", "disabled"}:
            raise ValueError("TELEGRAM_DELIVERY_MODE deve ser api, dry_run ou disabled.")
        return normalized

    @field_validator(
        "CORS_ORIGINS",
        "ALLOWED_HOSTS",
        "CHROMA_LEGACY_COLLECTION_PREFIXES",
        mode="before",
    )
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
