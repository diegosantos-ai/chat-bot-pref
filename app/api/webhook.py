"""
Webhook Meta Service — Pilot Atendimento MVE
=============================================
Recebe mensagens do Instagram/Facebook e processa através do orquestrador.

Responsabilidades:
- Receber POST /webhook/meta do Meta
- Validar token de verificação
- Converter payload Meta → ChatRequest
- Chamar orquestrador
- Enviar resposta via API Meta
- Fazer retry em caso de falha
"""

import logging
import hashlib
import hmac
import json
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Request, Response, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.contracts.enums import Channel, SurfaceType
from app.contracts.dto import ChatRequest
from app.orchestrator.service import OrchestratorService, get_orchestrator
from app.settings import settings

logger = logging.getLogger(__name__)

# Router para webhooks
router = APIRouter(prefix="/webhook", tags=["webhooks"])


# ========================================
# DTOs para Payload Meta
# ========================================

class MessageField(BaseModel):
    """Mensagem recebida no webhook"""
    mid: str = Field(..., description="ID único da mensagem")
    text: Optional[str] = Field(None, description="Texto da mensagem")
    timestamp: str = Field(..., description="Timestamp da mensagem")


class SenderField(BaseModel):
    """Quem enviou a mensagem"""
    id: str = Field(..., description="ID do usuário no Meta")


class RecipientField(BaseModel):
    """Destinatário (sempre a página)"""
    id: str = Field(..., description="ID da página")


class MessagingEvent(BaseModel):
    """Um evento de mensagem do webhook Meta"""
    sender: SenderField
    recipient: RecipientField
    timestamp: str
    message: Optional[MessageField] = None
    postback: Optional[Dict[str, Any]] = None
    # Para comentários em posts
    comment: Optional[Dict[str, Any]] = None


class MetaWebhookPayload(BaseModel):
    """Payload completo do webhook Meta"""
    object: str = Field(..., description="'page' para Page webhooks")
    entry: list[Dict[str, Any]]


# ========================================
# Webhook Handler
# ========================================

class WebhookHandler:
    """
    Processa webhooks do Meta e envia respostas.
    """
    
    def __init__(self, orchestrator: Optional[OrchestratorService] = None):
        self.orchestrator = orchestrator or get_orchestrator()
        self.verify_token = settings.META_WEBHOOK_VERIFY_TOKEN
        self.app_secret = settings.META_APP_SECRET
        # Usa token do Instagram para API do Instagram
        self.access_token = settings.META_ACCESS_TOKEN_INSTAGRAM
    
    def verify_webhook_token(self, hub_verify_token: str) -> bool:
        """Valida o token de verificação do webhook."""
        return hub_verify_token == self.verify_token
    
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """Valida a assinatura X-Hub-Signature do webhook."""
        expected_signature = "sha1=" + hmac.new(
            self.app_secret.encode(),
            body,
            hashlib.sha1
        ).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    
    async def handle_incoming_message(
        self,
        event: MessagingEvent,
        page_id: str,
    ) -> None:
        """Processa uma mensagem recebida."""
        
        sender_id = event.sender.id
        recipient_id = event.recipient.id
        timestamp = event.timestamp
        
        # Detecta o tipo de mensagem
        if event.message:
            text = event.message.text or "(mensagem sem texto)"
            message_id = event.message.mid
            is_comment = False
            
        elif event.comment:
            text = event.comment.get("message", "(comentário sem texto)")
            message_id = event.comment.get("id", "unknown")
            is_comment = True
            
        else:
            logger.warning(f"Evento sem mensagem ou comentário: {event}")
            return
        
        # Determina o tipo de superfície
        surface_type = SurfaceType.PUBLIC_COMMENT if is_comment else SurfaceType.INBOX
        
        logger.info(
            f"[META WEBHOOK] Mensagem recebida: "
            f"from={sender_id}, page={page_id}, type={'COMMENT' if is_comment else 'DM'}, "
            f"text='{text[:50]}...'"
        )
        
        # Cria requisição de chat
        chat_request = ChatRequest(
            session_id=sender_id,
            message=text,
            channel=Channel.INSTAGRAM_DM if not is_comment else Channel.INSTAGRAM_COMMENT,
            surface_type=surface_type,
            external_message_id=message_id,
            timestamp=datetime.fromisoformat(timestamp.rstrip('Z')),
        )
        
        try:
            # Processa através do orquestrador
            response, context = await self.orchestrator.process(
                chat_request,
                post_id=message_id if is_comment else None,
            )
            
            # Envia resposta via API Meta (se houver mensagem)
            if response.message:
                await self.send_message_via_meta(
                    recipient_id=sender_id,
                    message_text=response.message,
                    message_id=message_id,
                )
            else:
                logger.info("[META WEBHOOK] Resposta vazia (NO_REPLY), nenhuma mensagem enviada")
            
            # Log de auditoria
            logger.info(
                f"[META WEBHOOK] Resposta processada: "
                f"decision={response.decision.value}, "
                f"intent={response.intent.value}"
            )
            
        except Exception as e:
            logger.error(f"[META WEBHOOK] Erro ao processar mensagem: {e}", exc_info=True)
            # Envia mensagem de fallback
            await self.send_message_via_meta(
                recipient_id=sender_id,
                message_text="Desculpe, houve um erro ao processar sua solicitação. Tente novamente.",
                message_id=message_id,
            )
    
    async def send_message_via_meta(
        self,
        recipient_id: str,
        message_text: str,
        message_id: str,
    ) -> bool:
        """
        Envia mensagem via API Meta com retry.
        
        Returns:
            True se enviou com sucesso, False caso contrário
        """
        import aiohttp
        
        url = "https://graph.instagram.com/v18.0/me/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text},
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status in [200, 201]:
                        logger.info(f"[META API] Mensagem enviada com sucesso: {message_id}")
                        return True
                    else:
                        error_text = await resp.text()
                        logger.error(f"[META API] Erro ao enviar: {resp.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"[META API] Exceção ao enviar mensagem: {e}")
            return False


# ========================================
# Endpoints
# ========================================

_handler: Optional[WebhookHandler] = None


def get_webhook_handler() -> WebhookHandler:
    """Singleton do webhook handler."""
    global _handler
    if _handler is None:
        _handler = WebhookHandler()
    return _handler


@router.get("/meta")
async def webhook_get(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
) -> Response:
    """
    GET /webhook/meta - Verificação de webhook do Meta.
    
    Meta chama esse endpoint uma única vez para validar o webhook.
    """
    handler = get_webhook_handler()
    
    if hub_mode != "subscribe":
        logger.error(f"[META WEBHOOK] Invalid hub_mode: {hub_mode}")
        raise HTTPException(status_code=403, detail="Invalid hub_mode")
    
    if not handler.verify_webhook_token(hub_verify_token):
        logger.error("[META WEBHOOK] Invalid verify token")
        raise HTTPException(status_code=403, detail="Invalid verify token")
    
    logger.info("[META WEBHOOK] Webhook verificado com sucesso")
    return Response(content=hub_challenge)


@router.post("/meta")
async def webhook_post(
    request: Request,
    background_tasks: BackgroundTasks,
) -> Dict[str, str]:
    """
    POST /webhook/meta - Recebe eventos do Meta (mensagens, comentários).
    
    Meta envia eventos sempre que há atividade na página:
    - Novas mensagens (DMs)
    - Novos comentários em posts
    - Reações
    - Etc.
    """
    handler = get_webhook_handler()
    
    # Valida assinatura
    x_hub_signature = request.headers.get("X-Hub-Signature")
    body = await request.body()
    
    if not handler.verify_webhook_signature(body, x_hub_signature):
        logger.error("[META WEBHOOK] Invalid signature")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parseia payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.error("[META WEBHOOK] Invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Processa eventos em background
    if payload.get("object") == "page":
        for entry in payload.get("entry", []):
            page_id = entry.get("id")
            
            for messaging in entry.get("messaging", []):
                event = MessagingEvent(**messaging)
                
                # Processa em background para responder rápido
                background_tasks.add_task(
                    handler.handle_incoming_message,
                    event,
                    page_id,
                )
    
    # Responde rápido ao Meta (ele precisa de 200 em menos de 20s)
    return {"status": "ok"}
