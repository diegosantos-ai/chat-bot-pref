"""
Tenant Config — Nexo Basis Governador SaaS
==========================================
Carrega as configurações de identidade e credenciais do tenant ativo.

Responsabilidades:
- Buscar o perfil do tenant (bot_name, client_name, contact_info) da tabela `tenants`.
- Buscar as credenciais Meta (access_token por canal) da tabela `tenant_credentials`.
- Expor um cache em memória com TTL para não bater no banco a cada mensagem.
- Fornecer um dict `prompt_vars` pronto para inject em `get_prompt(variables=...)`.

Uso:
    from app.tenant_config import get_tenant_config, get_prompt_vars

    config = await get_tenant_config()   # usa tenant_context.require_tenant()
    vars = config.prompt_vars           # {bot_name, client_name, ...}
    token = config.meta_access_token(channel)
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional, Dict

import asyncpg

from app.settings import settings
from app import tenant_context

logger = logging.getLogger(__name__)

# TTL do cache: 10 minutos (suficiente para não derrubar o banco, curto para propagar mudanças)
_CACHE_TTL = 600
_config_cache: Dict[str, tuple["TenantConfig", float]] = {}


@dataclass
class TenantConfig:
    """Configuração completa de um tenant."""
    tenant_id: str
    bot_name: str
    client_name: str
    fallback_url: str
    contact_phone: str
    contact_address: str
    support_email: str

    # Credenciais Meta por canal   {canal: access_token}
    meta_tokens: Dict[str, str] = field(default_factory=dict)
    # ID da page Instagram
    meta_ig_page_id: Optional[str] = None
    # ID da page Facebook
    meta_fb_page_id: Optional[str] = None

    @property
    def prompt_vars(self) -> Dict[str, str]:
        """Variáveis prontas para substituição nos prompts."""
        return {
            "bot_name": self.bot_name,
            "client_name": self.client_name,
            "contact_phone": self.contact_phone,
            "contact_address": self.contact_address,
            "support_email": self.support_email,
            "fallback_url": self.fallback_url,
        }

    def meta_access_token(self, channel: str) -> Optional[str]:
        """
        Retorna o access token Meta para o canal especificado.

        Args:
            channel: valor do enum Channel (ex: 'instagram_dm', 'facebook_dm')
        """
        # Normaliza: instagram_dm e instagram_comment compartilham o mesmo token IG
        if "instagram" in channel.lower():
            return self.meta_tokens.get("instagram") or settings.META_ACCESS_TOKEN_INSTAGRAM
        if "facebook" in channel.lower():
            return self.meta_tokens.get("facebook") or settings.META_ACCESS_TOKEN_FACEBOOK
        return None


async def _load_from_db(tenant_id: str, pool: asyncpg.Pool) -> Optional[TenantConfig]:
    """Carrega o perfil e credenciais do tenant a partir do banco."""
    tenant_row = await pool.fetchrow(
        """
        SELECT bot_name, client_name, fallback_url,
               contact_phone, contact_address, support_email
        FROM tenants
        WHERE tenant_id = $1 AND is_active = TRUE
        """,
        tenant_id,
    )
    if not tenant_row:
        logger.warning("TenantConfig: tenant_id=%s não encontrado ou inativo", tenant_id)
        return None

    # Busca tokens Meta
    creds_rows = await pool.fetch(
        """
        SELECT meta_ig_page_id, meta_fb_page_id,
               meta_access_token_ig, meta_access_token_fb
        FROM tenant_credentials
        WHERE tenant_id = $1
        LIMIT 1
        """,
        tenant_id,
    )

    meta_tokens: Dict[str, str] = {}
    meta_ig_page_id: Optional[str] = None
    meta_fb_page_id: Optional[str] = None

    if creds_rows:
        cred = creds_rows[0]
        if cred["meta_access_token_ig"]:
            meta_tokens["instagram"] = cred["meta_access_token_ig"]
        if cred["meta_access_token_fb"]:
            meta_tokens["facebook"] = cred["meta_access_token_fb"]
        meta_ig_page_id = cred["meta_ig_page_id"]
        meta_fb_page_id = cred["meta_fb_page_id"]

    return TenantConfig(
        tenant_id=tenant_id,
        bot_name=tenant_row["bot_name"] or "Assistente Virtual",
        client_name=tenant_row["client_name"] or "Prefeitura",
        fallback_url=tenant_row["fallback_url"] or "",
        contact_phone=tenant_row["contact_phone"] or "",
        contact_address=tenant_row["contact_address"] or "",
        support_email=tenant_row["support_email"] or "",
        meta_tokens=meta_tokens,
        meta_ig_page_id=meta_ig_page_id,
        meta_fb_page_id=meta_fb_page_id,
    )


async def get_tenant_config(pool: Optional[asyncpg.Pool] = None) -> TenantConfig:
    """
    Retorna a configuração do tenant ativo (contextvars).

    Args:
        pool: Pool asyncpg. Se None, cria um pool temporário (menos eficiente).
              Prefira passar o pool do webhook handler.

    Returns:
        TenantConfig populado com dados do banco.

    Raises:
        ValueError: Se não há tenant ativo no contexto.
        RuntimeError: Se o tenant não existe no banco.
    """
    tenant_id = tenant_context.require_tenant()

    # Cache hit
    cached = _config_cache.get(tenant_id)
    if cached:
        config, expires_at = cached
        if time.monotonic() < expires_at:
            return config

    # DB lookup
    if pool is None:
        pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=1,
            max_size=3,
        )

    config = await _load_from_db(tenant_id, pool)
    if config is None:
        raise RuntimeError(f"Tenant '{tenant_id}' inativo ou não encontrado no banco.")

    _config_cache[tenant_id] = (config, time.monotonic() + _CACHE_TTL)
    logger.info("TenantConfig: carregado tenant_id=%s bot=%s", tenant_id, config.bot_name)
    return config


def invalidate_tenant_config(tenant_id: str) -> None:
    """Remove do cache (use após mudar configuração do tenant)."""
    _config_cache.pop(tenant_id, None)


async def get_prompt_vars(pool: Optional[asyncpg.Pool] = None) -> Dict[str, str]:
    """
    Atalho: retorna o dict de variáveis pronto para `get_prompt(variables=...)`.
    Retorna vars padrão vazias se não houver tenant ativo (modo dev/sem contexto).
    """
    try:
        config = await get_tenant_config(pool=pool)
        return config.prompt_vars
    except (ValueError, RuntimeError) as e:
        logger.warning("get_prompt_vars: sem tenant ativo, usando vars padrão (%s)", e)
        return {
            "bot_name": "Assistente Virtual",
            "client_name": "Prefeitura",
            "contact_phone": "",
            "contact_address": "",
            "support_email": "",
            "fallback_url": "",
        }
