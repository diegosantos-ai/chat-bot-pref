"""
Tenant Resolver — Nexo Basis Governador SaaS
=============================================
Resolve um Meta Page ID para um tenant_id ativo.

Estratégia:
1. Verifica cache LRU em memória (rápido, sem I/O).
2. Em caso de miss, faz lookup no PostgreSQL via `tenant_credentials`.
3. Retorna None se a página não tiver Tenant cadastrado (→ 401 no webhook).

O cache usa TTL de 5 minutos para garantir que desativações de tenant
sejam propagadas sem reiniciar o serviço.
"""

import logging
import time
from typing import Optional

import asyncpg

from app.settings import settings

logger = logging.getLogger(__name__)

# ---- LRU Cache simples com TTL ----
# {page_id: (tenant_id, expire_at_epoch)}
_cache: dict[str, tuple[str, float]] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutos


def _cache_get(page_id: str) -> Optional[str]:
    """Retorna tenant_id do cache se válido."""
    entry = _cache.get(page_id)
    if entry is None:
        return None
    tenant_id, expires_at = entry
    if time.monotonic() > expires_at:
        del _cache[page_id]
        return None
    return tenant_id


def _cache_set(page_id: str, tenant_id: str) -> None:
    """Armazena o mapeamento no cache com TTL."""
    _cache[page_id] = (tenant_id, time.monotonic() + _CACHE_TTL_SECONDS)


def _cache_invalidate(page_id: str) -> None:
    """Remove uma entrada do cache (ex: após desativação de tenant)."""
    _cache.pop(page_id, None)


# ---- Lookup no banco ----

async def _lookup_tenant_in_db(page_id: str, pool: asyncpg.Pool) -> Optional[str]:
    """
    Busca o tenant_id na tabela `tenant_credentials` pelo Meta Page ID.
    Verifica apenas tenants ativos.
    """
    query = """
        SELECT tc.tenant_id
        FROM tenant_credentials tc
        JOIN tenants t ON t.tenant_id = tc.tenant_id
        WHERE (tc.meta_page_id = $1 OR tc.meta_ig_page_id = $1)
          AND t.is_active = TRUE
        LIMIT 1
    """
    row = await pool.fetchrow(query, page_id)
    return row["tenant_id"] if row else None


# ---- Resolver público ----

async def resolve_tenant(page_id: str, pool: asyncpg.Pool) -> Optional[str]:
    """
    Resolve um Meta Page ID para um tenant_id ativo.

    Args:
        page_id: ID da página do Meta (entrada de cada entry no webhook).
        pool: Pool asyncpg compartilhado.

    Returns:
        tenant_id string se encontrado e ativo, None caso contrário.
    """
    # 1. Cache hit
    cached = _cache_get(page_id)
    if cached is not None:
        logger.debug("TenantResolver: cache hit page_id=%s → %s", page_id, cached)
        return cached

    # 2. DB lookup
    tenant_id = await _lookup_tenant_in_db(page_id, pool)

    if tenant_id:
        _cache_set(page_id, tenant_id)
        logger.info("TenantResolver: DB hit page_id=%s → %s", page_id, tenant_id)
    else:
        logger.warning("TenantResolver: page_id=%s não tem tenant cadastrado", page_id)

    return tenant_id
