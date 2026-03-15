"""Catálogo mínimo de artefatos versionáveis da Fase 2."""

from app.llmops.active_artifacts import ActiveArtifactResolver, ActiveJsonArtifact, ActiveTextArtifact
from app.llmops.artifact_catalog import (
    AI_ARTIFACTS_DIR,
    PHASE2_ARTIFACT_CATALOG,
    Phase2ArtifactCatalog,
    VersionedArtifactDescriptor,
)
from app.llmops.versioning import (
    ArtifactVersionMetadata,
    ArtifactVersionStatus,
    build_artifact_metadata,
    build_content_hash,
    build_version_id,
    canonicalize_artifact_content,
    load_artifact_metadata,
)

__all__ = [
    "AI_ARTIFACTS_DIR",
    "ActiveArtifactResolver",
    "ActiveTextArtifact",
    "ActiveJsonArtifact",
    "VersionedArtifactDescriptor",
    "Phase2ArtifactCatalog",
    "PHASE2_ARTIFACT_CATALOG",
    "ArtifactVersionMetadata",
    "ArtifactVersionStatus",
    "canonicalize_artifact_content",
    "build_content_hash",
    "build_version_id",
    "build_artifact_metadata",
    "load_artifact_metadata",
]
