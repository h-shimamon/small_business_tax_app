from __future__ import annotations

"""
Date-first readers for models, falling back to ISO String(10).

These helpers centralize the logic of obtaining a Python `date` without
changing existing behavior at call sites. They prefer the new parallel Date
columns (e.g., *_date), and fall back to parsing the legacy String(10) ISO
columns when needed. UI/behavior is unaffected; usage is opt-in from
internal services and generators.
"""

import datetime as _dt  # noqa: E402


def _to_date(value) -> _dt.date | None:
    if value is None or value == "":
        return None
    if isinstance(value, _dt.date):
        return value
    if isinstance(value, _dt.datetime):
        return value.date()
    try:
        return _dt.date.fromisoformat(str(value))
    except Exception:
        return None

def ensure_date(value) -> _dt.date | None:
    """Public alias for internal date normalization (String(10) -> date)."""
    return _to_date(value)

def to_iso(d: _dt.date | None) -> str | None:
    """Public helper to return ISO string from a date or None."""
    return d.isoformat() if isinstance(d, _dt.date) else None


# --- Company ---
def company_accounting_period_start(company) -> _dt.date | None:
    # Prefer Date column, fallback to String(10)
    return company.accounting_period_start_date or _to_date(company.accounting_period_start)


def company_accounting_period_end(company) -> _dt.date | None:
    return company.accounting_period_end_date or _to_date(company.accounting_period_end)


def company_closing_date(company) -> _dt.date | None:
    return company.closing_date_date or _to_date(company.closing_date)


# --- NotesReceivable ---
def notes_receivable_issue_date(nr) -> _dt.date | None:
    value = getattr(nr, 'issue_date', None)
    return _to_date(value)


def notes_receivable_due_date(nr) -> _dt.date | None:
    value = getattr(nr, 'due_date', None)
    return _to_date(value)


__all__ = [
    'company_accounting_period_start',
    'company_accounting_period_end',
    'company_closing_date',
    'notes_receivable_issue_date',
    'notes_receivable_due_date',
    'ensure_date',
    'to_iso',
]
