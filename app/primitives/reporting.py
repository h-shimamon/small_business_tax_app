from __future__ import annotations

"""
Reporting primitives for Date/String(10) health metrics.

This mirrors the CLI calculations so tests/CI can reuse the logic.
Additive-only; existing CLI continues to work independently.
"""

from datetime import date  # noqa: E402
from typing import Any  # noqa: E402


def _safe_parse_iso(text: str | None) -> date | None:
    if not text:
        return None
    try:
        if len(text) != 10 or text[4] != '-' or text[7] != '-':
            return None
        y, m, d = int(text[0:4]), int(text[5:7]), int(text[8:10])
        return date(y, m, d)
    except Exception:
        return None


def pair_metrics(rows: list[dict[str, Any]], str_key: str, date_key: str) -> dict[str, int]:
    total = len(rows)
    str_vals = [r.get(str_key) for r in rows]
    date_vals = [r.get(date_key) for r in rows]

    def _is_empty_str(v: Any) -> bool:
        try:
            return (v is None) or (str(v).strip() == "")
        except Exception:
            return True

    str_null = sum(1 for v in str_vals if _is_empty_str(v))
    date_null = sum(1 for v in date_vals if v is None)
    both_set = sum(1 for s, d in zip(str_vals, date_vals) if not _is_empty_str(s) and d is not None)
    str_only = sum(1 for s, d in zip(str_vals, date_vals) if not _is_empty_str(s) and d is None)
    date_only = sum(1 for s, d in zip(str_vals, date_vals) if _is_empty_str(s) and d is not None)
    mismatch = 0
    for s, d in zip(str_vals, date_vals):
        if _is_empty_str(s) or d is None:
            continue
        ps = _safe_parse_iso(s)
        if ps != d:
            mismatch += 1
    return {
        'total': total,
        'str_null': str_null,
        'date_null': date_null,
        'both_set': both_set,
        'str_only': str_only,
        'date_only': date_only,
        'mismatch': mismatch,
    }


__all__ = ["pair_metrics"]

