"""
Meta Webhook Adapter — Pilot Atendimento MVE
=============================================
Versão: v1.0
Escopo: MVE_PILOT

Parser e normalizador de webhooks do Instagram e Facebook.
Converte payloads Meta para NormalizedInboundEvent.
"""

import logging
from typing import Optional, List
from pydantic import BaseModel

from app.contracts.dto import NormalizedInboundEvent
from app.contracts.enums import Channel, SurfaceType

logger = logging.getLogger(__name__)


# ========================================
# Modelos de payload Meta (entrada bruta)
# ========================================

class MetaMessageAttachment(BaseModel):
    """Anexo de mensagem Meta."""
    type: str  # image, video, audio, file
    payload: Optional[dict] = None


class MetaMessage(BaseModel):
    """Mensagem de DM do Meta."""
    mid: str  # message id
    text: Optional[str] = None
    attachments: Optional[List[MetaMessageAttachment]] = None


class MetaMessagingEntry(BaseModel):
    """Entrada de messaging (DM)."""
    sender: dict  # {"id": "..."}
    recipient: dict  # {"id": "..."}
    timestamp: int
    message: Optional[MetaMessage] = None


class MetaCommentChange(BaseModel):
    """Mudança de comentário."""
    field: str  # "comments"
    value: dict  # {comment_id, post_id, parent_id, from, message, ...}


class MetaWebhookEntry(BaseModel):
    """Entrada do webhook Meta."""
    id: str  # page/account id
    time: int
    messaging: Optional[List[MetaMessagingEntry]] = None
    changes: Optional[List[MetaCommentChange]] = None


class MetaWebhookPayload(BaseModel):
    """Payload completo do webhook Meta."""
    object: str  # "instagram" ou "page"
    entry: List[MetaWebhookEntry]


# ========================================
# Funções de parsing
# ========================================

def parse_instagram_dm(entry: MetaMessagingEntry) -> Optional[NormalizedInboundEvent]:
    """
    Parseia DM do Instagram.
    
    Args:
        entry: Entrada de messaging do webhook
        
    Returns:
        Evento normalizado ou None se inválido
    """
    if not entry.message:
        logger.warning("Entrada de DM sem mensagem, ignorando")
        return None
    
    sender_id = entry.sender.get("id", "")
    thread_id = f"{sender_id}"  # No Instagram DM, o thread é 1:1 com o sender
    
    return NormalizedInboundEvent(
        external_message_id=entry.message.mid,
        session_id=f"instagram_dm:{thread_id}",
        channel=Channel.INSTAGRAM_DM,
        surface_type=SurfaceType.INBOX,
        text=entry.message.text or "",
        has_media=bool(entry.message.attachments),
        thread_id=thread_id,
        author_platform_id=sender_id,
    )


def parse_facebook_dm(entry: MetaMessagingEntry) -> Optional[NormalizedInboundEvent]:
    """
    Parseia DM do Facebook Messenger.
    
    Args:
        entry: Entrada de messaging do webhook
        
    Returns:
        Evento normalizado ou None se inválido
    """
    if not entry.message:
        logger.warning("Entrada de DM sem mensagem, ignorando")
        return None
    
    sender_id = entry.sender.get("id", "")
    thread_id = f"{sender_id}"
    
    return NormalizedInboundEvent(
        external_message_id=entry.message.mid,
        session_id=f"facebook_dm:{thread_id}",
        channel=Channel.FACEBOOK_DM,
        surface_type=SurfaceType.INBOX,
        text=entry.message.text or "",
        has_media=bool(entry.message.attachments),
        thread_id=thread_id,
        author_platform_id=sender_id,
    )


def parse_instagram_comment(change: MetaCommentChange) -> Optional[NormalizedInboundEvent]:
    """
    Parseia comentário do Instagram.
    
    Args:
        change: Mudança de comentário do webhook
        
    Returns:
        Evento normalizado ou None se inválido
    """
    if change.field != "comments":
        return None
    
    value = change.value
    comment_id = value.get("id", "")
    post_id = value.get("media", {}).get("id", "")
    parent_id = value.get("parent_id")
    author = value.get("from", {})
    author_id = author.get("id", "")
    text = value.get("text", "")
    
    return NormalizedInboundEvent(
        external_message_id=comment_id,
        session_id=f"instagram_comment:{post_id}:{author_id}",
        channel=Channel.INSTAGRAM_COMMENT,
        surface_type=SurfaceType.PUBLIC_COMMENT,
        text=text,
        has_media=False,
        post_id=post_id,
        comment_id=comment_id,
        parent_comment_id=parent_id,
        author_platform_id=author_id,
    )


def parse_facebook_comment(change: MetaCommentChange) -> Optional[NormalizedInboundEvent]:
    """
    Parseia comentário do Facebook.
    
    Args:
        change: Mudança de comentário do webhook
        
    Returns:
        Evento normalizado ou None se inválido
    """
    if change.field != "feed":
        return None
    
    value = change.value
    item = value.get("item", "")
    
    if item != "comment":
        return None
    
    comment_id = value.get("comment_id", "")
    post_id = value.get("post_id", "")
    parent_id = value.get("parent_id")
    author_id = value.get("from", {}).get("id", "")
    text = value.get("message", "")
    
    return NormalizedInboundEvent(
        external_message_id=comment_id,
        session_id=f"facebook_comment:{post_id}:{author_id}",
        channel=Channel.FACEBOOK_COMMENT,
        surface_type=SurfaceType.PUBLIC_COMMENT,
        text=text,
        has_media=False,
        post_id=post_id,
        comment_id=comment_id,
        parent_comment_id=parent_id,
        author_platform_id=author_id,
    )


def parse_meta_webhook(payload: dict) -> List[NormalizedInboundEvent]:
    """
    Parseia payload completo do webhook Meta.
    
    Args:
        payload: Payload JSON do webhook
        
    Returns:
        Lista de eventos normalizados
    """
    events = []
    
    try:
        webhook = MetaWebhookPayload(**payload)
    except Exception as e:
        logger.error(f"Erro ao parsear webhook Meta: {e}")
        return events
    
    is_instagram = webhook.object == "instagram"
    
    for entry in webhook.entry:
        # Processa DMs
        if entry.messaging:
            for msg_entry in entry.messaging:
                if is_instagram:
                    event = parse_instagram_dm(msg_entry)
                else:
                    event = parse_facebook_dm(msg_entry)
                
                if event:
                    events.append(event)
        
        # Processa comentários
        if entry.changes:
            for change in entry.changes:
                if is_instagram:
                    event = parse_instagram_comment(change)
                else:
                    event = parse_facebook_comment(change)
                
                if event:
                    events.append(event)
    
    logger.info(f"Parseados {len(events)} eventos do webhook Meta")
    return events
