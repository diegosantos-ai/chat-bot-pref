from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from . import get_db

router = APIRouter()

# Campos reais baseados em db/migrations/002_tenant_identity_and_credentials.sql
CREDENTIAL_FIELDS = [
    "meta_ig_page_id",
    "meta_fb_page_id",
    "meta_access_token_ig",
    "meta_access_token_fb",
    "meta_webhook_verify_token"
]

class CredentialUpdate(BaseModel):
    meta_ig_page_id: Optional[str] = None
    meta_fb_page_id: Optional[str] = None
    meta_access_token_ig: Optional[str] = None
    meta_access_token_fb: Optional[str] = None
    meta_webhook_verify_token: Optional[str] = None

@router.get("/{tenant_id}")
async def get_credentials(tenant_id: str):
    """Retorna as credenciais mascaradas para o frontend."""
    async with get_db() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM tenant_credentials WHERE tenant_id = $1",
            tenant_id
        )
        
        if not row:
            # Se não existe linha de credencial, retorna estrutura vazia
            return {f: "" for f in CREDENTIAL_FIELDS}
        
        # Mascaramento para o Admin ver que existe mas não ver o token inteiro
        res = {}
        for f in CREDENTIAL_FIELDS:
            val = row.get(f) or ""
            if "access_token" in f and val:
                res[f] = val[:6] + "..." + val[-6:] if len(val) > 20 else val
            else:
                res[f] = val
        return res

@router.put("/{tenant_id}")
async def update_credentials(tenant_id: str, creds: CredentialUpdate):
    """Atualiza ou cria credenciais para o tenant."""
    async with get_db() as conn:
        # Verifica se já existe
        exists = await conn.fetchval(
            "SELECT 1 FROM tenant_credentials WHERE tenant_id = $1",
            tenant_id
        )
        
        if not exists:
            # Se não existe, cria (assumindo que o tenant_id seja válido)
            await conn.execute(
                "INSERT INTO tenant_credentials (tenant_id) VALUES ($1)",
                tenant_id
            )
            
        update_data = creds.dict(exclude_unset=True)
        if not update_data:
            return {"status": "no changes"}
            
        set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(update_data.keys())])
        values = list(update_data.values())
        
        await conn.execute(
            f"UPDATE tenant_credentials SET {set_clause} WHERE tenant_id = $1",
            tenant_id, *values
        )
        return {"status": "updated", "fields": list(update_data.keys())}
