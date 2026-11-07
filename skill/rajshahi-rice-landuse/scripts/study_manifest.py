#!/usr/bin/env python3
"""Consolidate the study manifest (protocol Step 1 and Step 8).

Collects every committed and runtime manifest, records the code revision, the
environment, and SHA-256 checksums for published tables, so the study can be
reconstructed from a single record.

Output
------
manifests/study_manifest.json
environment/pip-freeze.txt

Usage
-----
    python study_manifest.py
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_DIR = REPO_ROOT / "manifests"
TABLE_DIR = REPO_ROOT / "tables"
ENV_DIR = REPO_ROOT / "environment"
RUNTIME = Path(
    os.environ.get("RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice")
).expanduser()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(REPO_ROOT), *args], text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def load_jsons(directory: Path) -> dict:
    records = {}
    if not directory.exists():
        return records
    for path in sorted(directory.glob("*.json")):
        try:
            records[path.name] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            records[path.name] = {"error": str(exc)}
    return records


def main() -> int:
    ENV_DIR.mkdir(parents=True, exist_ok=True)

    try:
        freeze = subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze"], text=True, stderr=subprocess.DEVNULL
        )
    except Exception:  # noqa: BLE001
        freeze = ""
    (ENV_DIR / "pip-freeze.txt").write_text(freeze, encoding="utf-8")

    published = []
    for path in sorted(TABLE_DIR.glob("*")):
        if path.is_file():
            published.append(
                {
                    "path": str(path.relative_to(REPO_ROOT)),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )

    runtime_manifests = load_jsons(RUNTIME / "manifests")
    committed_manifests = load_jsons(MANIFEST_DIR)

    manifest = {
        "artifact": "study_manifest",
        "generated_utc": utc_now(),
        "title": "Seasonal rice persistence and rice-to-urban conversion in Rajshahi, 1990-2025",
        "protocol": {
            "path": "Rajshahi_Rice_LandUse_Research_Protocol.md",
            "status": "planning draft",
        },
        "code": {
            "repository": git("config", "--get", "remote.origin.url"),
            "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "revision": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain")),
        },
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "pip_freeze": "environment/pip-freeze.txt",
        },
        "runtime_root": str(RUNTIME),
        "committed_manifests": sorted(committed_manifests.keys()),
        "runtime_manifests": sorted(runtime_manifests.keys()),
        "published_tables": published,
        "step_status": {
            "1_boundary_and_manifest": "complete",
            "2_observation_inventory": "complete",
            "3_reference_data": "sample frame complete; interpretation pending",
            "4_seasonal_rule_maps": "complete (provisional, uncalibrated)",
            "4_sar_features": "complete for 2015, 2020, 2025",
            "4_random_forest": "implemented; not reportable on pseudo-labels",
            "5_land_cover": "complete (provisional, unvalidated)",
            "6_validation": "estimator complete; blocked on labels",
            "6_benchmark": "script ready; external downloads blocked",
            "7_change": "computed (mapped only, not interpretable)",
            "8_reproducible_outputs": "complete",
        },
        "known_deviations": [
            "Season windows are provisional pending BRRI/DAE confirmation.",
            "Sentinel-2 has no 2015 coverage over the AOI; the 2015 comparison uses Sentinel-1 only.",
            "Rule thresholds are uncalibrated placeholders.",
            "Random forest trained on pseudo-labels is circular and not reportable.",
            "GCD-Rice, Zhao 2026 and Singha 2017 file hosts returned HTTP 403; manual download required.",
            "The RCC boundary is an operational health-microplanning layer, not a cadastral boundary, and its licence is unstated.",
        ],
    }

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    (MANIFEST_DIR / "study_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"manifest: {MANIFEST_DIR / 'study_manifest.json'}")
    print(f"published tables: {len(published)}")
    print(f"runtime manifests: {len(runtime_manifests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
