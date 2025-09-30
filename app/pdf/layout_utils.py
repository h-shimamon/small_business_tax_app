from __future__ import annotations

import json
import os
from typing import Any, Dict, List, NamedTuple, Optional

from .fonts import default_font_map, ensure_font_registered


class GeometryError(Exception):
    pass


class PdfAssets(NamedTuple):
    repo_root: str
    base_pdf: str
    font_map: Dict[str, str]
    geometry: Dict[str, Any]


def prepare_pdf_assets(
    form_subdir: str,
    geometry_key: str,
    year: str,
    *,
    repo_root: Optional[str] = None,
    ensure_font_name: Optional[str] = "NotoSansJP",
    required: bool = True,
    validate: bool = True,
) -> PdfAssets:
    resolved_root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    base_pdf = os.path.join(resolved_root, f"resources/pdf_forms/{form_subdir}/{year}/source.pdf")
    font_map = default_font_map(resolved_root)
    if ensure_font_name:
        try:
            ensure_font_registered(ensure_font_name, font_map[ensure_font_name])
        except Exception:
            pass
    geometry = load_geometry(geometry_key, year, repo_root=resolved_root, required=required, validate=validate)
    return PdfAssets(repo_root=resolved_root, base_pdf=base_pdf, font_map=font_map, geometry=geometry)


def _require_keys(obj: Dict[str, Any], path: List[str]) -> None:
    cur: Any = obj
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            raise GeometryError(f"geometry missing required key: {'/'.join(path)}")
        cur = cur[p]


def load_geometry(template_key: str, year: str, *, repo_root: str, required: bool = True, validate: bool = True) -> Dict[str, Any]:
    """
    Load geometry JSON for a given PDF template key and year.

    Fallback strategy (dev convenience):
    - If the exact year file is missing and we are NOT running under pytest,
      try the latest available year or a default file.
    - When running tests (pytest) and required=True, we strictly raise.
    """
    base_dir = os.path.join(repo_root, f"resources/pdf_templates/{template_key}")
    geom_path = os.path.join(base_dir, f"{year}_geometry.json")

    used_path = None
    if os.path.exists(geom_path):
        used_path = geom_path
    else:
        # Missing: decide whether to fallback or raise strictly
        under_pytest = bool(os.environ.get('PYTEST_CURRENT_TEST'))
        if required and under_pytest:
            # Strict behavior for tests: raise
            raise FileNotFoundError(f"Geometry file not found: {geom_path}")
        # Dev fallback: search latest year or default
        try:
            candidates = []
            if os.path.isdir(base_dir):
                for fn in os.listdir(base_dir):
                    if fn.endswith("_geometry.json") and fn[0:4].isdigit():
                        try:
                            y = int(fn[0:4])
                            candidates.append((y, os.path.join(base_dir, fn)))
                        except Exception:
                            continue
            if candidates:
                candidates.sort(key=lambda t: t[0], reverse=True)
                used_path = candidates[0][1]
        except Exception:
            used_path = None

        if used_path is None:
            default_path = os.path.join(base_dir, "default_geometry.json")
            if os.path.exists(default_path):
                used_path = default_path

        if used_path is None and required:
            raise FileNotFoundError(f"Geometry file not found: {geom_path}")
        if used_path is None:
            return {}

    try:
        with open(used_path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f) or {}
    except Exception as e:
        if required:
            raise GeometryError(f"Failed to parse geometry JSON: {used_path}") from e
        return {}

    if validate:
        # Try strict schema validation + defaults (non-fatal; falls back to legacy checks on error)
        try:
            from . import geom_loader as _geom  # local import to avoid cycles
            data = _geom.validate_and_apply_defaults(data)
        except Exception:
            # Keep legacy behavior if strict validation fails
            pass

        # Legacy minimal validation (preserved for backward compatibility)
        _require_keys(data, ["cols"])  # this loader is for cols-based templates
        cols = data.get("cols", {})
        if not isinstance(cols, dict) or not cols:
            raise GeometryError("geometry cols must be a non-empty object")
        for name, spec in cols.items():
            if not isinstance(spec, dict) or "x" not in spec:
                raise GeometryError(f"geometry column '{name}' missing x")
        if "margins" in data and not isinstance(data["margins"], dict):
            raise GeometryError("geometry 'margins' must be an object when present")

    return data


def center_from_row1(row1_center: float, row_step: float, row_idx: int) -> float:
    return float(row1_center) - float(row_step) * int(row_idx)


def baseline0_from_center(first_center: float, base_font_size: float) -> float:
    return float(first_center) - float(base_font_size) / 2.0


def center_from_baseline(baseline0: float, eff_step: float, row_idx: int, base_font_size: float) -> float:
    baseline_n = float(baseline0) - float(eff_step) * int(row_idx)
    return baseline_n + float(base_font_size) / 2.0


def append_left(texts, *, page: int, x: float, w: float, center_y: float, text: str, font_name: str, font_size: float) -> None:
    if not text:
        return
    y = float(center_y) - float(font_size) / 2.0
    from .pdf_fill import TextSpec  # local import to avoid cycles
    texts.append(TextSpec(page=page, x=float(x), y=y, text=str(text), font_name=font_name, font_size=float(font_size)))


def append_right(texts, *, page: int, x: float, w: float, center_y: float, text: str, font_name: str, font_size: float, right_margin: float = 0.0) -> None:
    if not text:
        return
    y = float(center_y) - float(font_size) / 2.0
    from .pdf_fill import TextSpec  # local import to avoid cycles
    texts.append(
        TextSpec(page=page, x=(float(x) + float(w) - float(right_margin)), y=y, text=str(text), font_name=font_name, font_size=float(font_size), align="right")
    )

