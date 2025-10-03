# app/company/services/statement_of_accounts_service.py
from typing import Any, Optional

from flask import current_app

from app.extensions import db
from app.services.db_utils import session_scope
from app.services.soa_registry import STATEMENT_PAGES_CONFIG, get_total_field

from .protocols import StatementOfAccountsServiceProtocol


DEFAULT_ACCOUNT_NAME_BY_PAGE = {
    'accounts_payable': '買掛金',
}


class StatementOfAccountsService(StatementOfAccountsServiceProtocol):
    """
    勘定科目内訳明細書に関連するデータ操作を処理するサービスクラス。
    """

    def __init__(self, company_id):
        self.company_id = company_id

    def _build_query(self, model, config):
        query = model.query.filter_by(company_id=self.company_id)
        query_filter = config.get('query_filter')
        if callable(query_filter):
            try:
                query = query_filter(query)
            except Exception as exc:
                current_app.logger.warning('SoA query filter failed for %s: %s', getattr(model, '__name__', model), exc)
                query = model.query.filter_by(company_id=self.company_id)
        return query

    def _get_model(self, data_type):
        config = STATEMENT_PAGES_CONFIG.get(data_type, {})
        return config.get('model'), config

    def _apply_model_defaults(self, data_type, item) -> None:
        default_name = DEFAULT_ACCOUNT_NAME_BY_PAGE.get(data_type)
        if not default_name or not hasattr(item, 'account_name'):
            return
        current = getattr(item, 'account_name', None)
        if current is None or (isinstance(current, str) and current.strip() == ''):
            setattr(item, 'account_name', default_name)

    def get_all_data(self):
        """
        すべての関連データをデータベースから取得する。
        """
        all_data = {}
        for key in STATEMENT_PAGES_CONFIG.keys():
            all_data[key] = self.get_data_by_type(key)
        return all_data

    def get_data_by_type(self, data_type):
        """
        指定されたタイプのデータを取得する。
        """
        model, config = self._get_model(data_type)
        if not model:
            return None
        query = self._build_query(model, config)
        return query.all()

    def get_item_by_id(self, data_type, item_id) -> Optional[Any]:
        """
        指定されたIDのアイテムを取得する（会社スコープでフィルタ）。
        """
        model, _ = self._get_model(data_type)
        if not model:
            return None
        return db.session.query(model).filter_by(id=item_id, company_id=self.company_id).first()

    def create_item(self, data_type, form) -> tuple[bool, Optional[Any], Optional[str]]:
        model, _ = self._get_model(data_type)
        if not model:
            return False, None, "無効なデータタイプです。"

        item = model(company_id=self.company_id)
        form.populate_obj(item)
        self._apply_model_defaults(data_type, item)
        try:
            with session_scope() as session:
                session.add(item)
            return True, item, None
        except Exception as exc:
            return False, None, f"保存中にエラーが発生しました: {exc}"



    def update_item(self, data_type, item, form) -> tuple[bool, Optional[Any], Optional[str]]:
        model, _ = self._get_model(data_type)
        if not model:
            return False, None, "無効なデータタイプです。"
        if not item:
            return False, None, "指定されたアイテムが見つかりません。"

        form.populate_obj(item)
        self._apply_model_defaults(data_type, item)
        try:
            with session_scope() as session:
                session.add(item)
            return True, item, None
        except Exception as exc:
            return False, None, f"更新中にエラーが発生しました: {exc}"

    def list_items(self, data_type) -> list[Any]:
        items = self.get_data_by_type(data_type)
        return items or []

    def calculate_total(self, data_type, items=None) -> int:
        total_field = get_total_field(data_type)
        target_items = items if items is not None else self.list_items(data_type)
        total = 0
        for item in target_items:
            try:
                value = getattr(item, total_field, 0) or 0
            except Exception:
                value = 0
            total += value
        return total

    def delete_item(self, data_type, item_id) -> tuple[bool, Optional[str]]:
        """

        指定されたIDのアイテムを削除する。
        """
        item = self.get_item_by_id(data_type, item_id)
        if not item:
            return False, "指定されたアイテムが見つかりません。"
        try:
            with session_scope() as session:
                session.delete(item)
            return True, None
        except Exception as exc:
            return False, f"削除中にエラーが発生しました: {exc}"

    def get_summary(self):
        """
        各項目の合計残高をサマリーとして取得する。
        モデルごとの合計列は STATEMENT_PAGES_CONFIG の total_field に従う。
        """
        summary = {}
        for key, config in STATEMENT_PAGES_CONFIG.items():
            model = config.get('model')
            if model is None:
                continue
            total_field = config.get('total_field', 'balance')
            column = getattr(model, total_field, None)
            if column is None:
                summary[key] = 0
                continue
            query = self._build_query(model, config)
            try:
                total = query.with_entities(db.func.sum(column)).scalar() or 0
            except Exception:
                total = 0
            summary[key] = total
        return summary

    def get_deposit_summary(self, bs_deposits_total):
        """
        預貯金の内訳合計と貸借対照表の金額を比較し、サマリーを返す。
        """
        config = STATEMENT_PAGES_CONFIG.get('deposits', {})
        model = config.get('model')
        total_field = config.get('total_field', 'balance')
        column = getattr(model, total_field, None) if model else None

        if model is None or column is None:
            breakdown_total = 0
        else:
            query = self._build_query(model, config)
            try:
                breakdown_total = query.with_entities(db.func.sum(column)).scalar() or 0
            except Exception:
                breakdown_total = 0

        difference = bs_deposits_total - breakdown_total

        return {
            'bs_total': bs_deposits_total,
            'breakdown_total': breakdown_total,
            'difference': difference
        }
