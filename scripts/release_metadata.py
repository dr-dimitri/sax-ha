"""Validate and calculate metadata for a SAX Power release."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

RELEASE_LABELS = {
    "release:major": "major",
    "release:minor": "minor",
    "release:patch": "patch",
}
STABLE_SEMVER_PATTERN = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)


class ReleaseMetadataError(ValueError):
    """Raised when release metadata is inconsistent."""


def release_bump(labels: Sequence[str]) -> str:
    """Return the single release bump selected by the pull request labels."""
    matching_labels = [label for label in labels if label in RELEASE_LABELS]
    if len(matching_labels) != 1:
        raise ReleaseMetadataError(
            "Genau ein Release-Label ist erforderlich; gefunden: "
            f"{len(matching_labels)}."
        )
    return RELEASE_LABELS[matching_labels[0]]


def next_version(tags: Sequence[str], bump: str) -> str:
    """Calculate the next stable SemVer version from the stable repository tags."""
    stable_versions = [
        tuple(int(part) for part in match.groups())
        for tag in tags
        if (match := STABLE_SEMVER_PATTERN.fullmatch(tag)) is not None
    ]
    major, minor, patch = max(stable_versions, default=(0, 0, 0))

    match bump:
        case "major":
            major, minor, patch = major + 1, 0, 0
        case "minor":
            minor, patch = minor + 1, 0
        case "patch":
            patch += 1
        case _:
            raise ReleaseMetadataError(f"Unbekannter Versionssprung: {bump}")

    return f"{major}.{minor}.{patch}"


def ensure_tag_absent(version: str, tags: Sequence[str]) -> None:
    """Stop before tag creation when the target ref already exists."""
    if version in tags:
        raise ReleaseMetadataError(f"Release-Tag existiert bereits: {version}")


def ensure_commit_matches(actual_commit: str, expected_commit: str) -> None:
    """Ensure the workflow tags exactly the commit already tested by CI."""
    if actual_commit != expected_commit:
        raise ReleaseMetadataError(
            "Getesteter und ausgecheckter Commit stimmen nicht überein: "
            f"{expected_commit} != {actual_commit}."
        )


def validate_release(
    *, labels: Sequence[str], tags: Sequence[str], manifest_version: str
) -> str:
    """Validate all release inputs and return the expected release version."""
    bump = release_bump(labels)
    expected_version = next_version(tags, bump)

    if STABLE_SEMVER_PATTERN.fullmatch(manifest_version) is None:
        raise ReleaseMetadataError(
            f"Manifest-Version ist kein stabiles SemVer: {manifest_version}"
        )
    if manifest_version != expected_version:
        raise ReleaseMetadataError(
            "Manifest-Version und nächste Release-Version stimmen nicht überein: "
            f"{manifest_version} != {expected_version}."
        )
    ensure_tag_absent(expected_version, tags)

    return expected_version


def _git_output(*arguments: str) -> str:
    result = subprocess.run(
        ("git", *arguments),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _parse_labels(labels_json: str) -> list[str]:
    labels = json.loads(labels_json)
    if not isinstance(labels, list) or not all(
        isinstance(label, str) for label in labels
    ):
        raise ReleaseMetadataError("PR_LABELS muss eine JSON-Liste aus Strings sein.")
    return labels


def _manifest_version(path: Path) -> str:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    version = manifest.get("version")
    if not isinstance(version, str):
        raise ReleaseMetadataError("manifest.json enthält keine Version als String.")
    return version


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels-json", required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("custom_components/sax_power/manifest.json"),
    )
    parser.add_argument("--expected-commit")
    parser.add_argument("--github-output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run release validation for CI or the release workflow."""
    arguments = _parser().parse_args(argv)
    try:
        labels = _parse_labels(arguments.labels_json)
        tags = _git_output("tag", "--list").splitlines()
        if arguments.expected_commit:
            actual_commit = _git_output("rev-parse", "HEAD")
            expected_commit = _git_output("rev-parse", arguments.expected_commit)
            ensure_commit_matches(actual_commit, expected_commit)

        version = validate_release(
            labels=labels,
            tags=tags,
            manifest_version=_manifest_version(arguments.manifest),
        )
    except (json.JSONDecodeError, OSError, subprocess.CalledProcessError) as err:
        print(f"Release-Metadaten konnten nicht gelesen werden: {err}", file=sys.stderr)
        return 1
    except ReleaseMetadataError as err:
        print(f"Release-Metadaten ungültig: {err}", file=sys.stderr)
        return 1

    print(f"Release-Metadaten sind konsistent: {version}")
    if arguments.github_output:
        with arguments.github_output.open("a", encoding="utf-8") as output:
            output.write(f"tag={version}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
