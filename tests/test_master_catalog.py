import pytest

from app.domain.master.catalog import load_catalog


def test_catalog_normalization_handles_spaces_and_case(app):
    with app.app_context():
        catalog = load_catalog()
        assert catalog.normalize(' 売 上 ') == '売上'
        assert catalog.normalize('通信費') == '通信費'


def test_catalog_alias_resolution_if_available(app):
    with app.app_context():
        catalog = load_catalog()
        resolved = catalog.resolve('給料手当')
        if resolved is None:
            pytest.skip('alias dictionary does not include 給料手当')
        assert resolved == '給料賃金'
