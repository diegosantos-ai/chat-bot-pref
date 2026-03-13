from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.contracts.dto import RagDocumentRecord
from app.storage.document_repository import FileDocumentRepository

TENANT_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _normalize_text(value: Any, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{field_name} obrigatorio")
    return normalized


def _normalize_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} deve ser lista")
    normalized_items: list[str] = []
    for item in value:
        normalized = str(item).strip()
        if normalized and normalized not in normalized_items:
            normalized_items.append(normalized)
    if not normalized_items:
        raise ValueError(f"{field_name} deve ter ao menos um item")
    return normalized_items


class DemoTenantIdentity(BaseModel):
    municipality_name: str
    state_code: str
    institutional_summary: str
    institutional_voice: str
    official_website: str
    support_email: str

    @field_validator("*", mode="before")
    @classmethod
    def normalize_fields(cls, value: Any, info) -> str:
        return _normalize_text(value, info.field_name)


class DemoTenantScope(BaseModel):
    assistant_role: str
    covered_topics: list[str]
    out_of_scope: list[str]
    disclaimer: str

    @field_validator("assistant_role", "disclaimer", mode="before")
    @classmethod
    def normalize_text_fields(cls, value: Any, info) -> str:
        return _normalize_text(value, info.field_name)

    @field_validator("covered_topics", "out_of_scope", mode="before")
    @classmethod
    def normalize_list_fields(cls, value: Any, info) -> list[str]:
        return _normalize_list(value, info.field_name)


class DemoTenantChannels(BaseModel):
    web_chat_enabled: bool = True
    webhook_page_id: str | None = None

    @field_validator("webhook_page_id", mode="before")
    @classmethod
    def normalize_page_id(cls, value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class DemoTenantKnowledgeBase(BaseModel):
    manifest_file: str
    documents_dir: str

    @field_validator("manifest_file", "documents_dir", mode="before")
    @classmethod
    def normalize_relative_paths(cls, value: Any, info) -> str:
        normalized = _normalize_text(value, info.field_name)
        if Path(normalized).is_absolute():
            raise ValueError(f"{info.field_name} deve ser relativo ao tenant bundle")
        return normalized


class DemoTenantManifest(BaseModel):
    tenant_id: str
    client_name: str
    bot_name: str
    identity: DemoTenantIdentity
    scope: DemoTenantScope
    channels: DemoTenantChannels = Field(default_factory=DemoTenantChannels)
    knowledge_base: DemoTenantKnowledgeBase

    @field_validator("tenant_id", "client_name", "bot_name", mode="before")
    @classmethod
    def normalize_root_fields(cls, value: Any, info) -> str:
        return _normalize_text(value, info.field_name)

    @field_validator("tenant_id")
    @classmethod
    def validate_tenant_id(cls, value: str) -> str:
        if not TENANT_ID_PATTERN.match(value):
            raise ValueError("tenant_id deve usar letras minusculas, numeros e hifens")
        return value


@dataclass
class AcceptanceCriterion:
    criterion: str
    ok: bool
    evidence: str


class DemoTenantService:
    def load_manifest(self, manifest_path: str | Path) -> DemoTenantManifest:
        path = Path(manifest_path)
        return DemoTenantManifest.model_validate_json(path.read_text(encoding="utf-8"))

    def bundle_root(self, manifest_path: str | Path) -> Path:
        return Path(manifest_path).resolve().parent

    def tenant_readme_path(self, manifest_path: str | Path) -> Path:
        return self.bundle_root(manifest_path) / "README.md"

    def knowledge_manifest_path(self, manifest_path: str | Path) -> Path:
        manifest = self.load_manifest(manifest_path)
        return self.bundle_root(manifest_path) / manifest.knowledge_base.manifest_file

    def documents_dir(self, manifest_path: str | Path) -> Path:
        manifest = self.load_manifest(manifest_path)
        return self.bundle_root(manifest_path) / manifest.knowledge_base.documents_dir

    def list_source_documents(self, manifest_path: str | Path) -> list[RagDocumentRecord]:
        documents: list[RagDocumentRecord] = []
        for file_path in sorted(self.documents_dir(manifest_path).glob("*.json")):
            documents.append(RagDocumentRecord.model_validate_json(file_path.read_text(encoding="utf-8")))
        return documents

    def validate_bundle(self, manifest_path: str | Path) -> dict[str, Any]:
        manifest = self.load_manifest(manifest_path)
        bundle_root = self.bundle_root(manifest_path)
        readme_path = self.tenant_readme_path(manifest_path)
        knowledge_manifest_path = self.knowledge_manifest_path(manifest_path)
        documents_dir = self.documents_dir(manifest_path)
        source_documents = self.list_source_documents(manifest_path)

        listed_documents: list[str] = []
        knowledge_manifest_tenant_id = ""
        if knowledge_manifest_path.exists():
            knowledge_manifest = json.loads(knowledge_manifest_path.read_text(encoding="utf-8"))
            knowledge_manifest_tenant_id = str(knowledge_manifest.get("tenant_id", "")).strip()
            listed_documents = [
                Path(str(item).strip()).name
                for item in knowledge_manifest.get("documents", [])
                if str(item).strip()
            ]

        document_names = sorted(path.name for path in documents_dir.glob("*.json"))
        all_documents_match_tenant = all(
            document.tenant_id == manifest.tenant_id for document in source_documents
        )
        knowledge_manifest_matches_tenant = (
            not knowledge_manifest_tenant_id or knowledge_manifest_tenant_id == manifest.tenant_id
        )
        has_relative_bundle_paths = (
            not Path(manifest.knowledge_base.manifest_file).is_absolute()
            and not Path(manifest.knowledge_base.documents_dir).is_absolute()
        )

        criteria = [
            AcceptanceCriterion(
                criterion="nome do tenant definido e padronizado",
                ok=bool(manifest.client_name and manifest.bot_name and manifest.tenant_id),
                evidence=(
                    f"tenant_id={manifest.tenant_id} | "
                    f"client_name={manifest.client_name} | bot_name={manifest.bot_name}"
                ),
            ),
            AcceptanceCriterion(
                criterion="identidade textual institucional criada",
                ok=readme_path.exists() and bool(manifest.identity.institutional_summary),
                evidence=(
                    f"README={readme_path.name} | "
                    f"municipio={manifest.identity.municipality_name} | "
                    f"voz={manifest.identity.institutional_voice}"
                ),
            ),
            AcceptanceCriterion(
                criterion="configuracao do tenant criada sem hardcodes",
                ok=(
                    knowledge_manifest_path.exists()
                    and has_relative_bundle_paths
                    and knowledge_manifest_matches_tenant
                ),
                evidence=(
                    f"manifest={Path(manifest_path).name} | "
                    f"knowledge_manifest={knowledge_manifest_path.relative_to(bundle_root)} | "
                    f"documents_dir={manifest.knowledge_base.documents_dir} | "
                    f"knowledge_manifest_tenant={knowledge_manifest_tenant_id or manifest.tenant_id}"
                ),
            ),
            AcceptanceCriterion(
                criterion="escopo do assistente documentado",
                ok=bool(manifest.scope.covered_topics and manifest.scope.out_of_scope),
                evidence=(
                    f"role={manifest.scope.assistant_role} | "
                    f"covered_topics={len(manifest.scope.covered_topics)} | "
                    f"out_of_scope={len(manifest.scope.out_of_scope)}"
                ),
            ),
            AcceptanceCriterion(
                criterion="estrutura inicial do tenant preparada para ingest",
                ok=(
                    documents_dir.exists()
                    and len(source_documents) >= 3
                    and all_documents_match_tenant
                    and knowledge_manifest_matches_tenant
                    and sorted(listed_documents) == document_names
                ),
                evidence=(
                    f"documents={len(source_documents)} | "
                    f"dir={documents_dir.relative_to(bundle_root)} | "
                    f"tenant_match={all_documents_match_tenant} | "
                    f"listed_documents={len(listed_documents)}"
                ),
            ),
        ]

        return {
            "tenant_id": manifest.tenant_id,
            "client_name": manifest.client_name,
            "bot_name": manifest.bot_name,
            "bundle_root": str(bundle_root),
            "status": "passed" if all(item.ok for item in criteria) else "failed",
            "documents_count": len(source_documents),
            "documents": [document.title for document in source_documents],
            "criteria": [asdict(item) for item in criteria],
        }

    def build_managerial_report(self, manifest_path: str | Path) -> dict[str, Any]:
        validation = self.validate_bundle(manifest_path)
        criteria = validation["criteria"]
        passed = sum(1 for item in criteria if item["ok"])
        total = len(criteria)

        return {
            "phase": "Fase 7 - Construcao do Tenant Demonstrativo Ficticio",
            "tenant_id": validation["tenant_id"],
            "client_name": validation["client_name"],
            "status": validation["status"],
            "criteria_total": total,
            "criteria_passed": passed,
            "criteria_failed": total - passed,
            "executive_summary": (
                "Tenant demonstrativo coerente e pronto para ingest."
                if validation["status"] == "passed"
                else "Tenant demonstrativo ainda possui pendencias estruturais."
            ),
            "criteria": criteria,
        }

    def bootstrap_bundle(
        self,
        manifest_path: str | Path,
        target_base_dir: str | Path,
        purge_documents: bool = False,
    ) -> dict[str, Any]:
        manifest = self.load_manifest(manifest_path)
        source_documents = self.list_source_documents(manifest_path)
        document_repository = FileDocumentRepository(base_dir=target_base_dir)

        removed_documents = 0
        if purge_documents:
            removed_documents = document_repository.reset_documents(manifest.tenant_id)

        for document in source_documents:
            document_repository.save_document(document)

        status_payload = {
            "last_ingested_at": None,
            "documents_count": len(source_documents),
            "chunks_count": 0,
            "removed_collections": [],
            "source_bundle": str(Path(manifest_path).resolve()),
        }
        document_repository.write_ingest_status(manifest.tenant_id, status_payload)

        return {
            "tenant_id": manifest.tenant_id,
            "client_name": manifest.client_name,
            "bot_name": manifest.bot_name,
            "removed_documents_count": removed_documents,
            "documents_count": len(source_documents),
            "target_dir": str(document_repository.source_dir(manifest.tenant_id)),
            "status_file": str(document_repository.ingest_status_path(manifest.tenant_id)),
        }
