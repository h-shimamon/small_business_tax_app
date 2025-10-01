#!/usr/bin/env python3
"""
check_ui_options.py

Purpose: Detect direct option arrays or legacy constants in templates to enforce SSOT via ui_options.
Usage:
  python scripts/check_ui_options.py [--base DIR]
Behavior:
  - Scans template files for patterns indicating hard-coded options
  - Ignores lines containing 'CI-ALLOW'
  - Exits with non-zero if any suspicious occurrences are found
Patterns:
  1) options=[ ... ] (hard-coded arrays)
  2) {% set NAME = [ ... ] %} (template-level arrays)
  3) OPTIONS_ tokens (legacy constants)

This script uses only stdlib to run in CI without extra deps.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("hard_array", re.compile(r"options\s*=\s*\[", re.IGNORECASE)),
    ("tmpl_set_array", re.compile(r"\{\%\s*set\s+[^=]+=\s*\[", re.IGNORECASE)),
    ("legacy_token", re.compile(r"OPTIONS_", re.IGNORECASE)),
]

EXCLUDE_DIRS = {".git", "venv", "node_modules", "__pycache__", ".pytest_cache", "migrations"}
TARGET_DIRS = ["app/templates"]


def iter_files(base: str):
    for tdir in TARGET_DIRS:
        root = os.path.join(base, tdir)
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fn in filenames:
                if not (fn.endswith(".html") or fn.endswith(".jinja") or fn.endswith(".j2")):
                    continue
                yield os.path.join(dirpath, fn)


def check_file(path: str) -> list[tuple[str, int, str]]:
    hits: list[tuple[str, int, str]] = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for lineno, line in enumerate(f, 1):
                if "CI-ALLOW" in line:
                    continue
                for name, rx in PATTERNS:
                    if rx.search(line):
                        hits.append((name, lineno, line.rstrip()))
    except Exception as e:
        print(f"WARN: cannot read {path}: {e}", file=sys.stderr)
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.getcwd())
    args = ap.parse_args()

    total = 0
    for fp in iter_files(args.base):
        hits = check_file(fp)
        for name, ln, snippet in hits:
            print(f"{fp}:{ln}: {name}: {snippet}")
            total += 1
    if total:
        print(f"ERROR: Found {total} possible direct option occurrences. Use ui_options.* instead.", file=sys.stderr)
        return 2
    print("OK: no direct option occurrences found.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
