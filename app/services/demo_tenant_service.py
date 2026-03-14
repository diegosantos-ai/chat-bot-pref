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
    telegram_enabled: bool = False

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


class ControlledRetrievalCheck(BaseModel):
    id: str
    question: str
    expected_title_contains: str
    expected_terms: list[str]
    chat_expected_terms: list[str] = Field(default_factory=list)
    use_in_chat: bool = False

    @field_validator("id", "question", "expected_title_contains", mode="before")
    @classmethod
    def normalize_text_fields(cls, value: Any, info) -> str:
        return _normalize_text(value, info.field_name)

    @field_validator("expected_terms", mode="before")
    @classmethod
    def normalize_expected_terms(cls, value: Any, info) -> list[str]:
        return _normalize_list(value, info.field_name)

    @field_validator("chat_expected_terms", mode="before")
    @classmethod
    def normalize_optional_terms(cls, value: Any) -> list[str]:
        if value in (None, ""):
            return []
        return _normalize_list(value, "chat_expected_terms")


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

    def load_knowledge_manifest(self, manifest_path: str | Path) -> dict[str, Any]:
        knowledge_manifest_path = self.knowledge_manifest_path(manifest_path)
        if not knowledge_manifest_path.exists():
            return {}
        return json.loads(knowledge_manifest_path.read_text(encoding="utf-8"))

    def retrieval_checks_path(self, manifest_path: str | Path) -> Path | None:
        knowledge_manifest = self.load_knowledge_manifest(manifest_path)
        raw_path = str(knowledge_manifest.get("retrieval_checks_file", "")).strip()
        if not raw_path:
            return None
        relative_path = Path(raw_path)
        if relative_path.is_absolute():
            raise ValueError("retrieval_checks_file deve ser relativo ao tenant bundle")
        return self.bundle_root(manifest_path) / relative_path

    def load_retrieval_checks(self, manifest_path: str | Path) -> list[ControlledRetrievalCheck]:
        checks_path = self.retrieval_checks_path(manifest_path)
        if checks_path is None or not checks_path.exists():
            return []
        payload = json.loads(checks_path.read_text(encoding="utf-8"))
        return [
            ControlledRetrievalCheck.model_validate(item)
            for item in payload.get("checks", [])
        ]

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

    def validate_knowledge_base_bundle(self, manifest_path: str | Path) -> dict[str, Any]:
        manifest = self.load_manifest(manifest_path)
        knowledge_manifest = self.load_knowledge_manifest(manifest_path)
        documents = self.list_source_documents(manifest_path)
        retrieval_checks = self.load_retrieval_checks(manifest_path)

        listed_documents = sorted(
            Path(str(item).strip()).name
            for item in knowledge_manifest.get("documents", [])
            if str(item).strip()
        )
        document_names = sorted(
            path.name for path in self.documents_dir(manifest_path).glob("*.json")
        )

        groups = knowledge_manifest.get("document_groups", [])
        group_names = {
            str(group.get("group", "")).strip()
            for group in groups
            if str(group.get("group", "")).strip()
        }
        grouped_documents = sorted(
            {
                Path(str(document).strip()).name
                for group in groups
                for document in group.get("documents", [])
                if str(document).strip()
            }
        )
        group_sizes = {
            str(group.get("group", "")).strip(): len(
                [document for document in group.get("documents", []) if str(document).strip()]
            )
            for group in groups
            if str(group.get("group", "")).strip()
        }

        required_group_names = {"institucional", "atendimento", "servicos", "faq"}
        covers_required_groups = required_group_names.issubset(group_names)
        balanced_group_sizes = (
            group_sizes.get("institucional", 0) >= 3
            and group_sizes.get("atendimento", 0) >= 2
            and group_sizes.get("servicos", 0) >= 4
            and group_sizes.get("faq", 0) >= 1
        )

        criteria = [
            AcceptanceCriterion(
                criterion="documentos ficticios criados e organizados",
                ok=(
                    len(documents) >= 8
                    and listed_documents == document_names
                    and grouped_documents == document_names
                ),
                evidence=(
                    f"documents={len(documents)} | "
                    f"listed_documents={len(listed_documents)} | "
                    f"grouped_documents={len(grouped_documents)}"
                ),
            ),
            AcceptanceCriterion(
                criterion="base cobre os principais temas da prefeitura ficticia",
                ok=(
                    covers_required_groups
                    and balanced_group_sizes
                    and len(retrieval_checks) >= 6
                ),
                evidence=(
                    f"groups={sorted(group_names)} | "
                    f"group_sizes={group_sizes} | "
                    f"retrieval_checks={len(retrieval_checks)}"
                ),
            ),
        ]

        retrieval_checks_path = self.retrieval_checks_path(manifest_path)

        return {
            "tenant_id": manifest.tenant_id,
            "client_name": manifest.client_name,
            "status": "passed" if all(item.ok for item in criteria) else "failed",
            "documents_count": len(documents),
            "groups": sorted(group_names),
            "retrieval_checks_count": len(retrieval_checks),
            "retrieval_checks_path": str(retrieval_checks_path) if retrieval_checks_path else None,
            "criteria": [asdict(item) for item in criteria],
        }

    def build_phase8_managerial_report(
        self,
        manifest_path: str | Path,
        runtime_validation: dict[str, Any],
    ) -> dict[str, Any]:
        bundle_validation = self.validate_knowledge_base_bundle(manifest_path)
        criteria = list(bundle_validation["criteria"])

        ingest_validation = runtime_validation.get("ingest_validation", {})
        retrieval_validation = runtime_validation.get("retrieval_validation", {})
        empty_state_validation = runtime_validation.get("empty_state_validation", {})

        criteria.extend(
            [
                {
                    "criterion": "ingest executada sem acoplamento legado",
                    "ok": bool(ingest_validation.get("ok")),
                    "evidence": str(ingest_validation.get("evidence", "")),
                },
                {
                    "criterion": "retrieval retorna contexto util para perguntas controladas",
                    "ok": bool(retrieval_validation.get("ok")),
                    "evidence": str(retrieval_validation.get("evidence", "")),
                },
                {
                    "criterion": "ausencia de base e tratada de forma controlada antes da ingest",
                    "ok": bool(empty_state_validation.get("ok")),
                    "evidence": str(empty_state_validation.get("evidence", "")),
                },
            ]
        )

        passed = sum(1 for item in criteria if item["ok"])
        total = len(criteria)

        return {
            "phase": "Fase 8 - Construcao da Base Documental Ficticia e Ingest Limpa",
            "tenant_id": bundle_validation["tenant_id"],
            "client_name": bundle_validation["client_name"],
            "status": "passed" if passed == total else "failed",
            "criteria_total": total,
            "criteria_passed": passed,
            "criteria_failed": total - passed,
            "executive_summary": (
                "Base documental ficticia pronta e retrieval controlado validado."
                if passed == total
                else "Base documental ficticia ainda possui pendencias de estrutura ou retrieval."
            ),
            "criteria": criteria,
        }

    def build_phase9_managerial_report(
        self,
        manifest_path: str | Path,
        runtime_validation: dict[str, Any],
    ) -> dict[str, Any]:
        validation = self.validate_bundle(manifest_path)
        manifest = self.load_manifest(manifest_path)

        criteria = [
            {
                "criterion": "bot Telegram configurado para o tenant demonstrativo",
                "ok": bool(manifest.channels.telegram_enabled),
                "evidence": (
                    f"tenant_id={manifest.tenant_id} | "
                    f"telegram_enabled={manifest.channels.telegram_enabled}"
                ),
            },
            {
                "criterion": "integracao backend ↔ Telegram implementada",
                "ok": bool(runtime_validation.get("telegram_webhook_validation", {}).get("ok")),
                "evidence": str(
                    runtime_validation.get("telegram_webhook_validation", {}).get("evidence", "")
                ),
            },
            {
                "criterion": "tenant demonstrativo acessivel via Telegram",
                "ok": bool(runtime_validation.get("telegram_tenant_validation", {}).get("ok")),
                "evidence": str(
                    runtime_validation.get("telegram_tenant_validation", {}).get("evidence", "")
                ),
            },
            {
                "criterion": "mensagens simples respondidas corretamente",
                "ok": bool(runtime_validation.get("telegram_message_validation", {}).get("ok")),
                "evidence": str(
                    runtime_validation.get("telegram_message_validation", {}).get("evidence", "")
                ),
            },
            {
                "criterion": "logs e auditoria registram as interacoes com correlacao minima",
                "ok": bool(runtime_validation.get("telegram_audit_validation", {}).get("ok")),
                "evidence": str(
                    runtime_validation.get("telegram_audit_validation", {}).get("evidence", "")
                ),
            },
        ]

        passed = sum(1 for item in criteria if item["ok"])
        total = len(criteria)

        return {
            "phase": "Fase 9 - Operacionalizacao do Chat via Telegram",
            "tenant_id": validation["tenant_id"],
            "client_name": validation["client_name"],
            "status": "passed" if passed == total else "failed",
            "criteria_total": total,
            "criteria_passed": passed,
            "criteria_failed": total - passed,
            "executive_summary": (
                "Canal Telegram integrado ao fluxo principal do tenant demonstrativo."
                if passed == total
                else "Canal Telegram ainda possui pendencias de integracao ou rastreabilidade."
            ),
            "criteria": criteria,
        }

    def build_phase10_managerial_report(
        self,
        manifest_path: str | Path,
        runtime_validation: dict[str, Any],
    ) -> dict[str, Any]:
        validation = self.validate_bundle(manifest_path)

        criteria = [
            {
                "criterion": "adaptador de provedor LLM implementado e isolado do restante da aplicacao",
                "ok": bool(runtime_validation.get("llm_adapter_validation", {}).get("ok")),
                "evidence": str(runtime_validation.get("llm_adapter_validation", {}).get("evidence", "")),
            },
            {
                "criterion": "composicao de resposta limitada ao contexto recuperado e ao escopo institucional",
                "ok": bool(runtime_validation.get("composition_validation", {}).get("ok")),
                "evidence": str(runtime_validation.get("composition_validation", {}).get("evidence", "")),
            },
            {
                "criterion": "prompts e politicas versionados",
                "ok": bool(runtime_validation.get("prompt_policy_validation", {}).get("ok")),
                "evidence": str(runtime_validation.get("prompt_policy_validation", {}).get("evidence", "")),
            },
            {
                "criterion": "policy_pre e policy_post executados com reason_codes",
                "ok": bool(runtime_validation.get("policy_validation", {}).get("ok")),
                "evidence": str(runtime_validation.get("policy_validation", {}).get("evidence", "")),
            },
            {
                "criterion": "cenarios normais, fora de escopo, baixa confianca e risco validados",
                "ok": bool(runtime_validation.get("scenario_validation", {}).get("ok")),
                "evidence": str(runtime_validation.get("scenario_validation", {}).get("evidence", "")),
            },
            {
                "criterion": "evidencias registradas com correlacao minima por request_id",
                "ok": bool(runtime_validation.get("audit_validation", {}).get("ok")),
                "evidence": str(runtime_validation.get("audit_validation", {}).get("evidence", "")),
            },
            {
                "criterion": "comportamento alinhado ao escopo institucional do tenant ficticio",
                "ok": bool(runtime_validation.get("scope_validation", {}).get("ok")),
                "evidence": str(runtime_validation.get("scope_validation", {}).get("evidence", "")),
            },
        ]

        passed = sum(1 for item in criteria if item["ok"])
        total = len(criteria)

        return {
            "phase": "Fase 10 - Composicao Generativa, Guardrails e Evidencias",
            "tenant_id": validation["tenant_id"],
            "client_name": validation["client_name"],
            "status": "passed" if passed == total else "failed",
            "criteria_total": total,
            "criteria_passed": passed,
            "criteria_failed": total - passed,
            "executive_summary": (
                "Camada generativa minima, guardrails e trilha de evidencias validados para o tenant demonstrativo."
                if passed == total
                else "A camada generativa ou os guardrails ainda possuem pendencias de execucao e evidencia."
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
