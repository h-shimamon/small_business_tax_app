from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from flask import current_app

from app import db
from app.company.models import AccountingData
from app.company.parser_factory import ParserFactory
from app.company.services.data_mapping_service import DataMappingService
from app.company.services.financial_statement_service import FinancialStatementService
from app.navigation import mark_step_as_completed
from app.primitives.dates import get_company_period


@dataclass
class UploadResult:
    """Result payload consumed by the upload_data route."""

    redirect_endpoint: str
    redirect_kwargs: Dict[str, Any] = field(default_factory=dict)
    flash_message: Optional[tuple[str, str]] = None


class UploadFlowError(Exception):
    """Generic failure raised during upload processing."""


class UploadValidationError(UploadFlowError):
    """Validation related failure (e.g., extension / size)."""


class UploadFlowService:
    """Encapsulates CSV/TXT upload handling for import_data views."""

    ALLOWED_EXTENSIONS = {'.csv', '.txt'}
    MAX_BYTES = 20 * 1024 * 1024

    def __init__(self, datatype: str, user, config: Dict[str, Any], flask_session):
        self.datatype = datatype
        self.user = user
        self.config = config or {}
        self.session = flask_session

    def handle(self, file_storage) -> UploadResult:
        if not file_storage or not getattr(file_storage, 'filename', None):
            raise UploadValidationError('ファイルが選択されていません。')

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

        raise UploadFlowError('無効なデータタイプです。')

    # --- internal helpers -------------------------------------------------

    def _validate_file(self, file_storage) -> None:
        ext = os.path.splitext(file_storage.filename)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise UploadValidationError('CSVまたはTXTファイルのみアップロードできます。')

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
            raise UploadValidationError('ファイルサイズが大きすぎます。（上限20MB）')

        try:
            file_storage.stream.seek(0)
        except Exception:
            pass

    def _create_parser(self, file_storage):
        software = self.session.get('selected_software')
        return ParserFactory.create_parser(software, file_storage)

    def _persist_raw_upload(self, parser, file_storage) -> None:
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
        if raw_bytes is None:
            try:
                file_storage.stream.seek(0)
                raw_bytes = file_storage.read()
            finally:
                try:
                    file_storage.stream.seek(0)
                except Exception:
                    pass

        try:
            with open(path, 'wb') as fh:
                fh.write(raw_bytes or b'')
        except Exception as exc:
            current_app.logger.warning('Failed to persist uploaded file: %s', exc)
            return

        self.session['uploaded_journals_path'] = path
        self.session['uploaded_journals_name'] = original_name

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

        try:
            AccountingData.query.filter_by(company_id=company.id).delete()
            accounting_data = AccountingData(
                company_id=company.id,
                period_start=start_date,
                period_end=end_date,
                data={
                    'balance_sheet': bs_data,
                    'profit_loss_statement': pl_data,
                    'soa_breakdowns': soa_breakdowns,
                },
            )
            db.session.add(accounting_data)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            raise UploadFlowError(str(exc)) from exc

        mark_step_as_completed(self.datatype)
        return UploadResult(
            redirect_endpoint='company.confirm_trial_balance',
            flash_message=('仕訳帳データが正常に取り込まれ、財務諸表が生成されました。', 'success'),
        )
