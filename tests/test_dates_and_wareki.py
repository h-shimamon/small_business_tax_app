from datetime import date

import pytest

from app.primitives.dates import parse_lenient, parse_strict
from app.primitives.wareki import render


def test_parse_lenient_accepts_iso_and_empty():
    assert parse_lenient("2024-05-01").isoformat() == "2024-05-01"
    assert parse_lenient("") is None


def test_parse_strict_accepts_only_iso():
    assert parse_strict("2024-05-01").isoformat() == "2024-05-01"
    with pytest.raises(ValueError):
        parse_strict("")
    with pytest.raises(ValueError):
        parse_strict("2024/05/01")


def test_wareki_render_styles():
    d = date(2024, 5, 1)
    assert render(d, "era_ymd").startswith("令和")
    assert render(d, "yy_mm_dd") == "06 05 01"  # 令和6年
    assert render(d, "era_year").startswith("令和")
    assert render(d, "era_name") == "令和"
    with pytest.raises(ValueError):
        render(d, "unknown_style")
