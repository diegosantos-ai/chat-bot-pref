"""Admin API — Tenant Management."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from api import get_conn

router = APIRouter(prefix="/api/admin/tenants", tags=["Tenants"])


class TenantCreate(BaseModel):
    tenant_id: str
    client_name: str
    bot_name: str
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    support_email: Optional[str] = None
    fallback_url: Optional[str] = None


class TenantUpdate(BaseModel):
    client_name: Optional[str] = None
    bot_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_address: Optional[str] = None
    support_email: Optional[str] = None
    fallback_url: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_tenants(active_only: bool = False):
    conn = await get_conn()
    try:
        q = "SELECT * FROM tenants"
        if active_only:
            q += " WHERE is_active = true"
        q += " ORDER BY created_at DESC"
        rows = await conn.fetch(q)
        return {"tenants": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        await conn.close()


@router.get("/{tenant_id}")
async def get_tenant(tenant_id: str):
    conn = await get_conn()
    try:
        row = await conn.fetchrow(
            "SELECT * FROM tenants WHERE tenant_id = $1", tenant_id
        )
        if not row:
            raise HTTPException(404, f"Tenant '{tenant_id}' not found")
        return dict(row)
    finally:
        await conn.close()


@router.post("", status_code=201)
async def create_tenant(payload: TenantCreate):
    conn = await get_conn()
    try:
        existing = await conn.fetchrow(
            "SELECT tenant_id FROM tenants WHERE tenant_id = $1", payload.tenant_id
        )
        if existing:
            raise HTTPException(409, f"Tenant '{payload.tenant_id}' already exists")
        await conn.execute(
            """INSERT INTO tenants (tenant_id, client_name, bot_name, contact_phone,
               contact_address, support_email, fallback_url, is_active)
               VALUES ($1,$2,$3,$4,$5,$6,$7,true)""",
            payload.tenant_id, payload.client_name, payload.bot_name,
            payload.contact_phone, payload.contact_address,
            payload.support_email, payload.fallback_url,
        )
        return {"ok": True, "tenant_id": payload.tenant_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        await conn.close()


@router.put("/{tenant_id}")
async def update_tenant(tenant_id: str, payload: TenantUpdate):
    conn = await get_conn()
    try:
        row = await conn.fetchrow(
            "SELECT tenant_id FROM tenants WHERE tenant_id = $1", tenant_id
        )
        if not row:
            raise HTTPException(404, "Tenant not found")
        updates = {k: v for k, v in payload.model_dump().items() if v is not None}
        if not updates:
            return {"ok": True, "message": "Nothing to update"}
        set_clause = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(updates))
        await conn.execute(
            f"UPDATE tenants SET {set_clause}, updated_at = NOW() WHERE tenant_id = $1",
            tenant_id, *updates.values(),
        )
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        await conn.close()


@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str):
    conn = await get_conn()
    try:
        result = await conn.execute(
            "DELETE FROM tenants WHERE tenant_id = $1", tenant_id
        )
        if result == "DELETE 0":
            raise HTTPException(404, "Tenant not found")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        await conn.close()
