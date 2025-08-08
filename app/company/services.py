# app/company/services.py
import pandas as pd
from collections import defaultdict
from thefuzz import process
from .forms import DeclarationForm
from .models import (
    Company, Deposit, NotesReceivable, AccountsReceivable, TemporaryPayment,
    LoansReceivable, Inventory, Security, FixedAsset, NotesPayable,
    AccountsPayable, TemporaryReceipt, Borrowing, ExecutiveCompensation,
    LandRent, Miscellaneous, AccountTitleMaster, UserAccountMapping
)
from app import db


class DeclarationService:
    """
    申告書フォームに関連するビジネスロジックを処理するサービスクラス。
    """

    def __init__(self, company_id):
        self.company_id = company_id

    def _get_company(self):
        return Company.query.get_or_404(self.company_id)

    def _get_all_statement_data(self):
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
        company = self._get_company()
        form = DeclarationForm(obj=company)
        return form, company

    def get_context_for_declaration_form(self):
        company = self._get_company()
        statement_data = self._get_all_statement_data()
        context = {'company': company, **statement_data}
        return context

    def update_declaration_data(self, form):
        company = self._get_company()
        form.populate_obj(company)
        db.session.add(company)
        db.session.commit()


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
            for original_name in original_names:
                master_id_str = mappings_form_data.get(f'map_{original_name}')
                if master_id_str and master_id_str.isdigit():
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


class FinancialStatementService:
    """財務諸表の生成に関連するロジックを処理するサービスクラス。"""

    def __init__(self, journal_data):
        self.opening_balances = journal_data.get('opening_balances', {})
        self.mid_year_balances = journal_data.get('mid_year_balances', {})
        self._load_master_data()

    def _load_master_data(self):
        """マスターCSVファイルを読み込み、空行を除去し、インデックスとして設定する。"""
        bs_df = pd.read_csv('resources/masters/balance_sheet.csv', encoding='utf-8-sig')
        bs_df.dropna(subset=['勘定科目名'], inplace=True)
        bs_df['勘定科目名'] = bs_df['勘定科目名'].str.strip()
        self.bs_master = bs_df.set_index('勘定科目名')

        pl_df = pd.read_csv('resources/masters/profit_and_loss.csv', encoding='utf-8-sig')
        pl_df.dropna(subset=['勘定科目名'], inplace=True)
        pl_df['勘定科目名'] = pl_df['勘定科目名'].str.strip()
        self.pl_master = pl_df.set_index('勘定科目名')

    def create_financial_statements(self):
        """貸借対照表と損益計算書を生成する。"""
        all_balances = defaultdict(int, self.opening_balances)
        for acc, amount in self.mid_year_balances.items():
            all_balances[acc] += amount

        pl_statement, net_income = self._create_profit_and_loss_statement(all_balances)
        bs_statement = self._create_balance_sheet(all_balances, net_income)
        
        return bs_statement, pl_statement

    def _create_balance_sheet(self, all_balances, net_income):
        """貸借対照表のデータ構造を生成する。"""
        bs_structure = defaultdict(lambda: defaultdict(lambda: {'items': [], 'total': 0}))
        
        final_bs_balances = {}
        for acc, amount in all_balances.items():
            if acc in self.bs_master.index:
                final_bs_balances[acc] = amount
        
        # 期首の繰越利益剰余金に当期純利益（損失）を加算して期末の繰越利益剰余金を計算
        opening_retained_earnings = self.opening_balances.get('繰越利益剰余金', 0)
        final_bs_balances['繰越利益剰余金'] = opening_retained_earnings + net_income

        for acc, amount in final_bs_balances.items():
            if acc in self.bs_master.index:
                major = self.bs_master.loc[acc, '大分類']
                middle = self.bs_master.loc[acc, '中分類']
                display_amount = -amount if major in ['負債', '純資産'] else amount
                bs_structure[major][middle]['items'].append({'name': acc, 'amount': display_amount})

        for major, middles in bs_structure.items():
            major_total = 0
            for middle, data in middles.items():
                middle_total = sum(item['amount'] for item in data['items'])
                data['total'] = middle_total
                major_total += middle_total
            bs_structure[major]['total'] = major_total
            
        return dict(bs_structure)

    def _create_profit_and_loss_statement(self, all_balances):
        """損益計算書のデータ構造を生成し、当期純利益を返す。"""
        pl_structure = defaultdict(lambda: defaultdict(lambda: {'items': [], 'total': 0}))
        
        for acc, amount in all_balances.items():
            if acc in self.pl_master.index:
                major = self.pl_master.loc[acc, '大分類']
                middle = self.pl_master.loc[acc, '中分類']
                pl_structure[major][middle]['items'].append({'name': acc, 'amount': amount})

        # 中分類ごとの合計を再計算
        for major, middles in pl_structure.items():
            for middle, data in middles.items():
                data['total'] = sum(item['amount'] for item in data['items'])
        
        # 利益計算
        sales = -pl_structure.get('損益', {}).get('売上高', {}).get('total', 0)
        cost_of_sales = pl_structure.get('損益', {}).get('売上原価', {}).get('total', 0)
        sga = pl_structure.get('損益', {}).get('販売費及び一般管理費', {}).get('total', 0)
        non_op_income = -pl_structure.get('損益', {}).get('営業外収益', {}).get('total', 0)
        non_op_expenses = pl_structure.get('損益', {}).get('営業外費用', {}).get('total', 0)
        special_income = -pl_structure.get('損益', {}).get('特別利益', {}).get('total', 0)
        special_expenses = pl_structure.get('損益', {}).get('特別損失', {}).get('total', 0)
        taxes = pl_structure.get('損益', {}).get('法人税等', {}).get('total', 0)

        gross_profit = sales - cost_of_sales
        operating_income = gross_profit - sga
        ordinary_income = operating_income + non_op_income - non_op_expenses
        pre_tax_income = ordinary_income + special_income - special_expenses
        net_income = pre_tax_income - taxes

        pl_structure['利益計算'] = {
            '売上総利益': {'items': [], 'total': gross_profit},
            '営業利益': {'items': [], 'total': operating_income},
            '経常利益': {'items': [], 'total': ordinary_income},
            '税引前当期純利益': {'items': [], 'total': pre_tax_income},
            '当期純利益': {'items': [], 'total': net_income},
        }
        
        return dict(pl_structure), net_income
