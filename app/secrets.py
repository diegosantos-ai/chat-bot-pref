"""
AWS Secrets Manager - Carregamento opcional de secrets
====================================================

Este módulo permite carregar secrets do AWS Secrets Manager
se USE_SECRETS_MANAGER=True nas configurações.

Uso:
    from app.secrets import get_secrets
    secrets = get_secrets()
    
Formato esperado no Secrets Manager:
{
    "GEMINI_API_KEY": "...",
    "DATABASE_URL": "...",
    "META_ACCESS_TOKEN_INSTAGRAM": "...",
    "META_ACCESS_TOKEN_FACEBOOK": "...",
    "META_PAGE_ID": "...",
    "META_APP_SECRET": "...",
    "META_WEBHOOK_VERIFY_TOKEN": "...",
    "USER_HASH_SALT": "...",
    "ADMIN_API_KEY": "..."
}
"""

import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Import boto3 apenas se necessário (lazy loading)
_boto3_available = False
try:
    import boto3
    from botocore.exceptions import ClientError
    _boto3_available = True
except ImportError:
    logger.warning("boto3 não está instalado. AWS Secrets Manager não estará disponível.")


def get_secrets(secret_name: str, region: str = "sa-east-1") -> Optional[Dict[str, Any]]:
    """
    Busca secrets do AWS Secrets Manager.
    
    Args:
        secret_name: Nome do secret no AWS Secrets Manager
        region: Região da AWS (padrão: sa-east-1)
    
    Returns:
        Dict com os secrets ou None em caso de erro
    
    Raises:
        Exception: Se boto3 não estiver instalado ou houver erro fatal
    """
    if not _boto3_available:
        raise ImportError(
            "boto3 não está instalado. "
            "Instale com: pip install boto3"
        )
    
    try:
        client = boto3.client('secretsmanager', region_name=region)
        
        logger.info(f"Buscando secret: {secret_name} na região {region}")
        
        response = client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in response:
            secret_dict = json.loads(response['SecretString'])
            logger.info(f"Secret {secret_name} carregado com sucesso ({len(secret_dict)} chaves)")
            return secret_dict
        else:
            logger.warning(f"Secret {secret_name} não contém SecretString")
            return None
            
    except client.exceptions.ResourceNotFoundException:
        logger.error(f"Secret {secret_name} não encontrado no AWS Secrets Manager")
        raise
    except ClientError as e:
        logger.error(f"Erro ao buscar secret {secret_name}: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar secret {secret_name}: {e}")
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar secret {secret_name}: {e}")
        raise


def update_settings_from_secrets(settings_class, secrets: Dict[str, Any]) -> None:
    """
    Atualiza instância de Settings com secrets do AWS.
    
    Args:
        settings_class: Instância de Settings (app.settings.settings)
        secrets: Dict com secrets carregados
    """
    for key, value in secrets.items():
        if hasattr(settings_class, key):
            current_value = getattr(settings_class, key)
            if current_value and current_value != value:
                logger.info(f"Sobrescrevendo {key} com valor do AWS Secrets Manager")
            elif not current_value:
                logger.info(f"Definindo {key} com valor do AWS Secrets Manager")
            setattr(settings_class, key, value)
        else:
            logger.warning(f"Chave {key} não encontrada em Settings")
