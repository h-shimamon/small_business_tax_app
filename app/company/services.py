# app/company/services.py
import pandas as pd
from thefuzz import process
from .forms import DeclarationForm
from .models import (
    Company, Deposit, NotesReceivable, AccountsReceivable, TemporaryPayment,
    LoansReceivable, Inventory, Security, FixedAsset, NotesPayable,
    AccountsPayable, TemporaryReceipt, Borrowing, ExecutiveCompensation,
    LandRent, Miscellaneous, AccountTitleMaster, UserAccountMapping
)
from app import db
import csv
import io


class DeclarationService:
    """
    申告書フォームに関連するビジネスロジックを処理するサービスクラス。
    """

    def __init__(self, company_id):
        """
        Args:
            company_id (int): 対象となる会社のID。
        """
        self.company_id = company_id

    def _get_company(self):
        """会社情報を取得する。"""
        return Company.query.get_or_404(self.company_id)

    def _get_all_statement_data(self):
        """勘定科目内訳明細書の全データを取得する。"""
        return {
            'deposits': Deposit.query.filter_by(company_id=self.company_id).all(),
            'notes_receivable': NotesReceivable.query.filter_by(company_id=self.company_id).all(),
            'accounts_receivable': AccountsReceivable.query.filter_by(company_id=self.company_id).all(),
            'temporary_payments': TemporaryPayment.query.filter_by(company_id=self.company_id).all(),
            'loans_receivable': LoansReceivable.query.filter_by(company_id=self.company_id).all(),
            'inventories': Inventory.query.filter_by(company_id=self.company_id).all(),
            'securities': Security.query.filter_by(company_id=self.company_id).all(),
            'fixed_assets': FixedAsset.query.filter_by(company_id=self.company_id).all(),
            'notes_payable': NotesPayable.query.filter_by(company_id=self.company_id).all(),
            'accounts_payable': AccountsPayable.query.filter_by(company_id=self.company_id).all(),
            'temporary_receipts': TemporaryReceipt.query.filter_by(company_id=self.company_id).all(),
            'borrowings': Borrowing.query.filter_by(company_id=self.company_id).all(),
            'executive_compensations': ExecutiveCompensation.query.filter_by(company_id=self.company_id).all(),
            'land_rents': LandRent.query.filter_by(company_id=self.company_id).all(),
            'miscellaneous_items': Miscellaneous.query.filter_by(company_id=self.company_id).all(),
        }

    def populate_declaration_form(self):
        """
        DBから取得したデータで申告書フォームを初期化して返す。
        """
        company = self._get_company()
        form = DeclarationForm(obj=company)
        return form, company

    def get_context_for_declaration_form(self):
        """
        申告書フォーム画面に必要なコンテキスト（データ）をまとめて取得する。
        """
        company = self._get_company()
        statement_data = self._get_all_statement_data()
        
        context = {
            'company': company,
            **statement_data
        }
        return context

    def update_declaration_data(self, form):
        """
        フォームから送信されたデータで会社情報を更新する。
        """
        company = self._get_company()
        form.populate_obj(company)
        db.session.add(company)
        db.session.commit()


class FileUploadService:
    """ファイルアップロードと解析に関連するサービスクラス。"""

    def _analyze_file(self, file_storage):
        """
        アップロードされたファイルを解析し、文字コードと区切り文字を特定する。

        Args:
            file_storage: アップロードされたファイルオブジェクト (FileStorage)。

        Returns:
            tuple: (デコードされたテキストIO, 区切り文字)

        Raises:
            Exception: 解析不可能な場合。
        """
        # ファイルの先頭に戻す
        file_storage.seek(0)
        content_bytes = file_storage.read()
        file_storage.seek(0)

        # 1. 文字コードの判別
        decoded_text = None
        # BOM付きUTF-8も考慮して 'utf-8-sig' を最初に追加
        encodings_to_try = ['utf-8-sig', 'utf-8', 'shift_jis']
        for encoding in encodings_to_try:
            try:
                decoded_text = content_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if decoded_text is None:
            raise Exception("ファイルの文字コードを判別できませんでした。UTF-8またはShift-JISで保存してください。")

        # 2. 区切り文字の判別
        try:
            # 空行をスキップして最初のデータ行を見つける
            first_line = ""
            for line in decoded_text.splitlines():
                if line.strip():
                    first_line = line
                    break
            if not first_line:
                raise csv.Error("ファイルにデータ行が見つかりません。")

            dialect = csv.Sniffer().sniff(first_line, delimiters=',\t')
            delimiter = dialect.delimiter
        except (csv.Error, IndexError):
            raise Exception("ファイルの区切り文字を判別できませんでした。カンマ(,)またはタブ区切りで保存してください。")

        return io.StringIO(decoded_text), delimiter

    def load_chart_of_accounts(self, file, software_config):
        """
        勘定科目一覧のファイルを読み込み、勘定科目名のリストを返す。
        ファイル形式、文字コード、区切り文字は自動判別される。
        
        Args:
            file: アップロードされたファイルオブジェクト。
            software_config (dict): 会計ソフトごとの設定（列名、ヘッダー行）。
        
        Returns:
            list: 勘定科目名のリスト。
        
        Raises:
            Exception: ファイル読み込みや処理中にエラーが発生した場合。
        """
        try:
            decoded_file, delimiter = self._analyze_file(file)
            
            df = pd.read_csv(
                decoded_file,
                delimiter=delimiter,
                header=software_config['header_row'],
                skip_blank_lines=True,
                engine='python' # C engine doesn't support StringIO as well
            )
            
            target_column = software_config['column_name']
            
            # BOMやエンコーディングの影響で列名の先頭に予期せぬ文字が含まれる場合を考慮
            df.columns = [col.strip() for col in df.columns]

            if target_column not in df.columns:
                raise Exception(f"指定された列名 '{target_column}' がファイルに見つかりません。ヘッダー行が正しく設定されているか確認してください。")

            return df[target_column].dropna().astype(str).str.strip().unique().tolist()
        except Exception as e:
            # エラーを呼び出し元に伝播させる
            raise Exception(f'ファイル処理エラー: {e}')


class DataMappingService:
    """勘定科目のマッピングに関連するサービスクラス。"""

    def __init__(self, user_id):
        self.user_id = user_id

    def get_unmatched_accounts(self, user_accounts):
        """
        ユーザーの勘定科目リストから、まだマッピングされていない勘定科目を特定する。
        
        Args:
            user_accounts (list): ユーザーがアップロードした勘定科目リスト。
        
        Returns:
            list: 未マッピングの勘定科目リスト。
        """
        master_account_names = {master.name.strip() for master in AccountTitleMaster.query.all()}
        
        unmatched = []
        for acc in user_accounts:
            # 空白でなく、マスターに存在せず、ユーザーマッピングにも存在しないものを抽出
            if acc and acc not in master_account_names and not UserAccountMapping.query.filter_by(user_id=self.user_id, original_account_name=acc).first():
                unmatched.append(acc)
        return unmatched

    def get_mapping_suggestions(self, unmatched_accounts):
        """
        未マッピングの勘定科目リストに対して、最適なマスター勘定科目を提案する。
        
        Args:
            unmatched_accounts (list): 未マッピングの勘定科目リスト。
        
        Returns:
            list: 提案を含むマッピングアイテムのリスト。
        """
        master_accounts = AccountTitleMaster.query.order_by(
            AccountTitleMaster.major_category,
            AccountTitleMaster.middle_category,
            AccountTitleMaster.number
        ).all()
        master_choices = {master.name: master.id for master in master_accounts}
        
        mapping_items = []
        for account in unmatched_accounts:
            suggested_master_id = None
            # thefuzzで最適な候補を検索 (スコア70以上)
            best_match = process.extractOne(account, master_choices.keys())
            if best_match and best_match[1] > 70:
                suggested_master_id = master_choices[best_match[0]]
            mapping_items.append({
                'original_name': account,
                'suggested_master_id': suggested_master_id
            })
        return mapping_items, master_accounts

    def save_mappings(self, mappings_form_data, software_name):
        """
        ユーザーが送信したマッピング情報をDBに保存する。
        
        Args:
            mappings_form_data (dict): request.formから取得したデータ。
            software_name (str): 会計ソフト名。
        
        Raises:
            Exception: DB保存中にエラーが発生した場合。
        """
        original_names = [key.replace('map_', '') for key in mappings_form_data.keys() if key.startswith('map_')]

        if not software_name or not original_names:
            raise ValueError("セッション情報が不足しています。")

        try:
            for original_name in original_names:
                master_id_str = mappings_form_data.get(f'map_{original_name}')
                if master_id_str and master_id_str.isdigit():
                    # 既存のマッピングがないか再確認
                    if not UserAccountMapping.query.filter_by(user_id=self.user_id, original_account_name=original_name).first():
                        mapping = UserAccountMapping(
                            user_id=self.user_id,
                            software_name=software_name,
                            original_account_name=original_name,
                            master_account_id=int(master_id_str)
                        )
                        db.session.add(mapping)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception(f'データベースへの保存中にエラーが発生しました: {e}')