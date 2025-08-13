# app/company/services/financial_statement_service.py
from collections import defaultdict
from .master_data_service import MasterDataService

class FinancialStatementService:
    """財務諸表の生成に関連するロジックを処理するサービスクラス。"""

    def __init__(self, journal_data, master_data_service: MasterDataService):
        """
        Args:
            journal_data (dict): 'opening_balances'と'mid_year_balances'を含む辞書。
            master_data_service (MasterDataService): マスターデータを取得するためのサービスインスタンス。
        """
        self.opening_balances = journal_data.get('opening_balances', {})
        self.mid_year_balances = journal_data.get('mid_year_balances', {})
        self.bs_master = master_data_service.get_bs_master_df()
        self.pl_master = master_data_service.get_pl_master_df()

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
        final_bs_balances = {acc: amount for acc, amount in all_balances.items() if acc in self.bs_master.index}
        
        opening_retained_earnings = self.opening_balances.get('繰越利益剰余金', 0)
        final_bs_balances['繰越利益剰余金'] = opening_retained_earnings - net_income

        bs_structure = self._build_statement_structure(final_bs_balances, self.bs_master, is_bs=True)
                
        return bs_structure

    def _create_profit_and_loss_statement(self, all_balances):
        """損益計算書のデータ構造を生成し、当期純利益を返す。"""
        pl_balances = {acc: amount for acc, amount in all_balances.items() if acc in self.pl_master.index}
        
        pl_structure = self._build_statement_structure(pl_balances, self.pl_master, is_bs=False)

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
        
        return pl_structure, net_income

    def _build_statement_structure(self, balances, master_df, is_bs=False):
        """
        勘定科目の残高とマスターデータから、ソートとグルーピング済みの財務諸表データ構造を構築する汎用メソッド。
        中分類と勘定科目をマスターの'No.'列に基づいてソートする。
        """
        structure = defaultdict(lambda: defaultdict(lambda: {'items': [], 'total': 0}))
        sign_inversion_majors = {'負債', '純資産'} if is_bs else set()

        for acc, amount in balances.items():
            if acc in master_df.index:
                major = master_df.loc[acc, 'major_category']
                middle = master_df.loc[acc, 'middle_category']
                display_amount = -amount if major in sign_inversion_majors else amount
                structure[major][middle]['items'].append({'name': acc, 'amount': display_amount})

        # 最終的なデータ構造を順序付きのdictで構築
        final_structure = {}
        # 大分類をソート (例: 資産 -> 負債 -> 純資産)
        # Note: このソート順は現状のロジックでは暗黙的。必要ならマスターに順序カラムを追加すべき。
        sorted_majors = sorted(structure.keys(), key=lambda m: master_df[master_df['major_category'] == m]['number'].min())

        for major in sorted_majors:
            middles = structure[major]
            major_total = 0
            
            # 中分類をマスターの 'No.' に基づいてソート
            sorted_middles = sorted(middles.items(), key=lambda item: master_df[master_df['middle_category'] == item[0]]['number'].min())
            
            # 順序付きのdictにソート済みの中分類を格納
            sorted_major_content = {}
            for middle, data in sorted_middles:
                # 勘定科目をマスターの'No.'列に基づいてソート
                data['items'].sort(key=lambda x: master_df.loc[x['name'], 'number'])
                middle_total = sum(item['amount'] for item in data['items'])
                data['total'] = middle_total
                major_total += middle_total
                sorted_major_content[middle] = data
            
            final_structure[major] = sorted_major_content
            final_structure[major]['total'] = major_total
            
        return final_structure
