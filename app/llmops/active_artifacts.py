"""Resolvedor dos artefatos ativos da Fase 2 usados pelo runtime atual."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from app.llmops.artifact_catalog import AI_ARTIFACTS_DIR, PHASE2_ARTIFACT_CATALOG, Phase2ArtifactCatalog
from app.llmops.artifact_catalog import VersionedArtifactDescriptor
from app.llmops.versioning import ArtifactVersionMetadata, build_content_hash, load_artifact_metadata
from app.settings import settings


@dataclass(frozen=True, slots=True)
class ActiveTextArtifact:
    """Representa um artefato textual ativo resolvido para o runtime."""

    descriptor: VersionedArtifactDescriptor
    metadata: ArtifactVersionMetadata
    path: Path
    content: str

    @property
    def version(self) -> str:
        """Retorna o rótulo de versão ativa do artefato."""

        return self.metadata.version_label

    @property
    def version_id(self) -> str:
        """Retorna o identificador comparável da versão ativa."""

        return self.metadata.version_id


@dataclass(frozen=True, slots=True)
class ActiveJsonArtifact:
    """Representa um artefato JSON ativo resolvido para o runtime."""

    descriptor: VersionedArtifactDescriptor
    metadata: ArtifactVersionMetadata
    path: Path
    payload: dict[str, Any]

    @property
    def version(self) -> str:
        """Retorna o rótulo de versão ativa do artefato."""

        return self.metadata.version_label

    @property
    def version_id(self) -> str:
        """Retorna o identificador comparável da versão ativa."""

        return self.metadata.version_id


class ActiveArtifactResolver:
    """Resolve e valida a versão ativa dos artefatos versionáveis da Fase 2."""

    def __init__(
        self,
        *,
        catalog: Phase2ArtifactCatalog | None = None,
        artifacts_dir: Path | None = None,
    ) -> None:
        self.catalog = catalog or PHASE2_ARTIFACT_CATALOG
        self.artifacts_dir = artifacts_dir or AI_ARTIFACTS_DIR

    def resolve_composer_prompt(self) -> ActiveTextArtifact:
        """Resolve o prompt principal ativo."""

        return self._resolve_text_artifact(self.catalog.composer_prompt)

    def resolve_fallback_prompt(self) -> ActiveTextArtifact:
        """Resolve o prompt de fallback ativo."""

        return self._resolve_text_artifact(self.catalog.fallback_prompt)

    def resolve_policy_text(self) -> ActiveTextArtifact:
        """Resolve a policy textual ativa."""

        return self._resolve_text_artifact(self.catalog.policy_text)

    def resolve_retrieval_config(self) -> ActiveJsonArtifact:
        """Resolve a configuração ativa de retrieval."""

        return self._resolve_json_artifact(self.catalog.retrieval_config)

    def resolve_chunking_config(self) -> ActiveJsonArtifact:
        """Resolve a configuração ativa de chunking."""

        return self._resolve_json_artifact(self.catalog.chunking_config)

    def retrieval_top_k_default(self) -> int:
        """Retorna o `top_k` ativo do runtime com fallback explícito para settings."""

        payload = self.resolve_retrieval_config().payload
        raw_value = payload.get("top_k_default", settings.LLM_CONTEXT_TOP_K)
        top_k = int(raw_value)
        if top_k < 1:
            raise ValueError("top_k_default deve ser maior ou igual a 1.")
        return top_k

    def retrieval_embedding_version(self) -> str:
        """Retorna a versão ativa do embedding declarada para o retrieval."""

        payload = self.resolve_retrieval_config().payload
        return str(payload.get("embedding_version", settings.RAG_EMBEDDING_VERSION)).strip()

    def chunk_split_strategy(self) -> str:
        """Retorna a estratégia ativa de fracionamento textual."""

        payload = self.resolve_chunking_config().payload
        return str(payload.get("split_strategy", "double_newline_paragraphs")).strip()

    def chunk_section_id_template(self) -> str:
        """Retorna o template ativo de identificador de seção."""

        payload = self.resolve_chunking_config().payload
        return str(payload.get("section_id_template", "section-{index}")).strip()

    def chunk_empty_content_fallback(self) -> str:
        """Retorna a política de fallback para conteúdo vazio no chunking."""

        payload = self.resolve_chunking_config().payload
        return str(payload.get("empty_content_fallback", "full_content")).strip()

    def _resolve_text_artifact(self, descriptor: VersionedArtifactDescriptor) -> ActiveTextArtifact:
        """Carrega um artefato textual e valida sua consistência com o sidecar."""

        artifact_path = self._artifact_path(descriptor)
        metadata = self._load_and_validate_metadata(descriptor, artifact_path)
        return ActiveTextArtifact(
            descriptor=descriptor,
            metadata=metadata,
            path=artifact_path,
            content=artifact_path.read_text(encoding="utf-8"),
        )

    def _resolve_json_artifact(self, descriptor: VersionedArtifactDescriptor) -> ActiveJsonArtifact:
        """Carrega um artefato JSON e valida sua consistência com o sidecar."""

        artifact_path = self._artifact_path(descriptor)
        metadata = self._load_and_validate_metadata(descriptor, artifact_path)
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"O artefato JSON ativo deve ser um objeto: {artifact_path}")
        return ActiveJsonArtifact(
            descriptor=descriptor,
            metadata=metadata,
            path=artifact_path,
            payload=payload,
        )

    def _load_and_validate_metadata(
        self,
        descriptor: VersionedArtifactDescriptor,
        artifact_path: Path,
    ) -> ArtifactVersionMetadata:
        """Carrega o sidecar e valida sua consistência com o artefato ativo."""

        metadata = load_artifact_metadata(self._metadata_path(descriptor))
        if metadata.artifact_type != descriptor.artifact_type:
            raise ValueError(f"artifact_type inconsistente para {artifact_path}")
        if metadata.artifact_name != descriptor.artifact_name:
            raise ValueError(f"artifact_name inconsistente para {artifact_path}")
        if metadata.version_label != descriptor.version:
            raise ValueError(f"version_label inconsistente para {artifact_path}")
        if metadata.content_hash != build_content_hash(artifact_path):
            raise ValueError(f"content_hash inconsistente para {artifact_path}")
        return metadata

    def _artifact_path(self, descriptor: VersionedArtifactDescriptor) -> Path:
        """Resolve o caminho absoluto do artefato a partir da pasta ativa."""

        return self.artifacts_dir / descriptor.relative_path

    def _metadata_path(self, descriptor: VersionedArtifactDescriptor) -> Path:
        """Resolve o caminho absoluto do sidecar a partir da pasta ativa."""

        artifact_path = self._artifact_path(descriptor)
        return artifact_path.with_suffix(f"{artifact_path.suffix}.meta.json")
