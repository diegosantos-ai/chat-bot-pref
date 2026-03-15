import json
from pathlib import Path

import pytest

from app.llmops import (
    PHASE2_ARTIFACT_CATALOG,
    ArtifactVersionStatus,
    build_artifact_metadata,
    build_content_hash,
    build_version_id,
    canonicalize_artifact_content,
    load_artifact_metadata,
)
from app.llmops.versioning import ArtifactVersionMetadata


def test_version_id_is_stable_when_content_does_not_change(tmp_path) -> None:
    artifact_path = tmp_path / "prompt_v1.txt"
    artifact_path.write_text("Linha 1\nLinha 2\n", encoding="utf-8")

    first_hash = build_content_hash(artifact_path)
    second_hash = build_content_hash(artifact_path)

    assert first_hash == second_hash
    assert build_version_id(
        artifact_type="prompt",
        artifact_name="composer_base",
        version_label="base_v1",
        content_hash=first_hash,
    ) == build_version_id(
        artifact_type="prompt",
        artifact_name="composer_base",
        version_label="base_v1",
        content_hash=second_hash,
    )


def test_version_id_changes_when_relevant_content_changes(tmp_path) -> None:
    original_path = tmp_path / "retrieval_a.json"
    changed_path = tmp_path / "retrieval_b.json"
    original_path.write_text(json.dumps({"top_k": 3, "scope": "tenant_aware"}), encoding="utf-8")
    changed_path.write_text(json.dumps({"top_k": 5, "scope": "tenant_aware"}), encoding="utf-8")

    original_hash = build_content_hash(original_path)
    changed_hash = build_content_hash(changed_path)

    assert original_hash != changed_hash
    assert build_version_id(
        artifact_type="retrieval_config",
        artifact_name="tenant_chroma_hash",
        version_label="tenant_chroma_hash_v1",
        content_hash=original_hash,
    ) != build_version_id(
        artifact_type="retrieval_config",
        artifact_name="tenant_chroma_hash",
        version_label="tenant_chroma_hash_v1",
        content_hash=changed_hash,
    )


def test_json_canonicalization_ignores_key_order(tmp_path) -> None:
    left_path = tmp_path / "left.json"
    right_path = tmp_path / "right.json"
    left_path.write_text('{"a":1,"b":2}', encoding="utf-8")
    right_path.write_text('{"b":2,"a":1}', encoding="utf-8")

    assert canonicalize_artifact_content(left_path) == canonicalize_artifact_content(right_path)
    assert build_content_hash(left_path) == build_content_hash(right_path)


def test_metadata_validation_requires_required_fields() -> None:
    with pytest.raises(ValueError):
        ArtifactVersionMetadata(
            artifact_type="prompt",
            artifact_name="",
            version_label="base_v1",
            version_id="prompt.composer_base.base_v1.abc123",
            content_hash="deadbeef",
            status=ArtifactVersionStatus.CANDIDATE,
            created_at="2026-03-15T00:00:00Z",
            notes="sem nome",
        )


def test_example_metadata_files_match_catalog_and_content() -> None:
    created_at = "2026-03-15T00:00:00Z"

    for artifact in PHASE2_ARTIFACT_CATALOG.all():
        stored_metadata = load_artifact_metadata(artifact.metadata_path())
        rebuilt_metadata = build_artifact_metadata(
            artifact,
            status=stored_metadata.status,
            created_at=created_at,
            notes=stored_metadata.notes,
        )

        assert stored_metadata.artifact_type == artifact.artifact_type
        assert stored_metadata.artifact_name == artifact.artifact_name
        assert stored_metadata.version_label == artifact.version
        assert stored_metadata.content_hash == rebuilt_metadata.content_hash
        assert stored_metadata.version_id == rebuilt_metadata.version_id
