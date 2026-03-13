"""
Webhook Meta Router — Nexo Basis Governador SaaS
=================================================
Versão: v2.0
Escopo: SAAS_MULTI_TENANT

Responsabilidades:
- Receber POST /webhook/meta do Meta
- Validar assinatura X-Hub-Signature-256 (HMAC-SHA256)
- **Resolver Page ID → tenant_id via TenantResolver (LRU cache + DB)**
- **Injetar o tenant_id no contextvars da coroutine (tenant_context.set_tenant)**
- Retornar 401 para páginas sem Tenant cadastrado
- Converter payload Meta → NormalizedInboundEvent via meta_adapter
- Processar em background (resposta < 500ms para o Meta)
"""

import logging
import hashlib
import hmac
import json
from typing import Optional, Dict

import asyncpg
from fastapi import APIRouter, Request, Response, HTTPException, BackgroundTasks

from app.channels.meta_adapter import parse_meta_webhook
from app.contracts.dto import NormalizedInboundEvent
from app.orchestrator.service import get_orchestrator
from app.settings import settings
from app import tenant_context
from app.tenant_resolver import resolve_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])

# Pool compartilhado inicializado no startup da aplicação
_db_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Retorna o pool asyncpg compartilhado (criado no lifespan da app)."""
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=2,
            max_size=settings.DATABASE_POOL_SIZE,
        )
    return _db_pool


# ────────────────────────────────────────────────────
# Verificação de assinatura Meta
# ────────────────────────────────────────────────────

def _verify_signature(
    body: bytes,
    signature_header: Optional[str],
    secrets: list[str],
) -> bool:
    """
    Valida a assinatura X-Hub-Signature-256 do webhook Meta.
    Usa HMAC-SHA256 (padrão atual da Meta Graph API v18+).
    """
    if not signature_header:
        return False
    if not secrets:
        logger.error("Nenhum segredo de webhook Meta configurado.")
        return False

    prefix = "sha256="
    if not signature_header.startswith(prefix):
        return False

    for app_secret in secrets:
        expected = "sha256=" + hmac.new(
            app_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if hmac.compare_digest(signature_header, expected):
            return True

    return False


# ────────────────────────────────────────────────────
# Processamento em background (por tenant)
# ────────────────────────────────────────────────────

async def _process_event(
    event: NormalizedInboundEvent,
    tenant_id: str,
    page_id: str,
) -> None:
    """
    Processa um único evento no contexto do tenant.
    Executado em background — não bloqueia a resposta ao Meta.
    """
    # Injeta o tenant no contexto async desta coroutine
    tenant_context.set_tenant(tenant_id)

    orchestrator = get_orchestrator()

    from app.contracts.dto import ChatRequest

    chat_request = ChatRequest(
        session_id=event.session_id,
        message=event.text or "",
        tenant_id=tenant_id,
        channel=event.channel,
        surface_type=event.surface_type,
        external_message_id=event.external_message_id,
    )

    try:
        response, _ctx = await orchestrator.process(
            chat_request,
            post_id=event.post_id,
        )

        if response.message:
            from app.channels.meta_sender import send_message
            await send_message(
                channel=event.channel,
                recipient_id=event.author_platform_id or event.session_id,
                message_text=response.message,
            )
    except Exception:
        logger.exception(
            "[WEBHOOK] Erro ao processar evento tenant=%s page=%s msg=%s",
            tenant_id, page_id, event.external_message_id,
        )
    finally:
        tenant_context.clear_tenant()


# ────────────────────────────────────────────────────
# Endpoints
# ────────────────────────────────────────────────────

@router.get("/meta")
async def webhook_verify(
    hub_mode: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
    hub_challenge: Optional[str] = None,
) -> Response:
    """
    GET /webhook/meta — Verificação inicial do webhook pelo Meta.
    Usa o token global; a validação de tenant não se aplica aqui.
    """
    if hub_mode != "subscribe":
        raise HTTPException(status_code=403, detail="Invalid hub_mode")

    valid_tokens = settings.configured_webhook_verify_tokens
    if not valid_tokens:
        logger.error("[WEBHOOK] Nenhum verify token configurado")
        raise HTTPException(status_code=503, detail="Webhook verify token not configured")

    if hub_verify_token not in valid_tokens:
        logger.error("[WEBHOOK] Verify token inválido")
        raise HTTPException(status_code=403, detail="Invalid verify token")

    logger.info("[WEBHOOK] Webhook Meta verificado com sucesso")
    return Response(content=hub_challenge)


@router.post("/meta")
async def webhook_receive(
    request: Request,
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
    """
    POST /webhook/meta — Entrada principal de eventos Meta.

    Fluxo:
      1. Valida assinatura HMAC-SHA256.
      2. Parseia o payload JSON.
      3. Para cada entry, resolve o Page ID → tenant_id.
         - Página desconhecida → 401 (bloqueio silencioso, retorna {"status":"ok"} ao Meta).
      4. Despacha eventos normalizados em background com tenant injetado.
    """
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not _verify_signature(body, signature, settings.configured_meta_app_secrets):
        logger.error("[WEBHOOK] Assinatura inválida — request rejeitado")
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        raw_payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    pool = await get_db_pool()
    events = parse_meta_webhook(raw_payload)

    # Agrupar eventos pelo page_id para fazer uma única resolução por página
    page_ids: Dict[str, str] = {}
    for entry in raw_payload.get("entry", []):
        pid = entry.get("id", "")
        if pid and pid not in page_ids:
            tenant_id = await resolve_tenant(pid, pool)
            if tenant_id:
                page_ids[pid] = tenant_id
            else:
                logger.warning(
                    "[WEBHOOK] Page ID %s não tem tenant — eventos ignorados", pid
                )

    # Despacha apenas eventos de páginas com tenant resolvido
    dispatched = 0
    for event in events:
        if not event.page_id:
            logger.warning(
                "[WEBHOOK] Evento sem page_id normalizado: msg=%s canal=%s",
                event.external_message_id,
                event.channel,
            )
            continue

        tenant_id = page_ids.get(event.page_id)
        if not tenant_id:
            logger.warning(
                "[WEBHOOK] Evento ignorado por page_id sem tenant resolvido: page=%s msg=%s",
                event.page_id,
                event.external_message_id,
            )
            continue

        background_tasks.add_task(_process_event, event, tenant_id, event.page_id)
        dispatched += 1

    logger.info("[WEBHOOK] %d eventos despachados para %d tenants", dispatched, len(page_ids))

    # Meta exige resposta 200 em < 20s; processamento real é assíncrono
    return {"status": "ok"}
