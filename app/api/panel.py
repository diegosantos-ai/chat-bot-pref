"""
Panel API — Nexo Prefa Dashboard
=================================
Endpoints internos do painel de controle do tenant.
Prefixo: /api/panel   Tags: Panel
Sem autenticação (dev mode — preparado para X-Admin-Key futuramente).
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4

import asyncpg
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.settings import settings
from app import tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/panel", tags=["Panel"])


# ============================================================
# Helpers
# ============================================================

async def _get_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=1, max_size=3)


def _require_tenant(tenant_id: Optional[str] = None) -> str:
    """Usa tenant_id do query param ou do contextvars."""
    if tenant_id:
        tenant_context.set_tenant(tenant_id)
        return tenant_id
    try:
        return tenant_context.require_tenant()
    except ValueError:
        raise HTTPException(status_code=400, detail="tenant_id obrigatório")


# ============================================================
# Config do Tenant
# ============================================================

class TenantConfigPayload(BaseModel):
    bot_name: str
    client_name: str
    contact_phone: str = ""
    contact_address: str = ""
    support_email: str = ""
    fallback_url: str = ""


@router.get("/config")
async def get_config(tenant_id: str = Query(..., description="ID do tenant")):
    """Retorna configuração atual do tenant."""
    pool = await _get_pool()
    try:
        row = await pool.fetchrow(
            """SELECT bot_name, client_name, contact_phone, contact_address,
                      support_email, fallback_url
               FROM tenants WHERE tenant_id = $1""",
            tenant_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Tenant não encontrado")
        return dict(row)
    finally:
        await pool.close()


@router.put("/config")
async def update_config(tenant_id: str, payload: TenantConfigPayload):
    """Atualiza configuração do tenant."""
    pool = await _get_pool()
    try:
        await pool.execute(
            """UPDATE tenants SET bot_name=$1, client_name=$2, contact_phone=$3,
                                  contact_address=$4, support_email=$5, fallback_url=$6
               WHERE tenant_id=$7""",
            payload.bot_name, payload.client_name, payload.contact_phone,
            payload.contact_address, payload.support_email, payload.fallback_url,
            tenant_id,
        )
        # Invalida cache do TenantConfig
        try:
            from app.tenant_config import invalidate_tenant_config
            invalidate_tenant_config(tenant_id)
        except Exception:
            pass
        return {"status": "ok", "tenant_id": tenant_id}
    finally:
        await pool.close()


# ============================================================
# Logs de conversa
# ============================================================

@router.get("/logs")
async def get_logs(
    tenant_id: str = Query(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    channel: Optional[str] = None,
):
    """Lista conversas auditadas com paginação."""
    pool = await _get_pool()
    try:
        offset = (page - 1) * per_page
        filters = "WHERE tenant_id = $1"
        params = [tenant_id]
        if channel:
            filters += " AND channel = $2"
            params.append(channel)

        rows = await pool.fetch(
            f"""SELECT id, created_at, session_id, channel, surface_type,
                       user_message, bot_response, intent, decision
                FROM audit_logs {filters}
                ORDER BY created_at DESC
                LIMIT {per_page} OFFSET {offset}""",
            *params,
        )
        total = await pool.fetchval(
            f"SELECT COUNT(*) FROM audit_logs {filters}", *params
        )
        return {
            "items": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": max(1, (total + per_page - 1) // per_page),
        }
    except Exception as e:
        logger.error("Erro ao buscar logs: %s", e)
        # Retorna mock se tabela não existir ainda
        return {"items": [], "total": 0, "page": page, "per_page": per_page, "pages": 1}
    finally:
        await pool.close()


# ============================================================
# RAG — ETL Trigger
# ============================================================

# Armazena estado do job em memória (suficiente para dev)
_etl_state: dict = {"status": "IDLE", "log": [], "started_at": None}


@router.post("/rag/trigger")
async def trigger_etl(tenant_id: str, background_tasks: BackgroundTasks):
    """Dispara o ETL RAG para um tenant específico."""
    if _etl_state["status"] == "RUNNING":
        raise HTTPException(status_code=409, detail="ETL já está rodando")

    _etl_state.update({"status": "RUNNING", "log": ["[START] Iniciando ETL..."], "started_at": time.time()})

    async def _run():
        try:
            import subprocess
            import sys
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "scripts/rag_etl_job.py", "--tenant", tenant_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            async for line in proc.stdout:
                _etl_state["log"].append(line.decode().rstrip())
            await proc.wait()
            _etl_state["status"] = "DONE" if proc.returncode == 0 else "ERROR"
            _etl_state["log"].append(f"[END] Código de saída: {proc.returncode}")
        except Exception as e:
            _etl_state["status"] = "ERROR"
            _etl_state["log"].append(f"[ERROR] {e}")

    background_tasks.add_task(_run)
    return {"status": "RUNNING", "message": "ETL iniciado em background"}


@router.get("/rag/status")
async def get_etl_status():
    """Retorna estado atual do ETL job."""
    return _etl_state


# ============================================================
# RAG — Upload de documentos
# ============================================================

@router.post("/rag/upload")
async def upload_doc(tenant_id: str, file: UploadFile = File(...)):
    """
    Recebe um arquivo (PDF/TXT/MD) e registra para ingestão.
    O arquivo é salvo em data/{tenant_id}/uploads/ e pode ser ingerido manualmente.
    """
    allowed = {".pdf", ".txt", ".md", ".docx"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"Formato não suportado: {suffix}")

    upload_dir = Path("data") / tenant_id / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    dest = upload_dir / file.filename
    content = await file.read()
    dest.write_bytes(content)

    logger.info("Upload: tenant=%s file=%s size=%d", tenant_id, file.filename, len(content))
    return {
        "filename": file.filename,
        "size": len(content),
        "path": str(dest),
        "status": "uploaded",
    }


@router.get("/rag/docs")
async def list_docs(tenant_id: str):
    """Lista documentos uploadados para o tenant."""
    upload_dir = Path("data") / tenant_id / "uploads"
    if not upload_dir.exists():
        return {"docs": []}

    docs = []
    for f in sorted(upload_dir.iterdir()):
        if f.is_file():
            stat = f.stat()
            docs.append({
                "filename": f.name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "path": str(f),
            })
    return {"docs": docs, "tenant_id": tenant_id}


# ============================================================
# Health detalhado
# ============================================================

@router.get("/health/details")
async def health_details():
    """Verifica latência real dos três serviços compartilhados."""
    results = {}

    # PostgreSQL
    try:
        t0 = time.monotonic()
        pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL, min_size=1, max_size=1)
        await pool.fetchval("SELECT 1")
        await pool.close()
        results["postgres"] = {"status": "ONLINE", "latency_ms": round((time.monotonic() - t0) * 1000)}
    except Exception as e:
        results["postgres"] = {"status": "OFFLINE", "latency_ms": None, "error": str(e)}

    # ChromaDB
    try:
        import httpx
        t0 = time.monotonic()
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{settings.CHROMA_URL}/api/v1/heartbeat")
        results["chromadb"] = {
            "status": "ONLINE" if r.status_code == 200 else "DEGRADED",
            "latency_ms": round((time.monotonic() - t0) * 1000),
        }
    except Exception as e:
        results["chromadb"] = {"status": "OFFLINE", "latency_ms": None, "error": str(e)}

    # Redis
    try:
        import redis.asyncio as aioredis
        t0 = time.monotonic()
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        results["redis"] = {"status": "ONLINE", "latency_ms": round((time.monotonic() - t0) * 1000)}
    except Exception as e:
        results["redis"] = {"status": "OFFLINE", "latency_ms": None, "error": str(e)}

    return results


# ============================================================
# Tenants disponíveis (para dropdown no painel)
# ============================================================

@router.get("/tenants")
async def list_tenants():
    """Lista todos os tenants ativos para o seletor do painel."""
    pool = await _get_pool()
    try:
        rows = await pool.fetch(
            "SELECT tenant_id, bot_name, client_name FROM tenants WHERE is_active = TRUE ORDER BY client_name"
        )
        return {"tenants": [dict(r) for r in rows]}
    except Exception:
        # Fallback para demo quando banco não está disponível
        return {"tenants": [{"tenant_id": "prefeitura_nova_esperanca", "bot_name": "EsperBot", "client_name": "Prefeitura de Nova Esperança"}]}
    finally:
        await pool.close()
