import httpx
from app.settings import settings
import logging

logger = logging.getLogger(__name__)


import re  # noqa: E402


def strip_markdown(text: str) -> str:
    """
    Remove formatação Markdown do texto para plataformas que não suportam.

    Args:
        text: Texto com formatação Markdown

    Returns:
        Texto sem formatação Markdown
    """
    # Remove negrito (**texto**)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)

    # Remove itálico (*texto* ou _texto_)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)

    # Remove código inline (`texto`)
    text = re.sub(r"`(.+?)`", r"\1", text)

    # Remove blocos de código (```...```)
    text = re.sub(r"```[\s\S]*?```", "", text)

    # Remove links markdown [texto](url) -> mantém só o texto
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)

    # Remove imagens markdown ![alt](url)
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", "", text)

    # Remove headers (# Título)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)

    # Remove listas (* item ou - item ou 1. item) -> mantém o texto
    text = re.sub(r"^[\*\-\+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)

    # Remove citações (> texto)
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)

    # Remove separadores horizontais
    text = re.sub(r"\n---\n", "\n", text)
    text = re.sub(r"\n\*\*\*\n", "\n", text)
    text = re.sub(r"\n___\n", "\n", text)

    # Limpa espaços extras
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def split_message(text: str, max_length: int = 1000) -> list[str]:
    """
    Divide uma mensagem em partes menores sem cortar palavras.

    Args:
        text: Texto a ser dividido
        max_length: Tamanho máximo de cada parte

    Returns:
        Lista de partes da mensagem
    """
    if len(text) <= max_length:
        return [text]

    parts = []
    current_part = ""

    # Divide por parágrafos primeiro (quebras de linha duplas)
    paragraphs = text.split("\n\n")

    for paragraph in paragraphs:
        # Se o parágrafo sozinho é maior que o limite, divide por sentenças/pontos
        if len(paragraph) > max_length:
            sentences = (
                paragraph.replace(". ", ".\n")
                .replace("! ", "!\n")
                .replace("? ", "?\n")
                .split("\n")
            )

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                # Se a sentença ainda é grande, divide por espaços
                if len(sentence) > max_length:
                    words = sentence.split(" ")
                    for word in words:
                        if len(current_part) + len(word) + 1 <= max_length:
                            current_part += word + " "
                        else:
                            if current_part.strip():
                                parts.append(current_part.strip())
                            current_part = word + " "
                else:
                    # Tenta adicionar a sentença completa
                    if len(current_part) + len(sentence) + 2 <= max_length:
                        current_part += sentence + " "
                    else:
                        if current_part.strip():
                            parts.append(current_part.strip())
                        current_part = sentence + " "
        else:
            # Tenta adicionar o parágrafo completo
            if len(current_part) + len(paragraph) + 2 <= max_length:
                current_part += paragraph + "\n\n"
            else:
                if current_part.strip():
                    parts.append(current_part.strip())
                current_part = paragraph + "\n\n"

    # Adiciona o último pedaço se houver
    if current_part.strip():
        parts.append(current_part.strip())

    return parts if parts else [text[:max_length]]


class MetaClient:
    def __init__(self, platform: str = "facebook"):
        """
        Cliente Meta API.

        Args:
            platform: "instagram" ou "facebook" para identificar a origem
        """
        self.platform = platform.lower()

        # Seleciona configurações conforme a plataforma
        if self.platform == "instagram":
            # NOVA API: Instagram API with Instagram Login
            # Não requer mais Facebook Page vinculada
            # Documentação: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api/
            self.base_url = "https://graph.instagram.com"
            self._access_token = settings.META_ACCESS_TOKEN_INSTAGRAM
            self._ig_business_id = settings.META_PAGE_ID_INSTAGRAM
            # Para Facebook (legado), mantém graph.facebook.com
        else:
            self.base_url = f"https://graph.facebook.com/{settings.META_API_VERSION}"
            self._access_token = settings.META_ACCESS_TOKEN_FACEBOOK
            self._page_id = settings.META_PAGE_ID_FACEBOOK or settings.META_PAGE_ID

        # Timeout configurável
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def send_message(
        self, recipient_id: str, text: str, ig_user_id: str | None = None
    ):
        """
        Envia mensagem de texto para um usuário.

        Para Instagram (NOVA API): usa POST /me/messages (Instagram API with Instagram Login)
        Para Facebook (legado): usa POST /me/messages (Messenger API)

        Args:
            recipient_id: ID do destinatário (IGSID para Instagram, PSID para Facebook)
            text: Texto da mensagem
            ig_user_id: Opcional. Instagram Business Account ID para envio específico.
        """
        # Para Instagram, remove markdown e divide mensagens grandes
        if self.platform == "instagram":
            # Remove formatação Markdown
            text = strip_markdown(text)

            if len(text) > 1000:
                message_parts = split_message(text, max_length=1000)
                logger.info(
                    f"Mensagem dividida em {len(message_parts)} partes ({len(text)} caracteres)"
                )

                # Envia cada parte sequencialmente
                results = []
                for i, part in enumerate(message_parts, 1):
                    logger.debug(
                        f"Enviando parte {i}/{len(message_parts)} ({len(part)} caracteres)"
                    )
                    result = await self._send_single_message(
                        recipient_id, part, ig_user_id
                    )
                    results.append(result)

                return results

        # Para Facebook ou mensagens pequenas, envia normalmente
        return await self._send_single_message(recipient_id, text, ig_user_id)

    async def _send_single_message(
        self, recipient_id: str, text: str, ig_user_id: str | None = None
    ):
        """
        Envia uma única mensagem (método interno).
        """
        if self.platform == "instagram":
            # NOVA API: Instagram API with Instagram Login
            # Endpoint: POST /me/messages ou /{ig_id}/messages
            # Não requer Facebook Page vinculada
            # Documentação: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api/
            if ig_user_id:
                url = f"{self.base_url}/{ig_user_id}/messages"
            else:
                url = f"{self.base_url}/me/messages"
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": text},
            }
        else:
            # Facebook Messenger API (legado): POST /me/messages
            url = f"{self.base_url}/me/messages"
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": text},
                "messaging_type": "RESPONSE",
            }

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        logger.info(
            f"Enviando mensagem via {self.platform.upper()} API para {recipient_id[:20]}... "
            f"(endpoint: {url.split('/')[-2]})"
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"Mensagem enviada com sucesso via {self.platform.upper()}")
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Erro ao enviar mensagem Meta ({self.platform}): {e.response.text}"
                )
                raise e
            except httpx.TimeoutException as e:
                logger.error(f"Timeout ao enviar mensagem Meta: {str(e)}")
                raise e
            except Exception as e:
                logger.error(f"Erro desconhecido Meta: {str(e)}")
                raise e

    async def send_private_reply(self, comment_id: str, text: str):
        """
        Envia resposta privada a um comentário (Instagram/Facebook).

        Para Instagram (NOVA API): POST /me/messages com recipient.comment_id
        Para Facebook (legado): POST /me/messages com recipient.comment_id
        """
        # Para Instagram, remove markdown e divide mensagens grandes
        if self.platform == "instagram":
            # Remove formatação Markdown
            text = strip_markdown(text)

            if len(text) > 1000:
                message_parts = split_message(text, max_length=1000)
                logger.info(
                    f"Mensagem privada dividida em {len(message_parts)} partes ({len(text)} caracteres)"
                )

                # Envia cada parte sequencialmente
                results = []
                for i, part in enumerate(message_parts, 1):
                    logger.debug(
                        f"Enviando parte privada {i}/{len(message_parts)} ({len(part)} caracteres)"
                    )
                    result = await self._send_single_private_reply(comment_id, part)
                    results.append(result)

                return results

        # Para Facebook ou mensagens pequenas, envia normalmente
        return await self._send_single_private_reply(comment_id, text)

    async def _send_single_private_reply(self, comment_id: str, text: str):
        """
        Envia uma única resposta privada (método interno).
        """
        if self.platform == "instagram":
            # NOVA API: Instagram API with Instagram Login
            url = f"{self.base_url}/me/messages"
        else:
            # Facebook Messenger API (legado)
            url = f"{self.base_url}/me/messages"

        payload = {"recipient": {"comment_id": comment_id}, "message": {"text": text}}
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Erro ao enviar private reply Meta: {e.response.text}")
                raise e

    async def get_user_profile(self, user_id: str) -> dict | None:
        """
        Busca informações do perfil de um usuário na API da Meta.

        IMPORTANTE: Requer permissão 'instagram_basic' na Meta App.
        Se a permissão não estiver disponível, retorna None.

        Args:
            user_id: ID do usuário na plataforma (Instagram ou Facebook)

        Returns:
            Dict com 'username', 'name' e 'profile_picture_url' se sucesso,
            None se falhar ou não tiver permissão.

        Example:
            >>> profile = await client.get_user_profile("17841413792837146")
            >>> print(profile)
            {'username': 'prefeitura_sto', 'name': 'Prefeitura STO', 'profile_picture_url': 'https://...'}
        """
        # Para Instagram, usamos a API do Instagram
        # Para Facebook, usamos a Graph API
        if self.platform == "instagram":
            # Instagram API - Simplificado
            # Nota: O sender_id do webhook é um ID scoped que não permite acessar
            # o perfil público diretamente. Tentamos buscar o que for possível.
            url = f"{self.base_url}/{user_id}"
            params = {"fields": "username,name", "access_token": self._access_token}
        else:
            # Facebook Graph API
            url = f"{self.base_url}/{user_id}"
            params = {"fields": "name", "access_token": self._access_token}

        logger.info(
            f"Buscando perfil do usuário {user_id} na API {self.platform.upper()}"
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Normaliza os dados retornados
                profile = {
                    "username": data.get("username"),
                    "name": data.get("name"),
                    "profile_picture_url": None,
                }

                logger.info(
                    f"Perfil obtido com sucesso: @{profile['username'] or 'N/A'} "
                    f"({profile['name'] or 'N/A'})"
                )
                return profile

            except httpx.HTTPStatusError as e:
                # Erro 403 = sem permissão, 404 = usuário não encontrado
                if e.response.status_code == 403:
                    logger.warning(
                        f"Sem permissão para buscar perfil do usuário {user_id}. "
                        f"Verifique se a app tem permissão 'instagram_basic'."
                    )
                elif e.response.status_code == 404:
                    logger.warning(
                        f"Usuário {user_id} não encontrado na API {self.platform}"
                    )
                else:
                    logger.error(f"Erro ao buscar perfil: {e.response.text}")
                return None

            except Exception as e:
                logger.error(f"Erro inesperado ao buscar perfil: {str(e)}")
                return None


# Função helper para obter instância do cliente
def get_meta_client(platform: str = "facebook") -> MetaClient:
    """Retorna instância do cliente Meta para a plataforma especificada."""
    return MetaClient(platform=platform)
