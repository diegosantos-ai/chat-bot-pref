"""Catálogo mínimo da Fase 2 para artefatos versionáveis de IA."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from app.settings import settings

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
AI_ARTIFACTS_DIR: Final[Path] = REPO_ROOT / "ai_artifacts"
PHASE2_CHUNKING_VERSION: Final[str] = "paragraph_split_v1"


@dataclass(frozen=True, slots=True)
class VersionedArtifactDescriptor:
    """Descreve um artefato versionável separado do código de aplicação."""

    artifact_type: str
    artifact_name: str
    category: str
    version: str
    relative_path: str
    description: str
    current_runtime_sources: tuple[str, ...] = ()

    def file_path(self) -> Path:
        """Resolve o caminho absoluto do artefato versionável no repositório."""

        return AI_ARTIFACTS_DIR / self.relative_path

    def metadata_path(self) -> Path:
        """Resolve o caminho absoluto do sidecar de metadados do artefato."""

        artifact_path = self.file_path()
        return artifact_path.with_suffix(f"{artifact_path.suffix}.meta.json")


@dataclass(frozen=True, slots=True)
class Phase2ArtifactCatalog:
    """Agrupa os artefatos versionáveis iniciais definidos para a Fase 2."""

    composer_prompt: VersionedArtifactDescriptor
    fallback_prompt: VersionedArtifactDescriptor
    policy_text: VersionedArtifactDescriptor
    retrieval_config: VersionedArtifactDescriptor
    chunking_config: VersionedArtifactDescriptor

    def all(self) -> tuple[VersionedArtifactDescriptor, ...]:
        """Retorna todos os descritores do catálogo em ordem estável."""

        return (
            self.composer_prompt,
            self.fallback_prompt,
            self.policy_text,
            self.retrieval_config,
            self.chunking_config,
        )


PHASE2_ARTIFACT_CATALOG: Final[Phase2ArtifactCatalog] = Phase2ArtifactCatalog(
    composer_prompt=VersionedArtifactDescriptor(
        artifact_type="prompt",
        artifact_name="composer_base",
        category="prompts/composer",
        version=settings.PROMPT_BASE_VERSION,
        relative_path=f"prompts/composer/{settings.PROMPT_BASE_VERSION}.txt",
        description="Prompt base de composição contextual.",
        current_runtime_sources=("app/services/prompt_service.py",),
    ),
    fallback_prompt=VersionedArtifactDescriptor(
        artifact_type="prompt",
        artifact_name="fallback_default",
        category="prompts/fallback",
        version=settings.PROMPT_FALLBACK_VERSION,
        relative_path=f"prompts/fallback/{settings.PROMPT_FALLBACK_VERSION}.txt",
        description="Prompt de fallback controlado para limites e baixa confiança.",
        current_runtime_sources=("app/services/prompt_service.py",),
    ),
    policy_text=VersionedArtifactDescriptor(
        artifact_type="policy",
        artifact_name="institutional_policy",
        category="guardrails/policies",
        version=settings.POLICY_TEXT_VERSION,
        relative_path=f"guardrails/policies/{settings.POLICY_TEXT_VERSION}.md",
        description="Policy textual versionada para guardrails e decisões de bloqueio/fallback.",
        current_runtime_sources=("app/services/prompt_service.py", "app/policy_guard/service.py"),
    ),
    retrieval_config=VersionedArtifactDescriptor(
        artifact_type="retrieval_config",
        artifact_name="tenant_chroma_hash",
        category="rag/retrieval",
        version=settings.RAG_RETRIEVER_VERSION,
        relative_path=f"rag/retrieval/{settings.RAG_RETRIEVER_VERSION}.json",
        description="Configuração versionável da estratégia de retrieval tenant-aware.",
        current_runtime_sources=("app/services/chat_service.py", "app/storage/chroma_repository.py"),
    ),
    chunking_config=VersionedArtifactDescriptor(
        artifact_type="chunking_config",
        artifact_name="paragraph_split",
        category="rag/chunking",
        version=PHASE2_CHUNKING_VERSION,
        relative_path=f"rag/chunking/{PHASE2_CHUNKING_VERSION}.json",
        description="Configuração versionável do fracionamento textual usado na ingestão.",
        current_runtime_sources=("app/services/rag_service.py",),
    ),
)
