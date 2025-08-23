from __future__ import annotations

import json
import os
from typing import Any, Dict, List


class GeometryError(Exception):
    pass


def _require_keys(obj: Dict[str, Any], path: List[str]) -> None:
    cur: Any = obj
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            raise GeometryError(f"geometry missing required key: {'/'.join(path)}")
        cur = cur[p]


def load_geometry(template_key: str, year: str, *, repo_root: str, required: bool = True, validate: bool = True) -> Dict[str, Any]:
    """
    Load geometry JSON for a given PDF template key and year.

    - template_key: e.g., 'uchiwakesyo_yocyokin', 'uchiwakesyo_urikakekin'
    - year: e.g., '2025'
    - repo_root: absolute repository root path
    - required: if True, raise GeometryError/FileNotFoundError when missing
    - validate: if True, perform minimal key validation
    """
    geom_path = os.path.join(repo_root, f"resources/pdf_templates/{template_key}/{year}_geometry.json")
    if not os.path.exists(geom_path):
        if required:
            raise FileNotFoundError(f"Geometry file not found: {geom_path}")
        return {}
    try:
        with open(geom_path, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
    except Exception as e:
        if required:
            raise GeometryError(f"Failed to parse geometry JSON: {geom_path}") from e
        return {}

    if validate:
        _require_keys(data, ["row"])
        _require_keys(data, ["cols"])
        _require_keys(data, ["row", "ROW1_CENTER"])
        _require_keys(data, ["row", "DETAIL_ROWS"])
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

