"""
Geometry loader and validator for PDF templates.
- Validates either "cols"-style or "rects"-style geometry JSONs
- Applies safe defaults for backward compatibility
- Provides CLI: python -m app.pdf.geom_loader --check-all

This module does not change UI or DB. It is self-contained and optional to adopt
from existing call sites. It can be wired via layout_utils later.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Iterable
from typing import Any


class GeometrySchemaError(Exception):
    pass


Number = (int, float)


def _is_number(x: Any) -> bool:
    return isinstance(x, Number) and not isinstance(x, bool)


def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        raise GeometrySchemaError(f"directory does not exist: {d}")


def _apply_defaults(data: dict[str, Any]) -> dict[str, Any]:
    # schema_version default
    data.setdefault("schema_version", "1.0")

    # row defaults (non-invasive)
    row = data.get("row")
    if not isinstance(row, dict):
        row = {}
        data["row"] = row
    # Only set DETAIL_ROWS if absent; do not override explicit values
    if "DETAIL_ROWS" not in row:
        row["DETAIL_ROWS"] = 20

    # margins defaults
    margins = data.get("margins")
    if not isinstance(margins, dict):
        margins = {}
        data["margins"] = margins
    if "right_margin" not in margins:
        margins["right_margin"] = 0.0

    return data


def _validate_cols(cols: Any) -> None:
    if not isinstance(cols, dict) or not cols:
        raise GeometrySchemaError("'cols' must be a non-empty object")
    for name, spec in cols.items():
        if not isinstance(name, str) or not name:
            raise GeometrySchemaError("column name must be a non-empty string")
        if not isinstance(spec, dict):
            raise GeometrySchemaError(f"cols['{name}'] must be an object")
        if not _is_number(spec.get("x")):
            raise GeometrySchemaError(f"cols['{name}'].x must be a number")
        if not _is_number(spec.get("w")):
            raise GeometrySchemaError(f"cols['{name}'].w must be a number")


def _validate_rects(rects: Any) -> None:
    if not isinstance(rects, dict) or not rects:
        raise GeometrySchemaError("'rects' must be a non-empty object")
    for name, arr in rects.items():
        if not isinstance(name, str) or not name:
            raise GeometrySchemaError("rect key must be a non-empty string")
        if not isinstance(arr, list) or len(arr) != 4:
            raise GeometrySchemaError(f"rects['{name}'] must be an array of 4 numbers [x0,y0,w,h]")
        for i, v in enumerate(arr):
            if not _is_number(v):
                raise GeometrySchemaError(f"rects['{name}'][{i}] must be a number")


def validate_and_apply_defaults(data: dict[str, Any]) -> dict[str, Any]:
    """Validate the geometry dict and apply safe defaults.

    Accepts either:
      - cols-mode: { cols: { <name>: {x,w}, ... }, row?, margins? }
      - rects-mode: { rects: { <name>: [x0,y0,w,h], ... }, row? }
    Returns the (possibly defaulted) dict on success. Raises GeometrySchemaError on failure.
    """
    if not isinstance(data, dict):
        raise GeometrySchemaError("geometry JSON root must be an object")

    has_cols = "cols" in data
    has_rects = "rects" in data
    if not (has_cols or has_rects):
        raise GeometrySchemaError("either 'cols' or 'rects' must be present")
    if has_cols:
        _validate_cols(data.get("cols"))
    if has_rects:
        _validate_rects(data.get("rects"))

    return _apply_defaults(dict(data))


def load(template_key: str, year: str, *, repo_root: str, required: bool = True, validate: bool = True) -> dict[str, Any]:
    """Load a geometry JSON, optionally validate and apply defaults.

    - template_key: e.g. 'uchiwakesyo_uketoritegata' or 'beppyou_02'
    - year: e.g. '2025'
    - repo_root: absolute repository root path
    - required: if True, raise on missing or parse error
    - validate: if True, run schema checks and defaults
    """
    path = os.path.join(repo_root, f"resources/pdf_templates/{template_key}/{year}_geometry.json")
    if not os.path.exists(path):
        if required:
            raise FileNotFoundError(f"geometry not found: {path}")
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception as e:
        if required:
            raise GeometrySchemaError(f"failed to parse geometry JSON: {path}") from e
        return {}

    if validate:
        data = validate_and_apply_defaults(data)
    return data


def _repo_root_from_here() -> str:
    # app/pdf/geom_loader.py -> app/pdf -> app -> repo_root
    here = os.path.abspath(os.path.dirname(__file__))
    repo_root = os.path.abspath(os.path.join(here, "..", ".."))
    return repo_root


def _iter_geometry_files(repo_root: str) -> Iterable[tuple[str, str, str]]:
    base = os.path.join(repo_root, "resources", "pdf_templates")
    if not os.path.isdir(base):
        return []
    for tkey in sorted(os.listdir(base)):
        tdir = os.path.join(base, tkey)
        if not os.path.isdir(tdir):
            continue
        for fname in sorted(os.listdir(tdir)):
            if fname.endswith("_geometry.json"):
                # expected format: <year>_geometry.json
                year = fname.split("_", 1)[0]
                yield (tkey, year, os.path.join(tdir, fname))


def cli_check_all(repo_root: str, report_path: str | None = None) -> int:
    """Validate all geometry files. Returns process exit code (0 ok, 1 failure)."""
    errors: list[dict[str, str]] = []
    count = 0
    for tkey, year, path in _iter_geometry_files(repo_root):
        count += 1
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f) or {}
            validate_and_apply_defaults(raw)
        except Exception as e:
            rel = os.path.relpath(path, repo_root)
            errors.append({"path": rel, "error": str(e)})
    status = 0
    if errors:
        print("Geometry validation FAILED:", file=sys.stderr)
        for item in errors:
            print(f" - {item['path']}: {item['error']}", file=sys.stderr)
        status = 1
    else:
        print(f"Geometry validation OK ({count} file(s))")
    if report_path:
        _write_json_report(report_path, count=count, errors=errors, status=status)
    return status


def _write_json_report(report_path: str, *, count: int, errors: list[dict[str, str]], status: int) -> None:
    payload = {
        "status": "failed" if status else "ok",
        "files_checked": count,
        "errors": errors,
    }
    try:
        _ensure_dir(report_path)
        with open(report_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"Failed to write JSON report {report_path}: {exc}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PDF geometry templates")
    parser.add_argument("--check-all", action="store_true", help="validate all *_geometry.json under resources/pdf_templates")
    parser.add_argument("--repo-root", default=_repo_root_from_here(), help="repository root (auto-detected)")
    parser.add_argument("--json-report", help="write validation result to JSON file")
    args = parser.parse_args(argv)

    if args.check_all:
        return cli_check_all(args.repo_root, report_path=args.json_report)

    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
