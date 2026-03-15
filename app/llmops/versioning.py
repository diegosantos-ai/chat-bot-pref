"""Contratos e utilitários de versionamento da Fase 2 para artefatos de IA."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from app.llmops.artifact_catalog import VersionedArtifactDescriptor


class ArtifactVersionStatus(StrEnum):
    """Estados mínimos de promoção aceitos para um artefato versionável."""

    DRAFT = "draft"
    CANDIDATE = "candidate"
    PROMOTED = "promoted"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True, slots=True)
class ArtifactVersionMetadata:
    """Representa o contrato mínimo de metadados de uma versão de artefato."""

    artifact_type: str
    artifact_name: str
    version_label: str
    version_id: str
    content_hash: str
    status: ArtifactVersionStatus
    created_at: str
    notes: str

    def __post_init__(self) -> None:
        """Valida a presença dos campos mínimos obrigatórios do contrato."""

        required_fields = {
            "artifact_type": self.artifact_type,
            "artifact_name": self.artifact_name,
            "version_label": self.version_label,
            "version_id": self.version_id,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "notes": self.notes,
        }
        for field_name, value in required_fields.items():
            if not str(value).strip():
                raise ValueError(f"Campo obrigatório ausente no metadado: {field_name}")

    def as_dict(self) -> dict[str, str]:
        """Converte o contrato em dicionário serializável para sidecar JSON."""

        return {
            "artifact_type": self.artifact_type,
            "artifact_name": self.artifact_name,
            "version_label": self.version_label,
            "version_id": self.version_id,
            "content_hash": self.content_hash,
            "status": self.status.value,
            "created_at": self.created_at,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ArtifactVersionMetadata":
        """Reconstrói o contrato a partir de um sidecar JSON."""

        return cls(
            artifact_type=str(payload.get("artifact_type", "")),
            artifact_name=str(payload.get("artifact_name", "")),
            version_label=str(payload.get("version_label", "")),
            version_id=str(payload.get("version_id", "")),
            content_hash=str(payload.get("content_hash", "")),
            status=ArtifactVersionStatus(str(payload.get("status", ""))),
            created_at=str(payload.get("created_at", "")),
            notes=str(payload.get("notes", "")),
        )


def canonicalize_artifact_content(artifact_path: Path) -> str:
    """Normaliza o conteúdo relevante do artefato para comparação estável."""

    raw_content = artifact_path.read_text(encoding="utf-8")
    if artifact_path.suffix.lower() == ".json":
        payload = json.loads(raw_content)
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    normalized_lines = [line.rstrip() for line in raw_content.replace("\r\n", "\n").split("\n")]
    return "\n".join(normalized_lines).strip()


def build_content_hash(artifact_path: Path) -> str:
    """Gera um hash SHA-256 estável a partir do conteúdo relevante do artefato."""

    canonical_content = canonicalize_artifact_content(artifact_path)
    return hashlib.sha256(canonical_content.encode("utf-8")).hexdigest()


def build_version_id(
    *,
    artifact_type: str,
    artifact_name: str,
    version_label: str,
    content_hash: str,
) -> str:
    """Gera um identificador estável e comparável a partir do contrato e do hash do conteúdo."""

    stable_seed = f"{artifact_type}:{artifact_name}:{version_label}:{content_hash}"
    short_hash = hashlib.sha256(stable_seed.encode("utf-8")).hexdigest()[:12]
    return f"{artifact_type}.{artifact_name}.{version_label}.{short_hash}"


def build_artifact_metadata(
    descriptor: VersionedArtifactDescriptor,
    *,
    status: ArtifactVersionStatus,
    created_at: str,
    notes: str,
) -> ArtifactVersionMetadata:
    """Constroi o metadado mínimo de um artefato versionável a partir do catálogo."""

    artifact_path = descriptor.file_path()
    content_hash = build_content_hash(artifact_path)
    version_id = build_version_id(
        artifact_type=descriptor.artifact_type,
        artifact_name=descriptor.artifact_name,
        version_label=descriptor.version,
        content_hash=content_hash,
    )
    return ArtifactVersionMetadata(
        artifact_type=descriptor.artifact_type,
        artifact_name=descriptor.artifact_name,
        version_label=descriptor.version,
        version_id=version_id,
        content_hash=content_hash,
        status=status,
        created_at=created_at,
        notes=notes,
    )


def load_artifact_metadata(metadata_path: Path) -> ArtifactVersionMetadata:
    """Carrega e valida o sidecar de metadados de uma versão de artefato."""

    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    return ArtifactVersionMetadata.from_dict(payload)
