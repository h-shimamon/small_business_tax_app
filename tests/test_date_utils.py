from datetime import date, datetime
from types import SimpleNamespace

from app.models_utils.date_readers import (
    DateValue,
    company_accounting_period_end,
    company_accounting_period_start,
    company_closing_date,
    ensure_date,
    normalize_date,
    to_iso,
)


def test_normalize_date_handles_various_inputs():
    assert normalize_date('2024-01-02') == date(2024, 1, 2)
    assert normalize_date(datetime(2024, 1, 2, 10, 30)) == date(2024, 1, 2)
    assert normalize_date(None) is None
    assert normalize_date('') is None


def test_date_value_encapsulates_raw_and_iso():
    value = DateValue.from_value('2024-04-01')
    assert value.date == date(2024, 4, 1)
    assert value.iso == '2024-04-01'
    assert bool(value)

    empty = DateValue.from_value('')
    assert empty.date is None
    assert empty.iso is None
    assert not empty


def test_company_accessors_prefer_date_columns():
    company = SimpleNamespace(
        accounting_period_start_date=date(2023, 4, 1),
        accounting_period_start='2023-03-01',
        accounting_period_end_date=None,
        accounting_period_end='2024-03-31',
        closing_date_date=None,
        closing_date='2024-05-10',
    )

    assert company_accounting_period_start(company) == date(2023, 4, 1)
    assert company_accounting_period_end(company) == date(2024, 3, 31)
    assert company_closing_date(company) == date(2024, 5, 10)


def test_to_iso_accepts_date_and_value_object():
    d = date(2024, 6, 1)
    dv = DateValue.from_value(d)

    assert to_iso(d) == '2024-06-01'
    assert to_iso(dv) == '2024-06-01'
    assert to_iso(None) is None


def test_ensure_date_aliases_normalize_date():
    assert ensure_date('2024-07-01') == normalize_date('2024-07-01')
