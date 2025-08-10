# app/company/services/financial_statement_service.py
from collections import defaultdict

class FinancialStatementService:
    """財務諸表の生成に関連するロジックを処理するサービスクラス。"""

    def __init__(self, journal_data, master_data):
        """
        Args:
            journal_data (dict): 'opening_balances'と'mid_year_balances'を含む辞書。
            master_data (dict): 'bs_master'と'pl_master'のDataFrameを含む辞書。
        """
        self.opening_balances = journal_data.get('opening_balances', {})
        self.mid_year_balances = journal_data.get('mid_year_balances', {})
        self.bs_master = master_data['bs_master']
        self.pl_master = master_data['pl_master']

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
        
        # P/Lサービスで計算されるnet_incomeは、会計上の利益がマイナス、損失がプラスの値を持つ。
        # そのため、期首の繰越利益剰余金からnet_incomeを「減算」することで、
        # 利益（マイナス値）を足し合わせ、損失（プラス値）を差し引く正しい計算となる。
        final_bs_balances['繰越利益剰余金'] = opening_retained_earnings - net_income

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
