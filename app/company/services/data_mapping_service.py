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
        """
        ユーザーアカウントリストとマスターデータを比較し、未マッピングの勘定科目を返す。
        比較はcase-insensitiveに行う。
        """
        # マスター勘定科目名を小文字のセットとして準備
        master_account_names = {master.name.strip().lower() for master in AccountTitleMaster.query.all()}
        
        # 既存のマッピング（ユーザーが過去に設定したもの）を小文字のセットとして準備
        existing_mappings = {
            mapping.original_account_name.strip().lower()
            for mapping in UserAccountMapping.query.filter_by(user_id=self.user_id).all()
        }
        
        unmatched = []
        # 処理済みの勘定科目を小文字で保持し、重複チェック
        processed_accounts = set()

        for acc in user_accounts:
            if not acc:
                continue
            
            clean_acc = acc.strip()
            clean_acc_lower = clean_acc.lower()

            # 空白のみの文字列や、既に処理済みの勘定科目はスキップ
            if not clean_acc or clean_acc_lower in processed_accounts:
                continue
            
            processed_accounts.add(clean_acc_lower)
            
            # マスターと既存マッピングの両方に存在しないものを抽出（小文字で比較）
            if clean_acc_lower not in master_account_names and clean_acc_lower not in existing_mappings:
                # 画面表示用に、元の表記のままの勘定科目を追加
                unmatched.append(clean_acc)
                
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

    def apply_mappings_to_journals(self, journals_df):
        """
        仕訳帳データフレームの勘定科目名を、保存されたマッピング情報に基づいてマスター名に変換する。
        複数の勘定科目列に対応する。
        """
        # ユーザーのマッピング情報を辞書として取得
        user_mappings = {
            m.original_account_name: m.master_account.name 
            for m in UserAccountMapping.query.filter_by(user_id=self.user_id).all()
        }
        
        # マッピングを適用する可能性のある列名をリスト化
        account_columns = ['借方勘定科目', '貸方勘定科目']
        
        for col in account_columns:
            if col in journals_df.columns:
                # .map() を使って置換。マッピングがない場合は元の値を維持するために .fillna() を使用。
                journals_df[col] = journals_df[col].map(user_mappings).fillna(journals_df[col])
        
        return journals_df