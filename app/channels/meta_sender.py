"""
Meta Sender — Pilot Atendimento MVE
====================================
Versão: v1.0
Escopo: MVE_PILOT

Abstração para envio de mensagens via APIs do Instagram e Facebook.
"""

import logging
from typing import Optional

from app.contracts.enums import Channel, SurfaceType
from app.settings import settings

logger = logging.getLogger(__name__)


class MetaSenderError(Exception):
    """Erro ao enviar mensagem via Meta API."""

    pass


class MetaSender:
    """
    Sender unificado para Instagram e Facebook.
    Abstrai as diferenças entre DM e comentários.
    """

    def _get_page_id(self, channel: Channel) -> str:
        """Retorna o page ID correto baseado no canal (com fallback para legacy)."""
        if channel in (Channel.INSTAGRAM_DM, Channel.INSTAGRAM_COMMENT):
            return settings.META_PAGE_ID_INSTAGRAM or settings.META_PAGE_ID
        return settings.META_PAGE_ID_FACEBOOK or settings.META_PAGE_ID

    def _get_access_token(self, channel: Channel) -> str:
        """Retorna o token correto baseado no canal."""
        if channel in (Channel.INSTAGRAM_DM, Channel.INSTAGRAM_COMMENT):
            return settings.META_ACCESS_TOKEN_INSTAGRAM
        return settings.META_ACCESS_TOKEN_FACEBOOK

    async def send_dm(
        self,
        channel: Channel,
        thread_id: str,
        text: str,
    ) -> dict:
        """
        Envia mensagem de DM.

        Args:
            channel: INSTAGRAM_DM ou FACEBOOK_DM
            thread_id: ID do thread/conversa
            text: Texto da mensagem

        Returns:
            Resposta da API Meta
        """
        # TODO: Implementar chamada real à API Meta
        # Por ora, apenas log e mock
        logger.info(f"[MOCK] Enviando DM via {channel.value} para thread {thread_id}")
        logger.debug(f"Texto: {text[:100]}...")

        return {
            "recipient_id": thread_id,
            "message_id": f"mock_mid_{thread_id}",
        }

    async def reply_comment(
        self,
        channel: Channel,
        comment_id: str,
        text: str,
    ) -> dict:
        """
        Responde a um comentário.

        Args:
            channel: INSTAGRAM_COMMENT ou FACEBOOK_COMMENT
            comment_id: ID do comentário a responder
            text: Texto da resposta

        Returns:
            Resposta da API Meta
        """
        # TODO: Implementar chamada real à API Meta
        # Por ora, apenas log e mock
        logger.info(f"[MOCK] Respondendo comentário via {channel.value}: {comment_id}")
        logger.debug(f"Texto: {text[:100]}...")

        return {
            "comment_id": comment_id,
            "reply_id": f"mock_reply_{comment_id}",
        }

    async def send(
        self,
        channel: Channel,
        surface_type: SurfaceType,
        text: str,
        thread_id: Optional[str] = None,
        comment_id: Optional[str] = None,
    ) -> dict:
        """
        Método unificado de envio.
        Roteia para send_dm ou reply_comment conforme superfície.

        Args:
            channel: Canal de destino
            surface_type: Tipo de superfície
            text: Texto da mensagem
            thread_id: ID do thread (para DMs)
            comment_id: ID do comentário (para respostas)

        Returns:
            Resposta da API
        """
        if surface_type == SurfaceType.INBOX:
            if not thread_id:
                raise MetaSenderError("thread_id obrigatório para DM")
            return await self.send_dm(channel, thread_id, text)

        elif surface_type == SurfaceType.PUBLIC_COMMENT:
            if not comment_id:
                raise MetaSenderError(
                    "comment_id obrigatório para resposta de comentário"
                )
            return await self.reply_comment(channel, comment_id, text)

        else:
            raise MetaSenderError(f"surface_type não suportado: {surface_type}")


# Instância singleton
meta_sender = MetaSender()
