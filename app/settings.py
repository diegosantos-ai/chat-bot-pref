"""
Configurações — Pilot Atendimento MVE
======================================
Versão: v1.1
Escopo: MVE_PILOT
Atualizado: Suporte a Instagram/Facebook

Todas as configurações sensíveis devem vir do arquivo .env
ou do AWS Secrets Manager (se USE_SECRETS_MANAGER=True)
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do ambiente."""

    # ========================================
    # APP
    # ========================================
    APP_NAME: str = "Pilot Atendimento API"
    ENV: str = "dev"
    VERSION: str = "0.0.1"
    DEBUG: bool = False
    BASE_DIR: str = "."
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # ========================================
    # LLM — Google Gemini 2.0 Flash
    # ========================================
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_MAX_TOKENS: int = 1024
    GEMINI_TEMPERATURE: float = 0.3  # Baixo para respostas consistentes

    # ========================================
    # DATABASE - PostgreSQL
    # ========================================
    DATABASE_URL: str = "postgresql://localhost:5432/pilot_atendimento"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    USER_HASH_SALT: str = ""

    # ========================================
    # VECTOR STORE — ChromaDB
    # ========================================
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # ========================================
    # RAG
    # ========================================
    RAG_BASE_ID: str = "BA-RAG-PILOTO-2026.01.v1"
    RAG_COLLECTION_NAME: str = "rag_ba_rag_piloto_2026_01_v1"
    RAG_TOP_K: int = 5  # Reduzido para diminuir redundância
    RAG_MIN_SCORE: float = 0.30  # Ajustado para recuperar mais resultados relevantes

    # ========================================
    # EMBEDDING PROVIDERS
    # ========================================
    # Opções: "default" | "gemini" | "openai" | "qwen"
    # Todos os provedores externos usam o OpenRouter com OPENROUTER_API_KEY.
    EMBEDDING_PROVIDER: str = "default"
    OPENROUTER_API_KEY: str = ""      # Para provedores gemini, openai e qwen via OpenRouter
    # Override global opcional para facilitar experimentos sem alteração de código.
    EMBEDDING_MODEL_OVERRIDE: str = ""
    # Overrides por provedor (mantem defaults atuais se vazio).
    EMBEDDING_MODEL_GEMINI: str = "google/gemini-embedding-001"
    EMBEDDING_MODEL_OPENAI: str = "openai/text-embedding-3-large"
    EMBEDDING_MODEL_QWEN: str = "qwen/qwen3-embedding-8b"
    # Robustez/performance de requisições de embedding via OpenRouter.
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_REQUEST_TIMEOUT_SECONDS: float = 60.0
    EMBEDDING_MAX_RETRIES: int = 3

    # ========================================
    # POLICY GUARD
    # ========================================
    POLICY_MAX_MESSAGE_LENGTH: int = 2000
    POLICY_BLOCKED_PATTERNS: str = ""  # Padrões regex separados por |
    POLICY_PUBLIC_COMMENT_MAX_LENGTH: int = 280  # Limite para comentários públicos

    # ========================================
    # LOGGING / OBSERVABILITY
    # ========================================
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True
    METRICS_STATSD_ENABLED: bool = False
    METRICS_STATSD_HOST: str = "127.0.0.1"
    METRICS_STATSD_PORT: int = 8125
    METRICS_STATSD_PREFIX: str = "terezia"

    # ========================================
    # META API (Instagram/Facebook)
    # ========================================
    # Access Tokens
    META_ACCESS_TOKEN_INSTAGRAM: str = ""
    META_ACCESS_TOKEN_FACEBOOK: str = ""
    # Page IDs
    META_PAGE_ID_FACEBOOK: str = ""
    META_PAGE_ID_INSTAGRAM: str = ""  # Instagram Business Account ID
    # App Secrets (para verificação de webhook)
    META_APP_SECRET_FACEBOOK: str = ""
    META_APP_SECRET_INSTAGRAM: str = ""
    # Legacy (retrocompatibilidade - usar apenas se as novas não estiverem configuradas)
    META_PAGE_ID: str = ""
    META_APP_SECRET: str = ""
    # Webhook Verify Token
    META_WEBHOOK_VERIFY_TOKEN: str = "verify_token_webhook"
    META_WEBHOOK_VERIFY_TOKEN_FACEBOOK: str = ""
    META_WEBHOOK_VERIFY_TOKEN_INSTAGRAM: str = ""
    META_API_VERSION: str = "v19.0"

    # ========================================
    # RESPONSE FORMATTING
    # ========================================
    RESPONSE_MODE_INBOX_MAX_LENGTH: int = 1000
    RESPONSE_MODE_PUBLIC_MAX_LENGTH: int = 280

    # ========================================
    # SECURITY - CORS e Rate Limiting
    # ========================================
    CORS_ORIGINS: list[str] = ["*"]  # Em produção, especifique domínios permitidos
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 30  # Limite padrão por IP
    RATE_LIMIT_WEBHOOK_PER_MINUTE: int = 60  # Limite específico para webhook (Meta)

    # ========================================
    # SECRETS MANAGER (AWS)
    # ========================================
    USE_SECRETS_MANAGER: bool = False  # Se True, carrega secrets do AWS Secrets Manager
    AWS_REGION: str = "sa-east-1"
    AWS_SECRET_NAME: str = "terezia/prod"

    # ========================================
    # ADMIN API
    # ========================================
    ADMIN_API_KEY: str = ""  # Se vazio, endpoints admin bloqueados

    # ========================================
    # GOOGLE DRIVE & SMTP (FALLBACK)
    # ========================================
    GOOGLE_APPLICATION_CREDENTIALS: str = "service_account.json"
    GOOGLE_DRIVE_FOLDER_ID: str = ""

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    MANAGER_EMAILS: str = ""  # Lista separada por vírgulas

    # ========================================
    # DEPLOY WEBHOOK
    # ========================================
    DEPLOY_WEBHOOK_TOKEN: str = ""  # Token para autorizar deploy via webhook

    # ========================================
    # FALLBACK HYBRID (Web Scraping)
    # ========================================
    FALLBACK_HYBRID_ENABLED: bool = True
    FALLBACK_CONFIDENCE_THRESHOLD: float = 0.7
    FALLBACK_TARGET_URL: str = "https://santatereza.pr.gov.br/noticias"
    FALLBACK_WEB_TIMEOUT_SECONDS: int = 5
    FALLBACK_WEB_MIN_SCORE: float = 0.35

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


def _load_settings_with_secrets() -> Settings:
    """
    Carrega settings do .env e opcionalmente sobrescreve com AWS Secrets Manager.

    Estratégia:
    1. Carrega tudo do .env (padrão)
    2. Se USE_SECRETS_MANAGER=True, busca secrets do AWS e sobrescreve valores existentes
    """
    settings_instance = Settings()

    # Sobrescreve com AWS Secrets Manager se habilitado
    if settings_instance.USE_SECRETS_MANAGER:
        try:
            from app.secrets import get_secrets, update_settings_from_secrets

            secrets = get_secrets(
                secret_name=settings_instance.AWS_SECRET_NAME,
                region=settings_instance.AWS_REGION,
            )

            if secrets:
                update_settings_from_secrets(settings_instance, secrets)
        except ImportError:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning("boto3 não instalado. Usando apenas .env para secrets.")
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao carregar secrets do AWS: {e}")

    return settings_instance


settings = _load_settings_with_secrets()
# Force reload for .env update


def get_effective_rag_config() -> dict:
    """
    Retorna a configuração efetiva do RAG.
    Se houver admin_config.json, usa esses valores.
    Caso contrário, usa os valores padrão das settings.
    """
    from pathlib import Path
    import json

    config_path = Path(settings.BASE_DIR) / "admin_config.json"

    defaults = {
        "min_score": settings.RAG_MIN_SCORE,
        "top_k": settings.RAG_TOP_K,
        "boost_enabled": True,
        "boost_amount": 0.2,
        "model": settings.GEMINI_MODEL,
        "model_temperature": settings.GEMINI_TEMPERATURE,
        "model_max_tokens": settings.GEMINI_MAX_TOKENS,
    }

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                admin_config = json.load(f)
                rag_config = admin_config.get("rag_config", {})
                # Merge with defaults
                return {**defaults, **rag_config}
        except Exception:
            pass

    return defaults
