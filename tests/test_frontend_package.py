"""Verify that both installation paths contain the locally built Vue bundle."""

from __future__ import annotations

import io
import json
import shutil
import subprocess
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.snapshot_release import build_snapshot_archive
from scripts.verify_dashboard_package import (
    DashboardPackageError,
    verify_dashboard_package,
)

REPOSITORY_ROOT = Path(__file__).parents[1]
INTEGRATION_PATH = Path("custom_components/sax_power")
ASSET_PATH = Path("frontend/sax-power-vue.js")


def _git(repository: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
    ).stdout


def test_stable_source_and_snapshot_include_identical_frontend_assets(
    tmp_path: Path,
) -> None:
    """REQ-VUE-DASHBOARD: HACS and snapshots install without a frontend build."""
    source = tmp_path / "source"
    shutil.copytree(
        REPOSITORY_ROOT / INTEGRATION_PATH,
        source / INTEGRATION_PATH,
    )
    for name in ("hacs.json", ".gitignore", ".gitattributes"):
        if (REPOSITORY_ROOT / name).exists():
            shutil.copy2(REPOSITORY_ROOT / name, source / name)

    # GitHub's stable source archive contains tracked files; local test imports
    # must not accidentally add __pycache__ files to the snapshot fixture.
    _git(source, "init", "--quiet")
    _git(source, "add", ".")
    tree = _git(source, "write-tree").decode().strip()
    archive_bytes = _git(source, "archive", "--format=zip", tree)
    expected_asset = (REPOSITORY_ROOT / INTEGRATION_PATH / ASSET_PATH).read_bytes()
    assert expected_asset

    clean_source = tmp_path / "clean-source"
    with ZipFile(io.BytesIO(archive_bytes)) as stable_archive:
        hacs = json.loads(stable_archive.read("hacs.json"))
        assert hacs.get("content_in_root", False) is False
        assert hacs.get("zip_release", False) is False
        assert (
            stable_archive.read((INTEGRATION_PATH / ASSET_PATH).as_posix())
            == expected_asset
        )
        assert not any("__pycache__" in name for name in stable_archive.namelist())
        stable_archive.extractall(clean_source)

    snapshot = build_snapshot_archive(
        source_root=clean_source,
        output_directory=tmp_path / "snapshot",
        pull_request_number=197,
        commit="0123456789abcdef0123456789abcdef01234567",
    )
    with ZipFile(snapshot.archive) as snapshot_archive:
        assert (
            snapshot_archive.read((Path("sax_power") / ASSET_PATH).as_posix())
            == expected_asset
        )
        assert not any("__pycache__" in name for name in snapshot_archive.namelist())

    # REQ-VUE-PARITY: each layout is installed outside the repository and served
    # by a fresh HA process, so cached imports cannot hide missing package files.
    stable_package = tmp_path / "stable-source.zip"
    stable_package.write_bytes(
        _git(source, "archive", "--format=zip", "--prefix=sax-ha-reviewed/", tree)
    )
    stable_report = verify_dashboard_package(stable_package)
    snapshot_report = verify_dashboard_package(snapshot.archive)
    assert stable_report.asset_sha256 == snapshot_report.asset_sha256
    assert (
        stable_report.version
        == json.loads((clean_source / INTEGRATION_PATH / "manifest.json").read_text())[
            "version"
        ]
    )
    assert snapshot_report.version == snapshot.version
    assert stable_report.installed_files == snapshot_report.installed_files
    assert "2 passed" in stable_report.test_output
    assert "2 passed" in snapshot_report.test_output


@pytest.mark.parametrize(
    ("files", "message"),
    [
        ({"../outside.txt": b"outside"}, "Unsicherer Pfad"),
        ({"not-the-integration.txt": b"missing"}, "genau eine"),
        (
            {"sax_power/manifest.json": b'{"domain":"sax_power","version":"2.0.3"}'},
            "Installationsdateien fehlen",
        ),
    ],
)
def test_package_smoke_rejects_incomplete_or_unsafe_archives(
    tmp_path: Path, files: dict[str, bytes], message: str
) -> None:
    """REQ-VUE-PARITY: installation errors fail before importing any package."""
    archive = tmp_path / "invalid.zip"
    with ZipFile(archive, "w") as package:
        for name, contents in files.items():
            package.writestr(name, contents)
    with pytest.raises(DashboardPackageError, match=message):
        verify_dashboard_package(archive)
    assert not (tmp_path / "outside.txt").exists()
