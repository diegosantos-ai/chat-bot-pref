from collections.abc import Mapping

from app.settings import settings


def _normalize_identifier(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized


class TenantResolutionError(ValueError):
    pass


class TenantResolver:
    def __init__(self, page_tenant_map: Mapping[str, str] | None = None) -> None:
        self.page_tenant_map = {
            str(key).strip(): str(item).strip()
            for key, item in (page_tenant_map or settings.WEBHOOK_PAGE_TENANT_MAP).items()
            if str(key).strip() and str(item).strip()
        }

    def resolve_webhook_tenant(
        self,
        tenant_id: str | None,
        page_id: str | None,
    ) -> str:
        normalized_tenant = _normalize_identifier(tenant_id)
        normalized_page = _normalize_identifier(page_id)

        if normalized_tenant is not None and normalized_page is None:
            return normalized_tenant

        if normalized_page is not None:
            resolved_tenant = self.page_tenant_map.get(normalized_page)
            if normalized_tenant is not None:
                if resolved_tenant is None:
                    return normalized_tenant
                if resolved_tenant != normalized_tenant:
                    raise TenantResolutionError("tenant_id divergente do page_id informado")
                return normalized_tenant
            if resolved_tenant is None:
                raise TenantResolutionError("tenant_id não resolvido para page_id informado")
            return resolved_tenant

        raise TenantResolutionError("tenant_id obrigatório ou page_id configurado no webhook")
