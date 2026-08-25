"""Regression tests for release label and version synchronization."""

from __future__ import annotations

import pytest

from scripts.release_metadata import (
    ReleaseMetadataError,
    ensure_commit_matches,
    ensure_tag_absent,
    latest_stable_version,
    next_version,
    release_bump,
    validate_release,
)


@pytest.mark.parametrize(
    ("label", "expected_version"),
    [
        ("release:major", "2.0.0"),
        ("release:minor", "1.1.0"),
        ("release:patch", "1.0.2"),
    ],
)
def test_release_bumps_are_calculated_from_latest_stable_tag(
    label: str, expected_version: str
) -> None:
    """Major, minor and patch labels select their exact SemVer bump."""
    tags = ["0.16.1", "1.0.0", "1.0.1"]

    bump = release_bump(["bug", label])

    assert next_version(tags, bump) == expected_version


@pytest.mark.parametrize(
    "labels",
    [
        [],
        ["bug"],
        ["release:minor", "release:patch"],
        ["release:snapshot", "release:patch"],
    ],
)
def test_release_requires_exactly_one_release_label(labels: list[str]) -> None:
    """Missing and ambiguous release labels stop the release."""
    with pytest.raises(ReleaseMetadataError, match="Genau ein Release-Label"):
        release_bump(labels)


def test_release_rejects_manifest_version_mismatch() -> None:
    """A tag must never advance without the shipped manifest."""
    with pytest.raises(ReleaseMetadataError, match="stimmen nicht überein"):
        validate_release(
            labels=["release:patch"],
            tags=["1.0.1"],
            manifest_version="1.0.1",
        )


def test_release_rejects_existing_target_tag() -> None:
    """An already existing calculated tag stops the release before writing."""
    with pytest.raises(ReleaseMetadataError, match="existiert bereits"):
        ensure_tag_absent("1.0.2", ["1.0.1", "1.0.2"])


def test_release_rejects_commit_other_than_tested_commit() -> None:
    """The release must tag the exact commit whose CI run succeeded."""
    with pytest.raises(ReleaseMetadataError, match="Commit stimmen nicht überein"):
        ensure_commit_matches("checked-out-sha", "tested-sha")


def test_prerelease_tag_does_not_advance_stable_release_line() -> None:
    """Prereleases are not mistaken for the latest completed release."""
    assert next_version(["1.2.3", "1.3.0-rc.1"], "patch") == "1.2.4"


def test_snapshot_keeps_latest_stable_manifest_version() -> None:
    """Snapshot PRs package a prerelease without changing tracked metadata."""
    assert (
        validate_release(
            labels=["release:snapshot"],
            tags=["1.0.8", "snapshot-pr-121-0123456789ab"],
            manifest_version="1.0.8",
        )
        == "1.0.8"
    )


def test_snapshot_rejects_stable_manifest_bump() -> None:
    """Snapshot development cannot reserve or replace a stable version."""
    with pytest.raises(ReleaseMetadataError, match="beibehalten"):
        validate_release(
            labels=["release:snapshot"],
            tags=["1.0.8"],
            manifest_version="1.0.9",
        )


def test_snapshot_requires_existing_stable_release() -> None:
    """A snapshot must always identify its stable production baseline."""
    with pytest.raises(ReleaseMetadataError, match="Kein stabiler SemVer-Tag"):
        latest_stable_version(["snapshot-pr-121-0123456789ab"])


@pytest.mark.parametrize("version", ["v1.0.2", "1.0", "01.0.2", "1.0.2-rc.1"])
def test_release_rejects_non_stable_manifest_semver(version: str) -> None:
    """The shipped version must use the exact stable SemVer tag format."""
    with pytest.raises(ReleaseMetadataError, match="kein stabiles SemVer"):
        validate_release(
            labels=["release:patch"],
            tags=["1.0.1"],
            manifest_version=version,
        )
