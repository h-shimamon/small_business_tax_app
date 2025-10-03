from datetime import date, datetime

from app.utils import (
    date_compact,
    date_iso,
    date_kanji,
    format_currency,
    format_number,
    money,
    number,
)


def test_money_formats_positive_int():
    assert money(1234567) == '1,234,567円'


def test_money_handles_none_and_zero():
    assert money(None) == '0円'
    assert money(0) == '0円'


def test_money_accepts_strings_and_negative_values():
    assert money('1,500') == '1,500円'
    assert money(-2500) == '-2,500円'


def test_money_none_text_override():
    assert money(None, none_text='') == ''


def test_number_formats_values():
    assert number(9876543) == '9,876,543'
    assert number('1,200') == '1,200'
    assert number(None) == ''


def test_aliases_match_new_filters():
    assert format_currency(1000) == money(1000)
    assert format_number(2000) == number(2000)


def test_date_filters_accept_date_and_datetime():
    sample_date = date(2024, 3, 1)
    sample_datetime = datetime(2024, 3, 1, 12, 30)
    assert date_iso(sample_date) == '2024-03-01'
    assert date_iso(sample_datetime) == '2024-03-01'
    assert date_compact(sample_date) == '20240301'
    assert date_kanji(sample_date) == '2024年03月01日'


def test_date_filters_handle_strings_and_none():
    assert date_compact('2024-02-29') == '20240229'
    assert date_iso(None) == ''
    assert date_kanji('invalid') == ''
