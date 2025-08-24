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


__all__ = [
    "to_wareki",
    "with_spaces",
    "era_name",
    "numeric_parts",
]
