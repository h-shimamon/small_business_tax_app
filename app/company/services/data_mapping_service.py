# app/company/services/data_mapping_service.py
from collections import defaultdict
from thefuzz import process
from app.company.models import AccountTitleMaster, UserAccountMapping
from app import db


class DataMappingService:
    """勘定科目のマッピングに関連するサービスクラス。"""

    def __init__(self, user_id):
        self.user_id = user_id

    def get_unmatched_accounts(self, user_accounts):
        master_account_names = {master.name.strip() for master in AccountTitleMaster.query.all()}
        unmatched = []
        for acc in user_accounts:
            if acc and acc not in master_account_names and not UserAccountMapping.query.filter_by(user_id=self.user_id, original_account_name=acc).first():
                unmatched.append(acc)
        return unmatched

    def get_mapping_suggestions(self, unmatched_accounts):
        master_accounts = AccountTitleMaster.query.order_by(
            AccountTitleMaster.major_category,
            AccountTitleMaster.middle_category,
            AccountTitleMaster.number
        ).all()
        master_choices = {master.name: master.id for master in master_accounts}
        
        mapping_items = []
        for account in unmatched_accounts:
            suggested_master_id = None
            best_match = process.extractOne(account, master_choices.keys())
            if best_match and best_match[1] > 70:
                suggested_master_id = master_choices[best_match[0]]
            mapping_items.append({
                'original_name': account,
                'suggested_master_id': suggested_master_id
            })
        return mapping_items, master_accounts

    def save_mappings(self, mappings_form_data, software_name):
        original_names = [key.replace('map_', '') for key in mappings_form_data.keys() if key.startswith('map_')]
        if not software_name or not original_names:
            raise ValueError("セッション情報が不足しています。")

        try:
            # 既存のマッピングを一括で取得し、セットに変換して高速な存在チェックを可能にする
            existing_mappings = db.session.query(UserAccountMapping.original_account_name).filter_by(user_id=self.user_id).all()
            existing_mapping_set = {item.original_account_name for item in existing_mappings}

            new_mappings = []
            for original_name in original_names:
                # セットでの存在チェック (DBクエリは発生しない)
                if original_name in existing_mapping_set:
                    continue

                master_id_str = mappings_form_data.get(f'map_{original_name}')
                if master_id_str and master_id_str.isdigit():
                    mapping = UserAccountMapping(
                        user_id=self.user_id,
                        software_name=software_name,
                        original_account_name=original_name,
                        master_account_id=int(master_id_str)
                    )
                    new_mappings.append(mapping)
            
            if new_mappings:
                db.session.add_all(new_mappings)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f'データベースへの保存中にエラーが発生しました: {e}')

    def apply_mappings_to_balances(self, balances):
        """
        残高辞書のキー（勘定科目名）を、保存されたマッピング情報に基づいてマスター名に変換する。
        """
        mapped_balances = defaultdict(int)
        mappings = {m.original_account_name: m.master_account.name for m in UserAccountMapping.query.filter_by(user_id=self.user_id).all()}
        
        for original_acc, amount in balances.items():
            master_acc = mappings.get(original_acc, original_acc)
            mapped_balances[master_acc] += amount
            
        return dict(mapped_balances)
