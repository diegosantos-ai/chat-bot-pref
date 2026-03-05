import hmac
import hashlib
import logging
from app.settings import settings
from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


def _verify_signature_with_secret(body: bytes, signature: str, secret: str) -> bool:
    """
    Verifica se a assinatura corresponde ao body usando o secret fornecido.
    """
    expected_prefix = "sha256="
    if not signature.startswith(expected_prefix):
        return False

    sig_hash = signature[len(expected_prefix) :]

    generated_hash = hmac.new(
        key=secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(sig_hash, generated_hash)


async def verify_signature(request: Request, platform: str | None = None):
    """
    Verifica a assinatura X-Hub-Signature-256 enviada pela Meta.

    Args:
        request: Requisição do FastAPI
        platform: Plataforma de origem ('facebook', 'instagram' ou None para tentar ambas)

    Raises:
        HTTPException: Se a assinatura for inválida ou ausente
    """
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=403, detail="Assinatura ausente")

    body = await request.body()

    # Se a plataforma foi especificada, usa o secret correspondente
    if platform == "instagram" and settings.META_APP_SECRET_INSTAGRAM:
        if _verify_signature_with_secret(
            body, signature, settings.META_APP_SECRET_INSTAGRAM
        ):
            return
        raise HTTPException(status_code=403, detail="Assinatura inválida (Instagram)")

    if platform == "facebook" and settings.META_APP_SECRET_FACEBOOK:
        if _verify_signature_with_secret(
            body, signature, settings.META_APP_SECRET_FACEBOOK
        ):
            return
        raise HTTPException(status_code=403, detail="Assinatura inválida (Facebook)")

    # Se não especificou plataforma ou secret está vazio, tenta ambos
    secrets_to_try = []

    if settings.META_APP_SECRET_FACEBOOK:
        secrets_to_try.append(("Facebook", settings.META_APP_SECRET_FACEBOOK))
    if settings.META_APP_SECRET_INSTAGRAM:
        secrets_to_try.append(("Instagram", settings.META_APP_SECRET_INSTAGRAM))

    # Fallback para variável antiga (retrocompatibilidade)
    if not secrets_to_try and settings.META_APP_SECRET:
        secrets_to_try.append(("Legacy", settings.META_APP_SECRET))

    for platform_name, secret in secrets_to_try:
        if _verify_signature_with_secret(body, signature, secret):
            logger.debug(
                f"Assinatura validada com sucesso usando secret do {platform_name}"
            )
            return

    raise HTTPException(status_code=403, detail="Assinatura inválida")
