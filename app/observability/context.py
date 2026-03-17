from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class CorrelationContext:
    request_id: str = ""
    tenant_id: str = ""
    session_id: str = ""
    channel: str = ""
    method: str = ""
    path: str = ""


_context_var: ContextVar[CorrelationContext] = ContextVar(
    "chat_pref_correlation_context",
    default=CorrelationContext(),
)


def get_correlation_context() -> CorrelationContext:
    return _context_var.get()


def set_correlation_context(
    *,
    request_id: str = "",
    tenant_id: str = "",
    session_id: str = "",
    channel: str = "",
    method: str = "",
    path: str = "",
) -> Token[CorrelationContext]:
    context = CorrelationContext(
        request_id=request_id.strip(),
        tenant_id=tenant_id.strip(),
        session_id=session_id.strip(),
        channel=channel.strip(),
        method=method.strip(),
        path=path.strip(),
    )
    return _context_var.set(context)


def update_correlation_context(**values: str) -> CorrelationContext:
    current = get_correlation_context()
    normalized = {
        key: str(value).strip()
        for key, value in values.items()
        if value is not None and hasattr(current, key)
    }
    updated = replace(current, **normalized)
    _context_var.set(updated)
    return updated


def reset_correlation_context(token: Token[CorrelationContext]) -> None:
    _context_var.reset(token)
