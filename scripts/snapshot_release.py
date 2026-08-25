"""Build a deterministic, manually installable snapshot integration archive.

This script intentionally has no project imports. The privileged workflow executes
the copy from the trusted default branch with ``python -I`` while packaging an
untrusted pull-request checkout. Pull-request code is read as data, never executed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

STABLE_SEMVER_PATTERN = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class SnapshotReleaseError(ValueError):
    """Raised when a snapshot cannot be built safely."""


@dataclass(frozen=True)
class SnapshotArtifact:
    """Paths and immutable identifiers of one snapshot build."""

    tag: str
    version: str
    archive: Path
    checksum: Path


def snapshot_identifiers(
    stable_version: str, pull_request_number: int, commit: str
) -> tuple[str, str]:
    """Return an immutable tag and SemVer prerelease version for a tested SHA."""
    if STABLE_SEMVER_PATTERN.fullmatch(stable_version) is None:
        raise SnapshotReleaseError(
            f"Manifest-Version ist kein stabiles SemVer: {stable_version}"
        )
    if pull_request_number <= 0:
        raise SnapshotReleaseError("Pull-Request-Nummer muss positiv sein.")
    if COMMIT_PATTERN.fullmatch(commit) is None:
        raise SnapshotReleaseError("Commit muss ein vollständiger SHA-1 sein.")

    short_commit = commit[:12]
    return (
        f"snapshot-pr-{pull_request_number}-{short_commit}",
        f"{stable_version}-snapshot.pr{pull_request_number}.sha{short_commit}",
    )


def _safe_package_files(package_root: Path) -> list[Path]:
    if package_root.is_symlink():
        raise SnapshotReleaseError(
            f"Symlink als Integrationsverzeichnis nicht erlaubt: {package_root}"
        )
    if not package_root.is_dir():
        raise SnapshotReleaseError(f"Integrationsverzeichnis fehlt: {package_root}")

    files: list[Path] = []
    for path in package_root.rglob("*"):
        if path.is_symlink():
            raise SnapshotReleaseError(f"Symlink im Snapshot nicht erlaubt: {path}")
        if path.is_file():
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(package_root).as_posix())


def _zip_info(name: str) -> ZipInfo:
    info = ZipInfo(name, FIXED_ZIP_TIMESTAMP)
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def build_snapshot_archive(
    *,
    source_root: Path,
    output_directory: Path,
    pull_request_number: int,
    commit: str,
) -> SnapshotArtifact:
    """Package ``custom_components/sax_power`` without mutating the checkout."""
    package_root = source_root / "custom_components" / "sax_power"
    manifest_path = package_root / "manifest.json"
    files = _safe_package_files(package_root)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise SnapshotReleaseError(
            f"Manifest kann nicht gelesen werden: {err}"
        ) from err
    stable_version = manifest.get("version")
    if not isinstance(stable_version, str):
        raise SnapshotReleaseError("Manifest enthält keine Version als String.")

    tag, snapshot_version = snapshot_identifiers(
        stable_version, pull_request_number, commit
    )
    manifest["version"] = snapshot_version
    snapshot_manifest = (
        json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    )

    output_directory.mkdir(parents=True, exist_ok=True)
    archive = output_directory / f"sax_power-{tag}.zip"
    with ZipFile(archive, "w") as snapshot_zip:
        for path in files:
            relative = path.relative_to(package_root)
            archive_name = (PurePosixPath("sax_power") / relative.as_posix()).as_posix()
            content = snapshot_manifest if path == manifest_path else path.read_bytes()
            snapshot_zip.writestr(_zip_info(archive_name), content)

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_suffix(".zip.sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    return SnapshotArtifact(tag, snapshot_version, archive, checksum)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--github-output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Build one snapshot and optionally expose its metadata to Actions."""
    arguments = _parser().parse_args(argv)
    try:
        artifact = build_snapshot_archive(
            source_root=arguments.source,
            output_directory=arguments.output_directory,
            pull_request_number=arguments.pull_request,
            commit=arguments.commit,
        )
    except SnapshotReleaseError as err:
        print(f"Snapshot ungültig: {err}")
        return 1

    values = {
        "tag": artifact.tag,
        "version": artifact.version,
        "archive": str(artifact.archive),
        "checksum": str(artifact.checksum),
    }
    print(f"Snapshot {artifact.version} erstellt: {artifact.archive.name}")
    if arguments.github_output:
        with arguments.github_output.open("a", encoding="utf-8") as output:
            for key, value in values.items():
                output.write(f"{key}={value}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
