from __future__ import annotations

"""
Date utilities: fixed contract for parsing and company periods.

- parse_lenient: UI input tolerant parser. Returns date|None (empty -> None).
- parse_strict: Storage/print strict parser. Accepts only YYYY-MM-DD, raises ValueError.
- get_company_period: Unified accessor for a company's accounting period (start/end).
- to_iso, company_closing_date: re-exported for convenience/compatibility.

This module keeps existing behavior by delegating to models_utils.date_readers.
"""

from dataclasses import dataclass  # noqa: E402
from datetime import date  # noqa: E402
from app.models_utils.date_readers import (  # noqa: E402
    DateValue,
    company_accounting_period_end,
    company_accounting_period_start,
    company_closing_date,  # re-export
    normalize_date,
    to_iso,  # re-export
)


@dataclass(frozen=True)
class Period:
    start: date | None
    end: date | None


def as_date_value(value) -> DateValue:
    """Value Object として日付情報を取得する簡易ヘルパ。"""
    return DateValue.from_value(value)


def parse_lenient(value) -> date | None:
    """Lenient parser for UI inputs. Returns None for empty/invalid."""
    return normalize_date(value)


def parse_strict(value) -> date:
    """Strict parser for storage/printing. Only accepts YYYY-MM-DD; raises ValueError otherwise."""
    if value is None or value == "":
        raise ValueError("date is required")
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except Exception as e:
        raise ValueError(f"invalid date format: {value}") from e


def get_company_period(company) -> Period:
    """Return company's accounting period as Period(start,end). Safe for missing values."""
    try:
        start = company_accounting_period_start(company)
        end = company_accounting_period_end(company)
        return Period(start=start, end=end)
    except Exception:
        return Period(start=None, end=None)


__all__ = [
    "DateValue",
    "Period",
    "as_date_value",
    "parse_lenient",
    "parse_strict",
    "get_company_period",
    "to_iso",
    "company_closing_date",
]
