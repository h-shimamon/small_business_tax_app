from __future__ import annotations

from typing import Optional, Tuple


_ERAS = [
    ("令和", (2019, 5, 1)),
    ("平成", (1989, 1, 8)),
    ("昭和", (1926, 12, 25)),
]


def to_wareki(date_str: Optional[str]) -> str:
    """Convert 'YYYY-MM-DD' (or 'YYYY/MM/DD') to Japanese era like '令和X年M月D日'.
    Returns '' if invalid or out of supported eras.
    """
    if not date_str:
        return ""
    from datetime import datetime
    try:
        ds = date_str.strip()
        fmt = "%Y-%m-%d" if "-" in ds else "%Y/%m/%d"
        dt = datetime.strptime(ds, fmt)
    except Exception:
        return ""
    y, m, d = dt.year, dt.month, dt.day
    era_name = None
    era_year = None
    for name, (ey, em, ed) in _ERAS:
        if (y, m, d) >= (ey, em, ed):
            era_name = name
            era_year = y - ey + 1
            break
    if era_name is None or era_year is None:
        return ""
    return f"{era_name}{era_year}年{m}月{d}日"


def wareki_with_spaces(date_str: Optional[str]) -> str:
    s = to_wareki(date_str)
    if not s:
        return ""
    ideographic_space = "\u3000"  # full-width space
    s = s.replace("年", ideographic_space).replace("月", ideographic_space).replace("日", "")
    return s.strip()


def wareki_era_name(date_str: Optional[str]) -> str:
    """Return era name (e.g., '令和', '平成', '昭和') for the given date string.
    Returns '' if invalid or before supported eras.
    """
    if not date_str:
        return ""
    from datetime import datetime
    try:
        ds = date_str.strip()
        fmt = "%Y-%m-%d" if "-" in ds else "%Y/%m/%d"
        dt = datetime.strptime(ds, fmt)
    except Exception:
        return ""
    y, m, d = dt.year, dt.month, dt.day
    for name, (ey, em, ed) in _ERAS:
        if (y, m, d) >= (ey, em, ed):
            return name
    return ""


def wareki_numeric_parts(date_str: Optional[str]) -> Optional[Tuple[str, str, str]]:
    """Return (yy, mm, dd) as zero-padded 2-digit strings for the given date in wareki.
    Returns None if input invalid.
    """
    if not date_str:
        return None
    from datetime import datetime
    try:
        ds = date_str.strip()
        fmt = "%Y-%m-%d" if "-" in ds else "%Y/%m/%d"
        dt = datetime.strptime(ds, fmt)
    except Exception:
        return None
    y, m, d = dt.year, dt.month, dt.day
    era_start = None
    for _, (ey, em, ed) in _ERAS:
        if (y, m, d) >= (ey, em, ed):
            era_start = (ey, em, ed)
            break
    if era_start is None:
        return None
    wy = y - era_start[0] + 1
    return (f"{wy:02d}", f"{m:02d}", f"{d:02d}")

