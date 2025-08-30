from __future__ import annotations

"""
Wareki primitives: unified, additive implementation for Japanese era conversions.

Accepts date|str|None and normalizes via ensure_date() so callers can
pass whichever they currently have without changing UI/outputs.
"""

from datetime import date, datetime
from typing import Optional, Tuple, Any

from app.models_utils.date_readers import ensure_date


_ERAS = [
    ("令和", (2019, 5, 1)),
    ("平成", (1989, 1, 8)),
    ("昭和", (1926, 12, 25)),
]


def _to_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value
    # strings or other types: rely on shared normalization
    return ensure_date(value)


def to_wareki(value: Any) -> str:
    d = _to_date(value)
    if d is None:
        return ""
    y, m, dd = d.year, d.month, d.day
    era_name_val = None
    era_year = None
    for name, (ey, em, ed) in _ERAS:
        if (y, m, dd) >= (ey, em, ed):
            era_name_val = name
            era_year = y - ey + 1
            break
    if era_name_val is None or era_year is None:
        return ""
    return f"{era_name_val}{era_year}年{m}月{dd}日"


def with_spaces(value: Any) -> str:
    s = to_wareki(value)
    if not s:
        return ""
    ideographic_space = "\u3000"  # full-width space
    s = s.replace("年", ideographic_space).replace("月", ideographic_space).replace("日", "")
    return s.strip()


def era_name(value: Any) -> str:
    d = _to_date(value)
    if d is None:
        return ""
    y, m, dd = d.year, d.month, d.day
    for name, (ey, em, ed) in _ERAS:
        if (y, m, dd) >= (ey, em, ed):
            return name
    return ""


def numeric_parts(value: Any) -> Optional[Tuple[str, str, str]]:
    d = _to_date(value)
    if d is None:
        return None
    y, m, dd = d.year, d.month, d.day
    era_start = None
    for _, (ey, em, ed) in _ERAS:
        if (y, m, dd) >= (ey, em, ed):
            era_start = (ey, em, ed)
            break
    if era_start is None:
        return None
    wy = y - era_start[0] + 1
    return (f"{wy:02d}", f"{m:02d}", f"{dd:02d}")


def render(value: Any, style: str = "era_ymd") -> str:
    """Render Japanese era date in common styles.

    Styles:
      - "era_ymd": e.g., "令和7年5月1日" (default)
      - "era_with_spaces": e.g., "令和7　05　01" (full-width spaces, no 年/月/日)
      - "yy_mm_dd": e.g., "07 05 01" (wareki numeric parts, no era)
      - "era_year": e.g., "令和7" (era name + era year only)
      - "era_name": e.g., "令和" (era name only)
    Returns empty string when value cannot be rendered.
    """
    d = _to_date(value)
    if d is None:
        return ""
    if style == "era_ymd":
        return to_wareki(d)
    if style == "era_with_spaces":
        return with_spaces(d)
    if style == "yy_mm_dd":
        parts = numeric_parts(d)
        return " ".join(parts) if parts else ""
    if style == "era_year":
        y, m, dd = d.year, d.month, d.day
        for name, (ey, em, ed) in _ERAS:
            if (y, m, dd) >= (ey, em, ed):
                wy = y - ey + 1
                return f"{name}{wy}"
        return ""
    if style == "era_name":
        return era_name(d)
    raise ValueError(f"unknown wareki render style: {style}")


__all__ = [
    "to_wareki",
    "with_spaces",
    "era_name",
    "numeric_parts",
    "render",
]
