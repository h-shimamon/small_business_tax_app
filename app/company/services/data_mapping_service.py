# app/company/services/data_mapping_service.py
from collections import defaultdict

from thefuzz import process

from app.company.models import AccountTitleMaster, UserAccountMapping
from app.domain.master.catalog import load_catalog
from app.extensions import db


class DataMappingService:
    """勘定科目のマッピングに関連するサービスクラス。"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.catalog = load_catalog()
        self._master_name_cache = None
        self._existing_mapping_cache = None
        self._master_accounts_cache = None
        self._normalized_master_index = None

    def _get_master_account_names(self) -> set[str]:
        if self._master_name_cache is None:
            normalized = {
                self.catalog.normalize(name)
                for name in self.catalog.canonical_names
            }
            if not normalized:
                normalized = {
                    self.catalog.normalize(master.name)
                    for master in AccountTitleMaster.query.all()
                }
            self._master_name_cache = normalized
        return self._master_name_cache

    def _get_existing_mapping_names(self) -> set[str]:
        if self._existing_mapping_cache is None:
            self._existing_mapping_cache = {
                self._normalize_string(mapping.original_account_name)
                for mapping in UserAccountMapping.query.filter_by(user_id=self.user_id).all()
            }
        return self._existing_mapping_cache

    def _get_master_accounts(self):
        if self._master_accounts_cache is None:
            self._master_accounts_cache = AccountTitleMaster.query.order_by(
                AccountTitleMaster.major_category,
                AccountTitleMaster.middle_category,
                AccountTitleMaster.number,
            ).all()
        return self._master_accounts_cache

    def _get_normalized_master_index(self):
        if self._normalized_master_index is None:
            master_accounts = self._get_master_accounts()
            master_choices = {m.name: m.id for m in master_accounts}

            alias_map_norm = {}
            for alias_norm, target_name in self.catalog.aliases.items():
                if target_name in master_choices:
                    alias_map_norm[alias_norm] = target_name

            master_norm_to_name = {
                self.catalog.normalize(name): name for name in master_choices.keys()
            }
            self._normalized_master_index = (master_choices, alias_map_norm, master_norm_to_name)
        return self._normalized_master_index

    def _normalize_string(self, value: str) -> str:
        return self.catalog.normalize(value)


    def get_unmatched_accounts(self, user_accounts):
        """
        ユーザーアカウントリストとマスターデータを比較し、未マッピングの勘定科目を返す。
        表記ゆれを避けるため、正規化後の文字列で比較する。
        """
        master_account_names = self._get_master_account_names()
        existing_mappings = self._get_existing_mapping_names()

        unmatched = []
        processed_accounts: set[str] = set()

        for acc in user_accounts:
            if not acc:
                continue

            clean_acc = acc.strip()
            normalized = self._normalize_string(clean_acc)
            if not clean_acc or not normalized or normalized in processed_accounts:
                continue

            processed_accounts.add(normalized)

            if normalized not in master_account_names and normalized not in existing_mappings:
                unmatched.append(clean_acc)

        return unmatched

    def get_mapping_suggestions(self, unmatched_accounts):
        master_accounts = self._get_master_accounts()
        master_choices, alias_map_norm, master_norm_to_name = self._get_normalized_master_index()

        mapping_items = []
        for account in unmatched_accounts:
            suggested_master_id = None
            norm_acc = self._normalize_string(account)

            alias_target = alias_map_norm.get(norm_acc)
            if alias_target and alias_target in master_choices:
                suggested_master_id = master_choices[alias_target]
            else:
                best_match = process.extractOne(account, master_choices.keys())
                if best_match and best_match[1] > 65:
                    suggested_master_id = master_choices[best_match[0]]
                else:
                    best_norm = process.extractOne(norm_acc, list(master_norm_to_name.keys()))
                    if best_norm and best_norm[1] > 70:
                        target_name = master_norm_to_name[best_norm[0]]
                        suggested_master_id = master_choices.get(target_name)

            mapping_items.append({
                'original_name': account,
                'suggested_master_id': suggested_master_id,
            })
        return mapping_items, master_accounts

    def save_mappings(self, mappings_form_data, software_name):
        original_names = [key.replace('map_', '') for key in mappings_form_data.keys() if key.startswith('map_')]
        if not software_name or not original_names:
            raise ValueError("セッション情報が不足しています。")

        try:
            existing_mapping_set = set(self._get_existing_mapping_names())

            new_mappings = []
            for original_name in original_names:
                normalized = self.catalog.normalize(original_name)
                if not normalized or normalized in existing_mapping_set:
                    continue

                master_id_str = mappings_form_data.get(f'map_{original_name}')
                if master_id_str and master_id_str.isdigit():
                    mapping = UserAccountMapping(
                        user_id=self.user_id,
                        software_name=software_name,
                        original_account_name=original_name,
                        master_account_id=int(master_id_str),
                    )
                    new_mappings.append(mapping)
                    existing_mapping_set.add(normalized)

            if new_mappings:
                db.session.add_all(new_mappings)

            db.session.commit()
            self._existing_mapping_cache = None
        except Exception as e:
            db.session.rollback()
            raise Exception(f'データベースへの保存中にエラーが発生しました: {e}') from e

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