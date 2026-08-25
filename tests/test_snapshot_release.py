"""Regression tests for isolated and reproducible snapshot artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.snapshot_release import (
    SnapshotReleaseError,
    build_snapshot_archive,
    snapshot_identifiers,
)

COMMIT = "0123456789abcdef0123456789abcdef01234567"
REPOSITORY_ROOT = Path(__file__).parents[1]


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    package = source / "custom_components" / "sax_power"
    package.mkdir(parents=True)
    (package / "manifest.json").write_text(
        json.dumps({"domain": "sax_power", "version": "1.0.8"}),
        encoding="utf-8",
    )
    (package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    return source


def test_snapshot_identifiers_include_pr_and_full_tested_commit_identity() -> None:
    """Every tested PR head gets an immutable and recognizable identity."""
    tag, version = snapshot_identifiers("1.0.8", 121, COMMIT)

    assert tag == "snapshot-pr-121-0123456789ab"
    assert version == "1.0.8-snapshot.pr121.sha0123456789ab"


def test_snapshot_patches_only_packaged_manifest_and_writes_checksum(
    tmp_path: Path,
) -> None:
    """Packaging keeps the checkout stable while making the archive identifiable."""
    source = _source(tmp_path)
    original_manifest = (
        source / "custom_components" / "sax_power" / "manifest.json"
    ).read_text(encoding="utf-8")

    artifact = build_snapshot_archive(
        source_root=source,
        output_directory=tmp_path / "output",
        pull_request_number=121,
        commit=COMMIT,
    )

    with ZipFile(artifact.archive) as snapshot_zip:
        packaged_manifest = json.loads(
            snapshot_zip.read("sax_power/manifest.json").decode("utf-8")
        )
        assert snapshot_zip.read("sax_power/__init__.py") == b"VALUE = 1\n"
    assert packaged_manifest["version"] == artifact.version
    assert (source / "custom_components" / "sax_power" / "manifest.json").read_text(
        encoding="utf-8"
    ) == original_manifest

    expected_digest = hashlib.sha256(artifact.archive.read_bytes()).hexdigest()
    assert artifact.checksum.read_text(encoding="utf-8") == (
        f"{expected_digest}  {artifact.archive.name}\n"
    )


def test_snapshot_archive_is_reproducible(tmp_path: Path) -> None:
    """The same tested source produces byte-identical installation archives."""
    source = _source(tmp_path)
    first = build_snapshot_archive(
        source_root=source,
        output_directory=tmp_path / "first",
        pull_request_number=121,
        commit=COMMIT,
    )
    second = build_snapshot_archive(
        source_root=source,
        output_directory=tmp_path / "second",
        pull_request_number=121,
        commit=COMMIT,
    )

    assert first.archive.read_bytes() == second.archive.read_bytes()
    assert first.checksum.read_text(encoding="utf-8").split()[0] == (
        second.checksum.read_text(encoding="utf-8").split()[0]
    )


@pytest.mark.parametrize(
    ("version", "pull_request_number", "commit"),
    [
        ("1.0.8-rc.1", 121, COMMIT),
        ("1.0.8", 0, COMMIT),
        ("1.0.8", 121, "0123456789ab"),
    ],
)
def test_snapshot_rejects_ambiguous_identity(
    version: str, pull_request_number: int, commit: str
) -> None:
    """Invalid stable baselines or shortened identifiers cannot be published."""
    with pytest.raises(SnapshotReleaseError):
        snapshot_identifiers(version, pull_request_number, commit)


def test_snapshot_rejects_symlinks(tmp_path: Path) -> None:
    """PR content cannot make the privileged packager follow external paths."""
    source = _source(tmp_path)
    package = source / "custom_components" / "sax_power"
    (package / "unsafe.py").symlink_to(tmp_path / "outside.py")

    with pytest.raises(SnapshotReleaseError, match="Symlink"):
        build_snapshot_archive(
            source_root=source,
            output_directory=tmp_path / "output",
            pull_request_number=121,
            commit=COMMIT,
        )


def test_snapshot_rejects_symlinked_manifest_before_reading(tmp_path: Path) -> None:
    """Even metadata must not be read through a pull-request-controlled link."""
    source = _source(tmp_path)
    package = source / "custom_components" / "sax_power"
    manifest = package / "manifest.json"
    manifest.unlink()
    manifest.symlink_to(tmp_path / "outside.json")

    with pytest.raises(SnapshotReleaseError, match="Symlink"):
        build_snapshot_archive(
            source_root=source,
            output_directory=tmp_path / "output",
            pull_request_number=121,
            commit=COMMIT,
        )


def test_privileged_workflow_never_executes_pull_request_code() -> None:
    """The write-token workflow may only execute trusted default-branch tools."""
    workflow = (REPOSITORY_ROOT / ".github/workflows/snapshot-release.yaml").read_text(
        encoding="utf-8"
    )

    assert ".head.repo.full_name == $repository" in workflow
    assert "python -I trusted/scripts/snapshot_release.py" in workflow
    assert "working-directory: trusted" in workflow
    assert "python -I scripts/release_metadata.py" in workflow
    assert "python source" not in workflow
    assert "source/scripts" not in workflow
    assert workflow.count("persist-credentials: false") == 2


def test_stable_release_is_suppressed_after_accidental_snapshot_merge() -> None:
    """A merged snapshot label can never mint or replace a stable release."""
    workflow = (REPOSITORY_ROOT / ".github/workflows/release.yaml").read_text(
        encoding="utf-8"
    )

    assert workflow.count("'release:snapshot'") == 4
    assert "Snapshot-Merge ohne Produktiv-Release melden" in workflow
