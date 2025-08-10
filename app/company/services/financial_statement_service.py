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
        # B/S関連の勘定科目のみをフィルタリング
        final_bs_balances = {acc: amount for acc, amount in all_balances.items() if acc in self.bs_master.index}
        
        # 期首の繰越利益剰余金に当期純利益（損失）を加算して期末の繰越利益剰余金を計算
        opening_retained_earnings = self.opening_balances.get('繰越利益剰余金', 0)
        
        # P/Lサービスで計算されるnet_incomeは、会計上の利益がプラス、損失がマイナスの値を持つ。
        # 期首の繰越利益剰余金（貸方残高のためマイナス）からnet_incomeを「減算」することで、
        # 利益（プラス値）を足し合わせ（よりマイナスに）、損失（マイナス値）を差し引く（よりプラスに）正しい計算となる。
        final_bs_balances['繰越利益剰余金'] = opening_retained_earnings - net_income

        # 汎用ヘルパーメソッドを呼び出して、ソートとグルーピング済みの構造を取得
        # is_bs=True を渡して、負債・純資産の符号を反転させる
        bs_structure = self._build_statement_structure(final_bs_balances, self.bs_master, is_bs=True)
                
        return bs_structure

    def _create_profit_and_loss_statement(self, all_balances):
        """損益計算書のデータ構造を生成し、当期純利益を返す。"""
        # P/L関連の勘定科目のみをフィルタリング
        pl_balances = {acc: amount for acc, amount in all_balances.items() if acc in self.pl_master.index}
        
        # 汎用ヘルパーメソッドを呼び出して、ソートとグルーピング済みの基本構造を取得
        pl_structure = self._build_statement_structure(pl_balances, self.pl_master, is_bs=False)

        # 利益計算
        # 収益（貸方残高）はマイナス、費用（借方残高）はプラスで計上されているため、計算時に符号を調整する
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
        
        # B/Sの計算で使用するため、会計上の利益（プラスの値）を返す
        return pl_structure, net_income

    def _build_statement_structure(self, balances, master_df, is_bs=False):
        """
        勘定科目の残高とマスターデータから、ソートとグルーピング済みの財務諸表データ構造を構築する汎用メソッド。

        Args:
            balances (dict): 勘定科目名をキー、残高を値とする辞書。
            master_df (pd.DataFrame): '大分類', '中分類', 'No.' 列を含むマスターデータ。
            is_bs (bool): 貸借対照表の場合True。負債と純資産の金額の符号を反転させる。

        Returns:
            dict: 整形された財務諸表データ。
        """
        structure = defaultdict(lambda: defaultdict(lambda: {'items': [], 'total': 0}))

        # is_bsがTrueの場合、表示用に符号を反転させる必要がある科目を特定
        sign_inversion_majors = {'負債', '純資産'} if is_bs else set()

        for acc, amount in balances.items():
            if acc in master_df.index:
                major = master_df.loc[acc, '大分類']
                middle = master_df.loc[acc, '中分類']
                
                display_amount = -amount if major in sign_inversion_majors else amount
                
                structure[major][middle]['items'].append({'name': acc, 'amount': display_amount})

        for major, middles in structure.items():
            major_total = 0
            # 中分類をマスターの 'No.' に基づいてソートするために、一度リストに変換
            sorted_middles = sorted(middles.items(), key=lambda item: master_df[master_df['中分類'] == item[0]]['No.'].min())
            
            # 新しいdefaultdictにソート済みの順序で再挿入
            sorted_structure_major = defaultdict(lambda: {'items': [], 'total': 0})

            for middle, data in sorted_middles:
                # 勘定科目をマスターの'No.'列に基づいてソート
                data['items'].sort(key=lambda x: master_df.loc[x['name'], 'No.'])
                middle_total = sum(item['amount'] for item in data['items'])
                data['total'] = middle_total
                major_total += middle_total
                sorted_structure_major[middle] = data

            structure[major] = sorted_structure_major
            structure[major]['total'] = major_total
            
        return dict(structure)
