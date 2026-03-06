"""Admin API — Health checks, metrics and system info."""
import os
import time
import sys
from fastapi import APIRouter
import httpx
import asyncpg
from api import get_conn

router = APIRouter(prefix="/api/admin", tags=["Health"])

DATABASE_URL = os.getenv("DATABASE_URL", "")
CHROMA_URL   = os.getenv("CHROMA_URL", "http://localhost:8000")
REDIS_URL    = os.getenv("REDIS_URL", "redis://localhost:6379")


async def _check_postgres() -> dict:
    start = time.monotonic()
    try:
        conn = await asyncpg.connect(DATABASE_URL, timeout=5)
        await conn.fetchval("SELECT 1")
        await conn.close()
        return {"status": "ONLINE", "latency_ms": round((time.monotonic() - start) * 1000, 1)}
    except Exception as e:
        return {"status": "OFFLINE", "error": str(e)[:80]}


async def _check_chroma() -> dict:
    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{CHROMA_URL}/api/v1/heartbeat")
        status = "ONLINE" if r.status_code == 200 else "DEGRADED"
        return {"status": status, "latency_ms": round((time.monotonic() - start) * 1000, 1)}
    except Exception as e:
        return {"status": "OFFLINE", "error": str(e)[:80]}


async def _check_redis() -> dict:
    start = time.monotonic()
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(REDIS_URL, socket_timeout=4)
        await r.ping()
        await r.aclose()
        return {"status": "ONLINE", "latency_ms": round((time.monotonic() - start) * 1000, 1)}
    except Exception as e:
        return {"status": "OFFLINE", "error": str(e)[:80]}


@router.get("/health/details")
async def health_details():
    import asyncio
    pg, chroma, redis = await asyncio.gather(
        _check_postgres(), _check_chroma(), _check_redis()
    )
    return {"postgres": pg, "chromadb": chroma, "redis": redis}


@router.get("/metrics")
async def metrics():
    conn = await get_conn()
    try:
        rows = await conn.fetch(
            """SELECT tenant_id, COUNT(*) as msgs_24h
               FROM audit_logs
               WHERE created_at >= NOW() - INTERVAL '24 hours'
               GROUP BY tenant_id
               ORDER BY msgs_24h DESC
               LIMIT 20"""
        )
        return {"messages_24h": [dict(r) for r in rows]}
    except Exception:
        return {"messages_24h": []}
    finally:
        await conn.close()


@router.get("/system")
async def system_info():
    tenant_count = contract_count = "—"
    try:
        from api import get_db
        async with get_db() as conn:
            tenant_count = await conn.fetchval(
                "SELECT COUNT(*) FROM tenants WHERE is_active = true"
            ) or 0
            contract_count = await conn.fetchval(
                "SELECT COUNT(*) FROM contracts WHERE status = 'active'"
            ) or 0
    except Exception:
        pass

    admin_key = os.getenv("ADMIN_API_KEY", "")
    masked_key = f"{'*' * (len(admin_key) - 4)}{admin_key[-4:]}" if len(admin_key) > 4 else "****"

    return {
        "api_version": "1.0.0",
        "python_version": sys.version.split(" ")[0],
        "tenants_active": tenant_count,
        "contracts_active": contract_count,
        "admin_key_hint": masked_key,
        "database_url_hint": DATABASE_URL[:30] + "..." if DATABASE_URL else "not set",
    }

