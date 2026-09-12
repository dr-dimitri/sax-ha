"""Install and smoke-test the Vue panel from a stable or snapshot ZIP.

The isolated worker uses only the unpacked integration and installed Python test
dependencies. It does not start the SAX coordinator, connect to a battery or run
Node. Run with the repository's test venv: ``python -I .../this_script.py ZIP``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile


class DashboardPackageError(ValueError):
    """The archive cannot be installed or its isolated HA smoke check failed."""


@dataclass(frozen=True)
class DashboardPackageReport:
    """Identity of the immutable archive and its tested frontend."""

    version: str
    archive_sha256: str
    asset_sha256: str
    installed_files: int
    test_output: str


def _install_archive(archive: Path, destination: Path) -> tuple[str, str, int]:
    """Copy one integration from either HACS source or snapshot archive layout."""
    try:
        with ZipFile(archive) as package:
            files = [item for item in package.infolist() if not item.is_dir()]
            paths = [PurePosixPath(item.filename) for item in files]
            for item, path in zip(files, paths, strict=True):
                if (
                    path.is_absolute()
                    or ".." in path.parts
                    or "\\" in item.filename
                    or stat.S_ISLNK(item.external_attr >> 16)
                ):
                    raise DashboardPackageError("Unsicherer Pfad im ZIP-Archiv.")
            manifests = [
                path
                for path in paths
                if path.parts[-2:] == ("sax_power", "manifest.json")
            ]
            if len(manifests) != 1:
                raise DashboardPackageError(
                    "Das Archiv muss genau eine SAX Power Integration enthalten."
                )
            package_prefix = manifests[0].parent
            if package_prefix.parts != ("sax_power",) and (
                package_prefix.parts[-2:] != ("custom_components", "sax_power")
            ):
                raise DashboardPackageError("Unbekanntes Installationslayout.")
            installed: set[Path] = set()
            for item, path in zip(files, paths, strict=True):
                if not path.is_relative_to(package_prefix):
                    continue
                relative = Path(*path.relative_to(package_prefix).parts)
                if relative in installed:
                    raise DashboardPackageError("Doppelter Dateipfad im Paket.")
                installed.add(relative)
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(package.read(item))
    except (OSError, BadZipFile) as err:
        raise DashboardPackageError(
            f"ZIP kann nicht installiert werden: {err}"
        ) from err

    try:
        manifest = json.loads((destination / "manifest.json").read_text())
        if manifest.get("domain") != "sax_power" or not isinstance(
            manifest.get("version"), str
        ):
            raise DashboardPackageError("Ungültiges SAX Power Manifest.")
        asset = (destination / "frontend" / "sax-power-vue.js").read_bytes()
        license_text = (destination / "frontend" / "LICENSES.txt").read_text()
        if not asset or "@vue/" not in license_text:
            raise DashboardPackageError("Vue-Bundle oder Lizenz fehlt im Paket.")
        for language in ("de", "en"):
            translations = json.loads(
                (destination / "translations" / f"{language}.json").read_text()
            )
            if "vue_dashboard_update" not in translations.get("issues", {}):
                raise DashboardPackageError("Übersetzung der Vue-Reparatur fehlt.")
    except (OSError, json.JSONDecodeError, AttributeError) as err:
        raise DashboardPackageError(f"Installationsdateien fehlen: {err}") from err
    return manifest["version"], hashlib.sha256(asset).hexdigest(), len(installed)


def verify_dashboard_package(archive: Path) -> DashboardPackageReport:
    """Verify a clean installation in a process that cannot import this checkout."""
    archive = archive.resolve()
    with tempfile.TemporaryDirectory(prefix="sax-dashboard-install-") as directory:
        isolated_root = Path(directory)
        package_root = isolated_root / "custom_components" / "sax_power"
        version, asset_sha256, installed_files = _install_archive(archive, package_root)
        worker = isolated_root / "test_installed_dashboard.py"
        shutil.copyfile(Path(__file__).with_name("dashboard_package_smoke.py"), worker)
        environment = {
            **os.environ,
            "PYTEST_ADDOPTS": "",
            "PYTEST_PLUGINS": "",
            "SAX_DASHBOARD_PACKAGE_SHA256": asset_sha256,
        }
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-m",
                "pytest",
                str(worker),
                "--confcutdir",
                str(isolated_root),
                "-o",
                "asyncio_mode=auto",
                "-o",
                "asyncio_default_fixture_loop_scope=function",
                "--timeout=45",
                "-q",
            ],
            cwd=isolated_root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            raise DashboardPackageError(
                f"Isolierter HA-Pakettest fehlgeschlagen:\n{output}"
            )
        return DashboardPackageReport(
            version=version,
            archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
            asset_sha256=asset_sha256,
            installed_files=installed_files,
            test_output=output,
        )


def main(argv: Sequence[str] | None = None) -> int:
    """Smoke-test one downloaded GitHub source or snapshot installation package."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    arguments = parser.parse_args(argv)
    try:
        report = verify_dashboard_package(arguments.archive)
    except (DashboardPackageError, subprocess.TimeoutExpired) as err:
        print(str(err), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "version": report.version,
                "archive_sha256": report.archive_sha256,
                "asset_sha256": report.asset_sha256,
                "installed_files": report.installed_files,
                "isolated_home_assistant": "passed",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
