from contextvars import ContextVar

_tenant_id_var: ContextVar[str | None] = ContextVar("tenant_id", default=None)


def set_tenant(tenant_id: str) -> None:
    _tenant_id_var.set(tenant_id)


def get_tenant() -> str | None:
    return _tenant_id_var.get()


def clear_tenant() -> None:
    _tenant_id_var.set(None)


def require_tenant() -> str:
    tenant_id = get_tenant()
    if tenant_id is None:
        raise RuntimeError("tenant_id ausente no contexto")
    return tenant_id
