from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from app.company.parser_factory import ParserFactory
from app.company.parsers.moneyforward_parser import MoneyForwardParser


def _dummy_file():
    return FileStorage(stream=BytesIO(b'id'), filename='dummy.csv')


def test_moneyforward_parser_supported():
    parser = ParserFactory.create_parser('moneyforward', _dummy_file())
    assert isinstance(parser, MoneyForwardParser)


@pytest.mark.parametrize('software_name', ['yayoi', 'freee', 'other'])
def test_unsupported_parsers_raise(software_name):
    with pytest.raises(ValueError) as exc:
        ParserFactory.create_parser(software_name, _dummy_file())
    assert '対応' in str(exc.value)
