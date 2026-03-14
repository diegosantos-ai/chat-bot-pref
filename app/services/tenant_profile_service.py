from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.demo_tenant_service import DemoTenantManifest, DemoTenantService


@dataclass(frozen=True)
class TenantProfile:
    tenant_id: str
    client_name: str
    bot_name: str
    assistant_role: str
    institutional_voice: str
    disclaimer: str
    official_website: str
    support_email: str


class TenantProfileService:
    def __init__(self, demo_tenant_service: DemoTenantService | None = None) -> None:
        self.demo_tenant_service = demo_tenant_service or DemoTenantService()
        self.tenants_dir = Path(__file__).resolve().parents[2] / "tenants"

    def get_profile(self, tenant_id: str) -> TenantProfile:
        manifest = self._load_manifest(tenant_id)
        if manifest is None:
            return TenantProfile(
                tenant_id=tenant_id,
                client_name=f"tenant '{tenant_id}'",
                bot_name="Assistente Institucional",
                assistant_role="Assistente digital institucional para orientacoes informativas.",
                institutional_voice="Clara, objetiva e estritamente informativa.",
                disclaimer=(
                    "Este assistente oferece apenas informacoes gerais e nao substitui "
                    "atendimento humano ou protocolo oficial."
                ),
                official_website="",
                support_email="",
            )

        return TenantProfile(
            tenant_id=manifest.tenant_id,
            client_name=manifest.client_name,
            bot_name=manifest.bot_name,
            assistant_role=manifest.scope.assistant_role,
            institutional_voice=manifest.identity.institutional_voice,
            disclaimer=manifest.scope.disclaimer,
            official_website=manifest.identity.official_website,
            support_email=manifest.identity.support_email,
        )

    def _load_manifest(self, tenant_id: str) -> DemoTenantManifest | None:
        if not self.tenants_dir.exists():
            return None

        for manifest_path in sorted(self.tenants_dir.glob("*/tenant.json")):
            manifest = self.demo_tenant_service.load_manifest(manifest_path)
            if manifest.tenant_id == tenant_id:
                return manifest
        return None
