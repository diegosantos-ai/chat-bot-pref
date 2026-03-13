import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from app.extensions import webhook_limiter as limiter

from app.contracts.dto import ChatRequest
from app.contracts.enums import Channel, SurfaceType
from app.integrations.meta.client import MetaClient
from app.integrations.meta.security import verify_signature
from app.orchestrator.service import get_orchestrator
from app.settings import settings

logger = logging.getLogger(__name__)

# The `limiter` instance is imported from app.extensions; decorators below
# will set the actual limits using values from settings.

router = APIRouter(prefix="/webhook", tags=["Meta Integration"])


@router.get("/meta")
@limiter.limit(
    "100/minute"
)  # Limite maior para verificação (Meta precisa responder rápido)
async def verify_webhook(
    request: Request,
    response: Response,
    mode: str = Query(..., alias="hub.mode"),
    token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge"),
) -> Response:
    """
    Verificacao do Webhook pela Meta.
    Header ngrok-skip-browser-warning evita pagina de protecao do ngrok free.
    """
    valid_tokens = {
        settings.META_WEBHOOK_VERIFY_TOKEN,
        settings.META_WEBHOOK_VERIFY_TOKEN_FACEBOOK,
        settings.META_WEBHOOK_VERIFY_TOKEN_INSTAGRAM,
    }
    # Remove strings vazias para seguranca
    valid_tokens = {t for t in valid_tokens if t}

    if mode == "subscribe" and token in valid_tokens:
        logger.info("Webhook verificado com sucesso.")
        return Response(
            content=challenge,
            media_type="text/plain",
            headers={"ngrok-skip-browser-warning": "true"},
        )

    logger.warning("Falha na verificacao do webhook: token invalido.")
    raise HTTPException(status_code=403, detail="Token invalido")


@router.post("/meta", dependencies=[Depends(verify_signature)])
@limiter.limit(f"{settings.RATE_LIMIT_WEBHOOK_PER_MINUTE}/minute")
async def handle_webhook_event(request: Request, response: Response) -> dict[str, str]:
    """
    Recebe eventos da Meta (Messenger, Instagram DM, Comentarios).
    """
    try:
        data = await request.json()

        object_type: str = data.get("object") or "page"
        entries: list[dict[str, Any]] = data.get("entry", [])
        logger.info(
            "Webhook Meta recebido: object=%s entries=%s",
            object_type,
            len(entries),
        )

        orchestrator = get_orchestrator()
        # Passa a plataforma para o cliente selecionar o token correto
        platform = "instagram" if object_type == "instagram" else "facebook"
        client = MetaClient(platform=platform)

        for entry in entries:
            page_id = entry.get("id")
            # Para Instagram, entry.id é o Instagram Business Account ID
            # Para Facebook, entry.id é o Page ID
            logger.info(f"Processing entry: id={page_id}, keys={list(entry.keys())}")

            if "messaging" in entry:
                for event in entry["messaging"]:
                    # Log detalhado do evento para debug
                    recipient_id = event.get("recipient", {}).get("id")
                    sender_id = event.get("sender", {}).get("id")
                    logger.info(
                        f"Messaging event: sender={sender_id}, recipient={recipient_id}"
                    )

                    if "message" in event and not event["message"].get("is_echo"):
                        await process_messaging_event(
                            event=event,
                            object_type=object_type,
                            orchestrator=orchestrator,
                            client=client,
                            # Para Instagram, o recipient.id é o ID da conta IG Business
                            ig_user_id=recipient_id
                            if object_type == "instagram"
                            else None,
                        )

            elif "changes" in entry:
                for change in entry["changes"]:
                    if change.get("field") in ["feed", "comments", "mentions"]:
                        await process_change_event(
                            change=change,
                            object_type=object_type,
                            orchestrator=orchestrator,
                            client=client,
                        )

        return {"status": "ok"}

    except Exception as exc:  # pragma: no cover - defensivo para producao
        logger.exception("Erro ao processar webhook Meta")
        # Retorna 200 para a Meta nao ficar reenviando em caso de erro interno nosso
        return {"status": "error", "detail": str(exc)}


async def process_messaging_event(
    event: dict[str, Any],
    object_type: str,
    orchestrator: Any,
    client: MetaClient,
    ig_user_id: str | None = None,
) -> None:
    """Processa eventos de mensagem direta."""
    sender_id = event["sender"]["id"]
    message_text = event["message"].get("text")
    message_id = event.get("message", {}).get("mid") or str(uuid4())

    if not message_text:
        return  # Ignora adesivos, anexos por enquanto

    channel = (
        Channel.INSTAGRAM_DM if object_type == "instagram" else Channel.FACEBOOK_DM
    )

    chat_request = ChatRequest(
        session_id=sender_id,
        message=message_text,
        channel=channel,
        surface_type=SurfaceType.INBOX,
        external_message_id=message_id,
    )

    response, _ = await orchestrator.process(chat_request)

    if response.message:
        await client.send_message(
            recipient_id=sender_id,
            text=response.message,
            ig_user_id=ig_user_id,
        )


async def process_change_event(
    change: dict[str, Any],
    object_type: str,
    orchestrator: Any,
    client: MetaClient,
) -> None:
    """Processa eventos de mudancas (comentarios)."""
    value = change.get("value", {})
    item = value.get("item")

    if item == "comment" or item == "post":
        comment_id = value.get("comment_id") or value.get("post_id")
        message_text = value.get("message")
        sender_id = value.get("from", {}).get("id")

        if not message_text or not sender_id:
            return

        # Ignora comentarios do proprio autor (se houver flag)
        # TODO: Adicionar verificacao de ID da pagina se necessario

        channel = (
            Channel.INSTAGRAM_COMMENT
            if object_type == "instagram"
            else Channel.FACEBOOK_COMMENT
        )

        chat_request = ChatRequest(
            session_id=f"{sender_id}_{comment_id}",
            # Melhor manter session por user se possivel, mas em comments o contexto e curto.
            # Vamos usar sender_id para manter historico se o user comentar de novo.
            message=message_text,
            channel=channel,
            surface_type=SurfaceType.PUBLIC_COMMENT,
            post_id=value.get("post_id"),
            comment_id=comment_id,
        )

        response, _ = await orchestrator.process(chat_request, comment_id=comment_id)

        # TODO: Implementar logica de reply publica vs privada dependendo da decisao do Orchestrator
        if response.message:
            # await client.send_private_reply(comment_id, response.message)
            logger.info(
                "Resposta gerada para comentario %s: %s (envio pendente de impl. final)",
                comment_id,
                response.message,
            )
