from __future__ import annotations

"""
Dates primitives: thin, additive facade over date readers.

Intent:
- Provide a single, expressive entrypoint for callers (e.g., "period")
- Keep UI/external I/F unchanged; usage is optional and non-breaking
"""

from datetime import date
from typing import NamedTuple, Optional, Any

from app.models_utils import date_readers as _readers


class Period(NamedTuple):
    start: Optional[date]
    end: Optional[date]


def get_company_period(company: Any) -> Period:
    """Return (start, end) dates for a company using centralized readers.

    - Prefers Date columns, falls back to String(10) parse
    - Returns None for missing/invalid
    """
    return Period(
        start=_readers.company_accounting_period_start(company),
        end=_readers.company_accounting_period_end(company),
    )


def company_closing_date(company: Any) -> Optional[date]:
    """Date for company closing date with safe fallback to String(10)."""
    return _readers.company_closing_date(company)


def to_iso(d: Optional[date]) -> Optional[str]:
    """ISO string for a date or None."""
    return d.isoformat() if isinstance(d, date) else None


__all__ = [
    "Period",
    "get_company_period",
    "company_closing_date",
    "to_iso",
]

