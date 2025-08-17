# app/company/services/statement_of_accounts_service.py
from app.company.models import (
    Deposit, NotesReceivable, AccountsReceivable, TemporaryPayment,
    LoansReceivable, Inventory, Security, FixedAsset, NotesPayable,
    AccountsPayable, TemporaryReceipt, Borrowing, ExecutiveCompensation,
    LandRent, Miscellaneous
)
from app import db


class StatementOfAccountsService:
    """
    勘定科目内訳明細書に関連するデータ操作を処理するサービスクラス。
    """
    MODEL_MAP = {
        'deposits': Deposit,
        'notes_receivable': NotesReceivable,
        'accounts_receivable': AccountsReceivable,
        'temporary_payments': TemporaryPayment,
        'loans_receivable': LoansReceivable,
        'inventories': Inventory,
        'securities': Security,
        'fixed_assets': FixedAsset,
        'notes_payable': NotesPayable,
        'accounts_payable': AccountsPayable,
        'temporary_receipts': TemporaryReceipt,
        'borrowings': Borrowing,
        'executive_compensations': ExecutiveCompensation,
        'land_rents': LandRent,
        'miscellaneous': Miscellaneous,
    }

    def __init__(self, company_id):
        self.company_id = company_id

    def get_all_data(self):
        """
        すべての関連データをデータベースから取得する。
        """
        all_data = {}
        for key, model in self.MODEL_MAP.items():
            all_data[key] = model.query.filter_by(company_id=self.company_id).all()
        return all_data

    def get_data_by_type(self, data_type):
        """
        指定されたタイプのデータを取得する。
        """
        model = self.MODEL_MAP.get(data_type)
        if not model:
            return None
        return model.query.filter_by(company_id=self.company_id).all()

    def get_item_by_id(self, data_type, item_id):
        """
        指定されたIDのアイテムを取得する。
        """
        model = self.MODEL_MAP.get(data_type)
        if not model:
            return None
        return model.query.get(item_id)

    def add_or_update_item(self, form, data_type, item_id=None):
        """
        アイテムを追加または更新する。
        """
        model = self.MODEL_MAP.get(data_type)
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
        """
        summary = {}
        for key, model in self.MODEL_MAP.items():
            total = db.session.query(db.func.sum(model.balance)).filter_by(company_id=self.company_id).scalar()
            summary[key] = total or 0
        return summary

    def get_deposit_summary(self, bs_deposits_total):
        """
        預貯金の内訳合計と貸借対照表の金額を比較し、サマリーを返す。
        """
        breakdown_total = db.session.query(db.func.sum(Deposit.balance)) \
            .filter_by(company_id=self.company_id).scalar() or 0
        
        difference = bs_deposits_total - breakdown_total
        
        return {
            'bs_total': bs_deposits_total,
            'breakdown_total': breakdown_total,
            'difference': difference
        }
