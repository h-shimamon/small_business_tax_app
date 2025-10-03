from __future__ import annotations

import hashlib
import os
import shutil
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from flask import current_app

from app.company.models import AccountingData
from app.company.parser_factory import ParserFactory
from app.company.services.data_mapping_service import DataMappingService
from app.company.services.financial_statement_service import FinancialStatementService


from app.navigation import mark_step_as_completed
from app.services.db_utils import session_scope
from app.primitives.dates import get_company_period


UPLOAD_ERROR_MESSAGES: dict[str, dict[str, str]] = {
    'no_file': {
        'title': 'ファイルが選択されていません',
        'body': 'CSV または TXT ファイルを 1 つ選択してから「このファイルをインポートする」を押してください。',
    },
    'unsupported_extension': {
        'title': '未対応のファイル形式です',
        'body': '拡張子が .csv または .txt のファイルのみ取り込めます。ファイル形式をご確認ください。',
    },
    'file_too_large': {
        'title': 'ファイルサイズが上限を超えています',
        'body': '20MB 以下のファイルに分割するか、期間を短くして再度アップロードしてください。',
    },
    'unknown_datatype': {
        'title': '想定外のデータ種別です',
        'body': '画面をリロードしてから再度ウィザードを開始してください。',
    },
    'unknown_error': {
        'title': 'インポート処理でエラーが発生しました',
        'body': 'ファイル内容をご確認のうえ再試行してください。',
    },
}


def build_upload_error_context(code: str | None, fallback: str) -> dict[str, str]:
    info = UPLOAD_ERROR_MESSAGES.get(code or '')
    if info:
        return {'code': code or '', 'title': info['title'], 'body': info['body']}
    return {
        'code': code or '',
        'title': fallback or 'インポート処理に失敗しました',
        'body': fallback or '原因不明のエラーです。再度お試しください。',
    }


@dataclass
class UploadResult:
    """Result payload consumed by the upload_data route."""

    redirect_endpoint: str
    redirect_kwargs: dict[str, Any] = field(default_factory=dict)
    flash_message: tuple[str, str] | None = None


class UploadFlowError(Exception):
    """Generic failure raised during upload processing."""

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.code = code


class UploadValidationError(UploadFlowError):
    """Validation related failure (e.g., extension / size)."""

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message, code=code)


@dataclass
class StoredJournalUpload:
    path: str
    original_name: str


class JournalUploadStore:
    PATH_KEY = 'uploaded_journals_path'
    NAME_KEY = 'uploaded_journals_name'

    def __init__(self, session):
        self._session = session

    def store(self, path: str, original_name: str) -> StoredJournalUpload:
        self._session[self.PATH_KEY] = path
        self._session[self.NAME_KEY] = original_name
        return StoredJournalUpload(path=path, original_name=original_name)

    def retrieve(self) -> Optional[StoredJournalUpload]:
        path = self._session.get(self.PATH_KEY)
        if not path:
            return None
        name = self._session.get(self.NAME_KEY) or ''
        return StoredJournalUpload(path=path, original_name=name)

    def clear(self, *, remove_file: bool = False) -> None:
        record = self.retrieve()
        if remove_file and record and os.path.isfile(record.path):
            try:
                os.remove(record.path)
            except Exception:
                pass
        self._session.pop(self.PATH_KEY, None)
        self._session.pop(self.NAME_KEY, None)

    @classmethod
    def retrieve_from_session(cls, session) -> Optional[StoredJournalUpload]:
        return cls(session).retrieve()


class UploadFlowService:
    """Encapsulates CSV/TXT upload handling for import_data views."""

    ALLOWED_EXTENSIONS = {'.csv', '.txt'}
    MAX_BYTES = 20 * 1024 * 1024
    DEFAULT_SCHEMA_VERSION = '2025.1'
    DEFAULT_ALGO_VERSION = '2025.1'

    def __init__(self, datatype: str, user, config: dict[str, Any], flask_session):
        self.datatype = datatype
        self.user = user
        self.config = config or {}
        self.session = flask_session
        self._journal_store = JournalUploadStore(self.session)

    def handle(self, file_storage) -> UploadResult:
        if not file_storage or not getattr(file_storage, 'filename', None):
            raise UploadValidationError('ファイルが選択されていません。', code='no_file')

        self._validate_file(file_storage)

        parser_method_name = self.config.get('parser_method')
        parser = self._create_parser(file_storage)
        self._persist_raw_upload(parser, file_storage)

        if parser_method_name:
            parser_method = getattr(parser, parser_method_name)
            parsed_data = parser_method()
        else:
            parsed_data = None

        if self.datatype == 'chart_of_accounts':
            return self._handle_chart_of_accounts(parsed_data)
        if self.datatype == 'journals':
            return self._handle_journals(parsed_data)
        if self.datatype == 'fixed_assets':
            return UploadResult('company.fixed_assets_import')

        raise UploadFlowError('無効なデータタイプです。', code='unknown_datatype')

    # --- internal helpers -------------------------------------------------

    def _validate_file(self, file_storage) -> None:
        ext = os.path.splitext(file_storage.filename)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise UploadValidationError('CSVまたはTXTファイルのみアップロードできます。', code='unsupported_extension')

        size = getattr(file_storage, 'content_length', None)
        if size is None:
            try:
                pos = file_storage.stream.tell()
                file_storage.stream.seek(0, os.SEEK_END)
                size = file_storage.stream.tell()
                file_storage.stream.seek(pos)
            except Exception:
                size = None
        if size is not None and size > self.MAX_BYTES:
            raise UploadValidationError('ファイルサイズが大きすぎます。（上限20MB）', code='file_too_large')

        try:
            file_storage.stream.seek(0)
        except Exception:
            pass

    def _create_parser(self, file_storage):
        software = self.session.get('selected_software')
        return ParserFactory.create_parser(software, file_storage)

    def _persist_raw_upload(self, parser, file_storage) -> Optional[StoredJournalUpload]:
        try:
            base_dir = current_app.instance_path
        except Exception:
            return
        if not base_dir:
            return

        upload_dir = os.path.join(base_dir, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        self._cleanup_old_files(upload_dir)

        original_name = getattr(file_storage, 'filename', '') or ''
        suffix = os.path.splitext(original_name)[1].lower()
        filename = f"journals_{uuid.uuid4().hex}{suffix}"
        path = os.path.join(upload_dir, filename)

        raw_bytes = getattr(parser, 'file_content_bytes', None)
        try:
            with open(path, 'wb') as fh:
                if raw_bytes is not None:
                    fh.write(raw_bytes)
                else:
                    try:
                        file_storage.stream.seek(0)
                        shutil.copyfileobj(file_storage.stream, fh, length=1024 * 1024)
                    finally:
                        try:
                            file_storage.stream.seek(0)
                        except Exception:
                            pass
        except Exception as exc:
            current_app.logger.warning('Failed to persist uploaded file: %s', exc)
            return None

        return self._journal_store.store(path, original_name)

    @staticmethod
    def _calculate_dataframe_hash(df) -> str:
        try:
            csv_bytes = df.to_csv(index=False).encode('utf-8')
        except Exception:
            return ''
        return hashlib.sha256(csv_bytes).hexdigest()

    def _build_accounting_metadata(self, journals_df) -> dict[str, str]:
        schema_version = current_app.config.get('ACCOUNTING_DATA_SCHEMA_VERSION', self.DEFAULT_SCHEMA_VERSION)
        algo_version = current_app.config.get('ACCOUNTING_DATA_ALGO_VERSION', self.DEFAULT_ALGO_VERSION)
        source_hash = self._calculate_dataframe_hash(journals_df)
        return {
            'schema_version': schema_version,
            'algo_version': algo_version,
            'source_hash': source_hash,
        }

    @staticmethod
    def _cleanup_old_files(upload_dir: str) -> None:
        ttl = 7 * 24 * 3600
        now = time.time()
        for name in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, name)
            try:
                if os.path.isfile(file_path) and (now - os.path.getmtime(file_path)) > ttl:
                    os.remove(file_path)
            except Exception:
                continue

    def _handle_chart_of_accounts(self, parsed_data) -> UploadResult:
        mapping_service = DataMappingService(self.user.id)
        unmatched_accounts = mapping_service.get_unmatched_accounts(parsed_data)
        if not unmatched_accounts:
            mark_step_as_completed(self.datatype)
            return UploadResult(
                redirect_endpoint='company.data_upload_wizard',
                flash_message=('すべての勘定科目の取り込みが完了しました。', 'success'),
            )

        self.session['unmatched_accounts'] = unmatched_accounts
        return UploadResult(redirect_endpoint='company.data_mapping')

    def _handle_journals(self, parsed_data) -> UploadResult:
        company = getattr(self.user, 'company', None)
        if not company:
            return UploadResult(
                redirect_endpoint='company.declaration',
                flash_message=('申告情報で会計期間が設定されていません。先に基本情報を登録してください。', 'warning'),
            )

        period = get_company_period(company)
        start_date = period.start
        end_date = period.end
        if not start_date or not end_date:
            return UploadResult(
                redirect_endpoint='company.declaration',
                flash_message=('申告情報で会計期間が設定されていません。先に基本情報を登録してください。', 'warning'),
            )

        mapping_service = DataMappingService(self.user.id)
        df_journals = mapping_service.apply_mappings_to_journals(parsed_data)

        try:
            account_names = set()
            for column in ['借方勘定科目', '貸方勘定科目']:
                if column in df_journals.columns:
                    values = df_journals[column].dropna().unique().tolist()
                    account_names.update(str(v).strip() for v in values if str(v).strip())
            unmatched_after = mapping_service.get_unmatched_accounts(list(account_names))
        except Exception:
            unmatched_after = []

        if unmatched_after:
            self.session['unmatched_accounts'] = unmatched_after
            return UploadResult(
                redirect_endpoint='company.data_mapping',
                flash_message=('未マッピングの勘定科目があります。対応後に仕訳帳を再取込してください。', 'warning'),
            )

        fs_service = FinancialStatementService(df_journals, start_date, end_date)
        bs_data = fs_service.create_balance_sheet()
        pl_data = fs_service.create_profit_loss_statement()
        soa_breakdowns = fs_service.get_soa_breakdowns()
        metadata = self._build_accounting_metadata(df_journals)

        try:
            with session_scope() as session:
                session.query(AccountingData).filter_by(company_id=company.id).delete()
                accounting_data = AccountingData(
                    company_id=company.id,
                    period_start=start_date,
                    period_end=end_date,
                    schema_version=metadata['schema_version'],
                    algo_version=metadata['algo_version'],
                    source_hash=metadata['source_hash'],
                    data={
                        'balance_sheet': bs_data,
                        'profit_loss_statement': pl_data,
                        'soa_breakdowns': soa_breakdowns,
                        'account_balances': fs_service.get_account_balances(),
                    },
                )
                session.add(accounting_data)
        except Exception as exc:
            raise UploadFlowError(str(exc)) from exc

        self._journal_store.clear(remove_file=True)
        mark_step_as_completed(self.datatype)
        return UploadResult(
            redirect_endpoint='company.confirm_trial_balance',
            flash_message=('仕訳帳データが正常に取り込まれ、財務諸表が生成されました。', 'success'),
        )
