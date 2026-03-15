from pathlib import Path

from app.llmops import AI_ARTIFACTS_DIR, PHASE2_ARTIFACT_CATALOG


def test_phase2_artifact_catalog_points_to_existing_versioned_files() -> None:
    assert AI_ARTIFACTS_DIR.is_dir()

    for artifact in PHASE2_ARTIFACT_CATALOG.all():
        assert artifact.file_path().is_file(), artifact.relative_path
        assert artifact.metadata_path().is_file(), artifact.metadata_path()


def test_phase2_artifact_catalog_keeps_runtime_sources_explicit() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    for artifact in PHASE2_ARTIFACT_CATALOG.all():
        assert artifact.current_runtime_sources
        for runtime_source in artifact.current_runtime_sources:
            assert (repo_root / runtime_source).exists(), runtime_source
