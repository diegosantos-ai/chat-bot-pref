"""
API endpoint para chat com a {bot_name}.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from uuid import uuid4
from app.extensions import limiter

from app.contracts.dto import ChatRequest, ChatResponse
from app.contracts.enums import Channel, SurfaceType
from app.orchestrator.service import OrchestratorService
from app.settings import settings
from app import tenant_context

router = APIRouter(prefix="/api", tags=["Chat"])

# Instância única do orchestrator
_orchestrator: OrchestratorService | None = None

# Use the shared `limiter` imported from `app.extensions` (configured by the app)


def get_orchestrator() -> OrchestratorService:
    """Retorna instância singleton do OrchestratorService."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorService()
    return _orchestrator


def _bind_chat_tenant(tenant_id: str | None) -> str:
    """Exige tenant_id explícito no chat direto e injeta no contextvars."""
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id obrigatório")
    tenant_context.set_tenant(tenant_id)
    return tenant_id


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def chat(
    request: Request, response: Response, chat_request: ChatRequest
) -> ChatResponse:
    """
    Processa uma mensagem do usuário e retorna a resposta da {bot_name}.

    **Exemplo de request:**
    ```json
    {
        "tenant_id": "prefeitura_nova_esperanca",
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "message": "Qual o telefone da prefeitura?",
        "channel": "web",
        "surface_type": "inbox"
    }
    ```

    **Canais disponíveis:** web, instagram, facebook, whatsapp

    **Tipos de superfície:** inbox (privado), public_comment (comentário público)
    """
    try:
        _bind_chat_tenant(chat_request.tenant_id)

        # Gera session_id se não fornecido
        if not chat_request.session_id:
            chat_request.session_id = str(uuid4())

        orchestrator = get_orchestrator()
        chat_response, _ctx = await orchestrator.process(chat_request)

        return chat_response

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao processar mensagem: {str(e)}"
        )
    finally:
        tenant_context.clear_tenant()


@router.post("/chat/simple")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def chat_simple(
    request: Request,
    response: Response,
    message: str,
    tenant_id: str,
    channel: str = "web_widget",
    surface: str = "INBOX",
) -> dict:
    """
    Endpoint simplificado para testes rápidos.

    **Parâmetros:**
    - message: A pergunta do usuário
    - tenant_id: Identificador explícito do tenant
    - channel: Canal (web_widget, instagram_dm, facebook_dm)
    - surface: Tipo (INBOX, PUBLIC_COMMENT)

    **Exemplo:** POST /api/chat/simple?message=Qual o horário de atendimento?
    """
    try:
        _bind_chat_tenant(tenant_id)

        # Mapeia strings amigáveis para valores do enum
        channel_map = {
            "web": "web_widget",
            "web_widget": "web_widget",
            "instagram": "instagram_dm",
            "instagram_dm": "instagram_dm",
            "instagram_comment": "instagram_comment",
            "facebook": "facebook_dm",
            "facebook_dm": "facebook_dm",
            "facebook_comment": "facebook_comment",
        }

        surface_map = {
            "inbox": "INBOX",
            "INBOX": "INBOX",
            "dm": "INBOX",
            "private": "INBOX",
            "public": "PUBLIC_COMMENT",
            "public_comment": "PUBLIC_COMMENT",
            "PUBLIC_COMMENT": "PUBLIC_COMMENT",
            "comment": "PUBLIC_COMMENT",
        }

        channel_value = channel_map.get(channel.lower(), channel)
        surface_value = surface_map.get(surface, surface.upper())

        channel_enum = Channel(channel_value)
        surface_enum = SurfaceType(surface_value)

        chat_request = ChatRequest(
            session_id=str(uuid4()),
            message=message,
            tenant_id=tenant_id,
            channel=channel_enum,
            surface_type=surface_enum,
        )

        orchestrator = get_orchestrator()
        chat_response, _ctx = await orchestrator.process(chat_request)

        return {
            "pergunta": message,
            "tenant_id": tenant_id,
            "resposta": chat_response.message,
            "intent": chat_response.intent.value if chat_response.intent else None,
            "decision": chat_response.decision.value if chat_response.decision else None,
            "session_id": chat_response.session_id,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Parâmetro inválido: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao processar mensagem: {str(e)}"
        )
    finally:
        tenant_context.clear_tenant()
