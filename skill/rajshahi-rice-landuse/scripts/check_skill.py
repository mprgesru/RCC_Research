#!/usr/bin/env python3
"""Structural checks for the rajshahi-rice-landuse skill.

Runs without the catalog validator. Checks file presence, SKILL.md frontmatter,
role folders and relative Markdown links.

Usage:
    python check_skill.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

SKILL_DIR = Path(__file__).resolve().parents[1]
REQUIRED = ("SKILL.md", "README.md", "INDEX.md", "PROVENANCE.md", "AGENTS.md")
ROLES = (
    "research-coordinator",
    "literature-dataset-auditor",
    "geospatial-data-steward",
    "rice-phenology-mapper",
    "accuracy-change-analyst",
    "research-report-writer",
)
FAILURES: list[str] = []


def fail(message: str) -> None:
    FAILURES.append(message)
    print(f"FAIL: {message}")


def ok(message: str) -> None:
    print(f"PASS: {message}")


def check_required() -> None:
    for name in REQUIRED:
        path = SKILL_DIR / name
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"missing or empty: {name}")
        else:
            ok(f"present: {name}")


def check_frontmatter() -> None:
    text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"(?ms)^---\s*$\n(.*?)\n^---\s*$", text)
    if not match:
        fail("SKILL.md has no leading YAML frontmatter")
        return
    body = match.group(1)
    fields = {}
    meta = {}
    in_metadata = False
    for line in body.splitlines():
        if not line.strip():
            continue
        top = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        nested = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(.*)$", line)
        if top and not line.startswith((" ", "\t")):
            key, value = top.groups()
            fields[key] = value.strip()
            in_metadata = key == "metadata"
        elif in_metadata and nested:
            key, value = nested.groups()
            meta[key] = value.strip()
    if fields.get("name") != SKILL_DIR.name:
        fail(f"frontmatter name must be {SKILL_DIR.name!r}, got {fields.get('name')!r}")
    else:
        ok("frontmatter name matches directory")
    missing_fields = [
        key
        for key in ("description", "version", "author")
        if not (fields.get(key) or meta.get(key) or meta.get(f"skill-{key}"))
    ]
    if missing_fields:
        for key in missing_fields:
            fail(f"frontmatter missing {key}")
    else:
        ok("frontmatter has description, version and author")


def check_roles() -> None:
    missing = [
        role
        for role in ROLES
        if not (SKILL_DIR / "roles" / role / "README.md").is_file()
        or (SKILL_DIR / "roles" / role / "README.md").stat().st_size == 0
    ]
    if missing:
        for role in missing:
            fail(f"missing role README: roles/{role}/README.md")
    else:
        ok(f"all {len(ROLES)} role folders have a README")


def check_links() -> None:
    pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    missing = []
    for markdown in sorted(SKILL_DIR.rglob("*.md")):
        text = re.sub(r"(?ms)^```.*?^```", "", markdown.read_text(encoding="utf-8"))
        for raw in pattern.findall(text):
            target = raw.strip()
            if not target or target.startswith(("#", "//")):
                continue
            if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
                continue
            path = unquote(urlsplit(target).path)
            if not path:
                continue
            resolved = (markdown.parent / path).resolve()
            if not resolved.exists():
                missing.append(f"{markdown.relative_to(SKILL_DIR)} -> {target}")
    if missing:
        for item in missing:
            fail(f"broken relative link: {item}")
    else:
        ok("all relative Markdown links resolve")


def main() -> int:
    print(f"Checking {SKILL_DIR}")
    check_required()
    check_frontmatter()
    check_roles()
    check_links()
    print()
    if FAILURES:
        print(f"RESULT: FAIL ({len(FAILURES)} problems)")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
