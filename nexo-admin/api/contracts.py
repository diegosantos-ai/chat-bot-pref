"""Admin API — Contract Management."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date
from api import get_conn

router = APIRouter(prefix="/api/admin/contracts", tags=["Contracts"])

PLAN_TYPES = {"starter", "pro", "enterprise"}
STATUS_TYPES = {"active", "trial", "expired", "cancelled"}


class ContractCreate(BaseModel):
    tenant_id: str
    plan_type: str = "starter"
    starts_at: date
    expires_at: Optional[date] = None
    msg_limit: int = 10000
    status: str = "active"


class ContractUpdate(BaseModel):
    plan_type: Optional[str] = None
    starts_at: Optional[date] = None
    expires_at: Optional[date] = None
    msg_limit: Optional[int] = None
    status: Optional[str] = None


@router.get("")
async def list_contracts(tenant_id: Optional[str] = None):
    conn = await get_conn()
    try:
        q = """
            SELECT c.*, t.client_name
            FROM contracts c
            JOIN tenants t ON t.tenant_id = c.tenant_id
        """
        args = []
        if tenant_id:
            q += " WHERE c.tenant_id = $1"
            args.append(tenant_id)
        q += " ORDER BY c.created_at DESC"
        rows = await conn.fetch(q, *args)
        return {"contracts": [dict(r) for r in rows]}
    except Exception as e:
        # Table may not exist yet
        return {"contracts": [], "warning": str(e)}
    finally:
        await conn.close()


@router.post("", status_code=201)
async def create_contract(payload: ContractCreate):
    if payload.plan_type not in PLAN_TYPES:
        raise HTTPException(400, f"plan_type must be one of {PLAN_TYPES}")
    if payload.status not in STATUS_TYPES:
        raise HTTPException(400, f"status must be one of {STATUS_TYPES}")
    conn = await get_conn()
    try:
        row = await conn.fetchrow(
            """INSERT INTO contracts (tenant_id, plan_type, starts_at, expires_at, msg_limit, status)
               VALUES ($1,$2,$3,$4,$5,$6) RETURNING id""",
            payload.tenant_id, payload.plan_type, payload.starts_at,
            payload.expires_at, payload.msg_limit, payload.status,
        )
        return {"ok": True, "id": row["id"]}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        await conn.close()


@router.put("/{contract_id}")
async def update_contract(contract_id: int, payload: ContractUpdate):
    conn = await get_conn()
    try:
        updates = {k: v for k, v in payload.model_dump().items() if v is not None}
        if not updates:
            return {"ok": True, "message": "Nothing to update"}
        set_clause = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(updates))
        result = await conn.execute(
            f"UPDATE contracts SET {set_clause}, updated_at = NOW() WHERE id = $1",
            contract_id, *updates.values(),
        )
        if result == "UPDATE 0":
            raise HTTPException(404, "Contract not found")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        await conn.close()


@router.delete("/{contract_id}")
async def delete_contract(contract_id: int):
    conn = await get_conn()
    try:
        result = await conn.execute("DELETE FROM contracts WHERE id = $1", contract_id)
        if result == "DELETE 0":
            raise HTTPException(404, "Contract not found")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        await conn.close()
