from __future__ import annotations

import io
from datetime import date
from types import SimpleNamespace
from unittest import mock

import pandas as pd
import pytest

from app.company.services.upload_flow_service import (
    UploadFlowService,
    UploadResult,
    UploadValidationError,
    UploadFlowError,
)


class DummyFile:
    def __init__(self, filename: str, content: bytes = b"data", content_length: int | None = None):
        self.filename = filename
        data = content or b""
        self.stream = io.BytesIO(data)
        self._content = data
        self.content_length = content_length if content_length is not None else len(data)

    def read(self):
        return self.stream.read()

    def seek(self, *args, **kwargs):
        return self.stream.seek(*args, **kwargs)

    def tell(self):
        return self.stream.tell()


@pytest.fixture(autouse=True)
def stub_mark_step(monkeypatch):
    monkeypatch.setattr('app.company.services.upload_flow_service.mark_step_as_completed', lambda *args, **kwargs: None)



@pytest.fixture
def user_stub():
    return SimpleNamespace(
        id=1,
        company=SimpleNamespace(
            id=10,
            accounting_period_start=date(2024, 1, 1),
            accounting_period_end=date(2024, 12, 31),
            accounting_period_start_date=date(2024, 1, 1),
            accounting_period_end_date=date(2024, 12, 31),
        ),
    )


@pytest.fixture
def session_stub(tmp_path, monkeypatch):
    session = {}
    monkeypatch.setattr(
        'app.company.services.upload_flow_service.current_app',
        SimpleNamespace(instance_path=str(tmp_path), config={}),
    )
    return session


@pytest.fixture
def mapping_service_mock(monkeypatch):
    mapping_mock = mock.Mock()
    mapping_mock.apply_mappings_to_journals.side_effect = lambda df: df
    mapping_mock.get_unmatched_accounts.return_value = []
    mapping_cls_mock = mock.Mock(return_value=mapping_mock)
    monkeypatch.setattr('app.company.services.upload_flow_service.DataMappingService', mapping_cls_mock)
    return mapping_mock


@pytest.fixture
def parser_factory_mock(monkeypatch):
    parser_mock = mock.Mock()
    parser_mock.file_content_bytes = b"csv-data"
    parser_mock.get_chart_of_accounts.return_value = ['現金']
    parser_mock.get_journals.return_value = pd.DataFrame({'借方勘定科目': ['売上'], '貸方勘定科目': ['現金']})
    factory_mock = mock.Mock(return_value=parser_mock)
    monkeypatch.setattr('app.company.services.upload_flow_service.ParserFactory.create_parser', factory_mock)
    return parser_mock


@pytest.fixture
def financial_service_mock(monkeypatch):
    fs_mock = mock.Mock()
    fs_mock.create_balance_sheet.return_value = {'assets': {}}
    fs_mock.create_profit_loss_statement.return_value = {'profit': {}}
    fs_mock.get_soa_breakdowns.return_value = {}
    fs_mock.get_account_balances.return_value = {}
    fs_cls_mock = mock.Mock(return_value=fs_mock)
    monkeypatch.setattr('app.company.services.upload_flow_service.FinancialStatementService', fs_cls_mock)
    return fs_mock


@pytest.fixture
def accounting_data_mock(monkeypatch):
    delete_mock = mock.Mock()
    accounting_data_class = mock.Mock()
    accounting_data_class.query = mock.Mock(filter_by=mock.Mock(return_value=mock.Mock(delete=delete_mock)))
    monkeypatch.setattr('app.company.services.upload_flow_service.AccountingData', accounting_data_class)
    return SimpleNamespace(delete=delete_mock, class_mock=accounting_data_class)


@pytest.fixture
def db_session_mock(monkeypatch):
    session_mock = mock.Mock()
    context_manager = mock.MagicMock()
    context_manager.__enter__.return_value = session_mock
    context_manager.__exit__.return_value = False
    monkeypatch.setattr('app.company.services.upload_flow_service.session_scope', mock.Mock(return_value=context_manager))
    add_mock = session_mock.add
    return SimpleNamespace(session=session_mock, add=add_mock)


def test_handle_valid_chart_of_accounts(user_stub, session_stub, parser_factory_mock, mapping_service_mock):
    service = UploadFlowService('chart_of_accounts', user_stub, {'parser_method': 'get_chart_of_accounts'}, session_stub)
    file_storage = DummyFile('coa.csv')

    result = service.handle(file_storage)

    assert isinstance(result, UploadResult)
    assert result.redirect_endpoint == 'company.data_upload_wizard'
    assert result.flash_message[1] == 'success'
    parser_factory_mock.get_chart_of_accounts.assert_called_once()


def test_handle_invalid_extension(user_stub, session_stub):
    service = UploadFlowService('chart_of_accounts', user_stub, {}, session_stub)

    with pytest.raises(UploadValidationError):
        service.handle(DummyFile('invalid.pdf'))


def test_handle_large_file(user_stub, session_stub):
    service = UploadFlowService('chart_of_accounts', user_stub, {}, session_stub)

    big_file = DummyFile('big.csv', content_length=UploadFlowService.MAX_BYTES + 1)
    with pytest.raises(UploadValidationError):
        service.handle(big_file)


def test_handle_journals_success(user_stub, session_stub, parser_factory_mock, mapping_service_mock, financial_service_mock, accounting_data_mock, db_session_mock, monkeypatch):
    service = UploadFlowService('journals', user_stub, {'parser_method': 'get_journals'}, session_stub)

    result = service.handle(DummyFile('journals.csv'))

    assert result.redirect_endpoint == 'company.confirm_trial_balance'
    assert result.flash_message[1] == 'success'
    financial_service_mock.create_balance_sheet.assert_called_once()

    accounting_kwargs = accounting_data_mock.class_mock.call_args.kwargs
    assert accounting_kwargs['schema_version'] == UploadFlowService.DEFAULT_SCHEMA_VERSION
    assert accounting_kwargs['algo_version'] == UploadFlowService.DEFAULT_ALGO_VERSION
    assert accounting_kwargs['source_hash']

    db_session_mock.session.add.assert_called()


def test_handle_journals_with_unmatched_accounts(user_stub, session_stub, parser_factory_mock, mapping_service_mock, financial_service_mock, accounting_data_mock, db_session_mock, monkeypatch):
    mapping_service_mock.get_unmatched_accounts.return_value = ['未マッピング科目']
    service = UploadFlowService('journals', user_stub, {'parser_method': 'get_journals'}, session_stub)

    result = service.handle(DummyFile('journals.csv'))

    assert result.redirect_endpoint == 'company.data_mapping'
    assert result.flash_message[1] == 'warning'
    assert session_stub['unmatched_accounts'] == ['未マッピング科目']


def test_handle_journals_db_failure(user_stub, session_stub, parser_factory_mock, mapping_service_mock, financial_service_mock, accounting_data_mock, db_session_mock, monkeypatch):
    db_session_mock.session.add.side_effect = RuntimeError('db failure')
    service = UploadFlowService('journals', user_stub, {'parser_method': 'get_journals'}, session_stub)

    with pytest.raises(UploadFlowError) as excinfo:
        service.handle(DummyFile('journals.csv'))
    assert 'db failure' in str(excinfo.value)
