"""
Tenant Context — Nexo Basis Governador SaaS
=============================================
Gerencia o tenant ativo da sessão corrente via `contextvars`.

Como funciona:
- O middleware de webhook resolve o `tenant_id` a partir do payload Meta (Page ID).
- Ele chama `set_tenant(tenant_id)` logo na entrada do request.
- O `get_tenant()` pode ser chamado por qualquer parte do sistema (repository, RAG,
  construtor de prompt) sem precisar passar o ID explicitamente em cada função.

Isolamento RLS:
- O `get_connection()` no AuditRepository configura a sessão asyncpg com
  `SET LOCAL app.tenant_id = ...` antes de cada transação. Isso ativa a RLS
  definida na migration `001_multi_tenant_rls.sql`.
"""

from contextvars import ContextVar
from typing import Optional

# Variável de contexto isolada por request/task asyncio
_tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)


def set_tenant(tenant_id: str) -> None:
    """Define o tenant ativo para o contexto da coroutine corrente."""
    _tenant_id_var.set(tenant_id)


def clear_tenant() -> None:
    """Limpa o tenant ativo do contexto da coroutine corrente."""
    _tenant_id_var.set(None)


def get_tenant() -> Optional[str]:
    """Retorna o tenant ativo. Retorna None se não configurado."""
    return _tenant_id_var.get()


def require_tenant() -> str:
    """
    Retorna o tenant ativo ou levanta ValueError se não configurado.
    Use em operações que nunca devem rodar sem tenant isolado.
    """
    tenant_id = _tenant_id_var.get()
    if not tenant_id:
        raise ValueError(
            "Nenhum tenant_id ativo no contexto. "
            "O middleware de webhook deve ser executado antes de qualquer operação de dados."
        )
    return tenant_id
