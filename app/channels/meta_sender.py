"""
Meta Sender — Nexo Basis Governador SaaS
=========================================
Versão: v2.0
Escopo: SAAS_MULTI_TENANT

Abstração para envio de mensagens via APIs do Instagram e Facebook.
Os tokens de acesso são carregados dinamicamente do banco por tenant
(via TenantConfig), com fallback para as variáveis de ambiente globais.
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

    async def _get_access_token(self, channel: Channel) -> str:
        """
        Retorna o access token Meta para o canal.
        Prioridade: 1) TenantConfig (banco) → 2) env vars (fallback dev).
        """
        try:
            from app.tenant_config import get_tenant_config
            config = await get_tenant_config()
            token = config.meta_access_token(channel.value)
            if token:
                return token
        except (ValueError, RuntimeError):
            pass  # Sem tenant ativo — usa fallback de env

        # Fallback: variáveis de ambiente globais
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
        """
        token = await self._get_access_token(channel)
        logger.debug("[SENDER] Token access fetched, length: %d", len(token) if token else 0)
        logger.info("[SENDER] Enviando DM canal=%s thread=%s", channel.value, thread_id)
        logger.debug("Texto: %s...", text[:100])
        # TODO: implementar chamada real à Graph API usando `token`
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
        """
        token = await self._get_access_token(channel)
        logger.debug("[SENDER] Token access fetched, length: %d", len(token) if token else 0)
        logger.info("[SENDER] Respondendo comentário canal=%s id=%s", channel.value, comment_id)
        logger.debug("Texto: %s...", text[:100])
        # TODO: implementar chamada real à Graph API usando `token`
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


async def send_message(
    channel: Channel,
    recipient_id: str,
    message_text: str,
    comment_id: Optional[str] = None,
) -> dict:
    """
    Atalho de envio multi-canal para o Webhook Router.

    Roteia automaticamente entre DM e resposta de comentário
    com base no canal fornecido.
    """
    from app.contracts.enums import SurfaceType

    if channel in (Channel.INSTAGRAM_COMMENT, Channel.FACEBOOK_COMMENT):
        if not comment_id:
            logger.warning("[SENDER] comment_id ausente para canal de comentário")
            return {}
        return await meta_sender.reply_comment(channel, comment_id, message_text)

    # DM (Instagram / Facebook)
    surface = SurfaceType.INBOX
    return await meta_sender.send(
        channel=channel,
        surface_type=surface,
        text=message_text,
        thread_id=recipient_id,
    )

