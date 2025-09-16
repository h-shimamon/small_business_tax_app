# app/company/services/statement_of_accounts_service.py
from app.company.soa_config import STATEMENT_PAGES_CONFIG
from app import db


class StatementOfAccountsService:
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
            except Exception:
                query = model.query.filter_by(company_id=self.company_id)
        return query

    def _get_model(self, data_type):
        config = STATEMENT_PAGES_CONFIG.get(data_type, {})
        return config.get('model'), config

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

    def get_item_by_id(self, data_type, item_id):
        """
        指定されたIDのアイテムを取得する。
        """
        model, _ = self._get_model(data_type)
        if not model:
            return None
        return model.query.get(item_id)

    def add_or_update_item(self, form, data_type, item_id=None):
        """
        アイテムを追加または更新する。
        """
        model, _ = self._get_model(data_type)
        if not model:
            return False, "無効なデータタイプです。"

        item = self.get_item_by_id(data_type, item_id) if item_id else model(company_id=self.company_id)
        if not item:
            return False, "指定されたアイテムが見つかりません。"

        form.populate_obj(item)
        try:
            db.session.add(item)
            db.session.commit()
            return True, "保存しました。"
        except Exception as e:
            db.session.rollback()
            return False, f"保存中にエラーが発生しました: {e}"

    def delete_item(self, data_type, item_id):
        """

        指定されたIDのアイテムを削除する。
        """
        item = self.get_item_by_id(data_type, item_id)
        if not item:
            return False, "指定されたアイテムが見つかりません。"
        try:
            db.session.delete(item)
            db.session.commit()
            return True, "削除しました。"
        except Exception as e:
            db.session.rollback()
            return False, f"削除中にエラーが発生しました: {e}"

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
