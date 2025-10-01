import pytest

from app.pdf.geom_loader import GeometrySchemaError, validate_and_apply_defaults


def test_cols_missing_w_raises():
    data = {
        "cols": {
            "balance": {"x": 100.0}  # 'w' missing
        }
    }
    with pytest.raises(GeometrySchemaError):
        validate_and_apply_defaults(data)


def test_rects_wrong_length_raises():
    data = {
        "rects": {
            "RECT_A": [10.0, 20.0, 30.0]  # only 3 items
        }
    }
    with pytest.raises(GeometrySchemaError):
        validate_and_apply_defaults(data)


def test_non_number_in_rects_raises():
    data = {
        "rects": {
            "RECT_A": [10.0, 20.0, "w", 40.0]
        }
    }
    with pytest.raises(GeometrySchemaError):
        validate_and_apply_defaults(data)


def test_defaults_applied_for_optional_fields():
    data = {
        "cols": {
            "account": {"x": 10.0, "w": 50.0}
        }
        # no row, no margins provided
    }
    out = validate_and_apply_defaults(data)
    assert out.get("schema_version") == "1.0"
    assert isinstance(out.get("row"), dict)
    assert out["row"].get("DETAIL_ROWS") == 20
    assert isinstance(out.get("margins"), dict)
    assert out["margins"].get("right_margin") == 0.0
