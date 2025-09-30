# app/company/services/financial_statement_service.py
from collections import defaultdict
from typing import Dict, Optional

import pandas as pd
from datetime import datetime

from .master_data_service import MasterDataService

class FinancialStatementService:
    """財務諸表の生成に関連するロジックを処理するサービスクラス。"""

    def __init__(self, journals_df: pd.DataFrame, start_date, end_date):
        """
        Args:
            journals_df (pd.DataFrame): 仕訳帳データフレーム。
            start_date (date): 事業年度の開始日。
            end_date (date): 事業年度の終了日。
        """
        master_data_service = MasterDataService()
        self.journals_df = journals_df
        # DataFrameの型と比較できるよう、dateをdatetimeに変換
        self.start_date = datetime.combine(start_date, datetime.min.time())
        self.end_date = datetime.combine(end_date, datetime.max.time())
        self.bs_master = master_data_service.get_bs_master_df()
        self.pl_master = master_data_service.get_pl_master_df()
        self._soa_breakdowns = {}
        self._account_balances: Dict[int, int] = {}
        self._name_to_id_cache = self._build_name_to_id_map()

        # 期首と期中の取引を分離
        opening_df, mid_year_df = self._separate_transactions(self.journals_df)
        self.opening_balances = self._calculate_balances_from_df(opening_df)
        self.mid_year_balances = self._calculate_balances_from_df(mid_year_df)

    def _separate_transactions(self, df):
        """
        データフレームを期首残高取引と期中取引に分離する。
        マネーフォワードの仕様に基づき、期首月の「資本金」を含む取引を期首取引と見なす。
        """
        if df.empty or '日付' not in df.columns or '貸方勘定科目' not in df.columns:
            return pd.DataFrame(), pd.DataFrame()

        # '日付' 列がNaTでないことを確認
        df_filtered = df.dropna(subset=['日付'])
        if df_filtered.empty:
            return pd.DataFrame(), pd.DataFrame()

        start_month = df_filtered['日付'].min().month
        start_month_df = df_filtered[df_filtered['日付'].dt.month == start_month]
        
        # 'id' 列が存在するか確認
        if 'id' in start_month_df.columns:
            capital_transactions = start_month_df[start_month_df['貸方勘定科目'] == '資本金']
            if capital_transactions.empty:
                return pd.DataFrame(), df

            opening_balance_tx_ids = capital_transactions['id'].unique()
            opening_balance_mask = df['id'].isin(opening_balance_tx_ids)
            
            opening_balance_df = df[opening_balance_mask]
            mid_year_transactions_df = df[~opening_balance_mask]
            
            return opening_balance_df, mid_year_transactions_df
        else:
            # 'id' 列がない場合は、単純な日付で期間を分けるフォールバック
            opening_df = df[df['日付'] < self.start_date]
            mid_year_df = df[(df['日付'] >= self.start_date) & (df['日付'] <= self.end_date)]
            return opening_df, mid_year_df

    def _calculate_balances_from_df(self, df):
        """DataFrameから勘定科目ごとの純残高を計算する。"""
        if df.empty:
            return defaultdict(int)

        debits = df.groupby('借方勘定科目')['借方金額'].sum()
        credits = df.groupby('貸方勘定科目')['貸方金額'].sum()
        
        balances = defaultdict(int)
        for acc, amount in debits.items():
            balances[acc] += amount
        for acc, amount in credits.items():
            balances[acc] -= amount
            
        return {k: v for k, v in balances.items() if v != 0}

    def _build_name_to_id_map(self) -> Dict[str, int]:
        mapping: Dict[str, int] = {}
        for df in (self.bs_master, self.pl_master):
            if df is None or df.empty:
                continue
            if 'id' not in df.columns:
                continue
            try:
                ids = df['id'].to_dict()
            except Exception:
                ids = {}
            for name, raw_id in ids.items():
                try:
                    mapping[str(name)] = int(raw_id)
                except (TypeError, ValueError):
                    continue
        return mapping

    def _lookup_account_id(self, account_name: str) -> Optional[int]:
        return self._name_to_id_cache.get(str(account_name))

    def _build_account_balances(self, balances) -> Dict[int, int]:
        totals: Dict[int, int] = {}
        for acc_name, amount in balances.items():
            account_id = self._lookup_account_id(acc_name)
            if account_id is None:
                continue
            try:
                numeric = int(round(float(amount)))
            except (TypeError, ValueError):
                continue
            if numeric == 0:
                continue
            totals[account_id] = numeric
        return totals

    def get_account_balances(self) -> Dict[str, int]:
        return {str(account_id): amount for account_id, amount in self._account_balances.items()}

    def _combined_balances(self):
        all_balances = defaultdict(int, self.opening_balances)
        for acc, amount in self.mid_year_balances.items():
            all_balances[acc] += amount
        return all_balances

    def _compute_breakdown_totals(self, balances):
        breakdowns = {}
        if self.bs_master is None or self.bs_master.empty:
            return breakdowns
        for acc, amount in balances.items():
            if acc not in self.bs_master.index:
                continue
            doc = self.bs_master.at[acc, 'breakdown_document'] if 'breakdown_document' in self.bs_master.columns else None
            if not isinstance(doc, str) or not doc.strip():
                continue
            breakdowns[doc] = breakdowns.get(doc, 0) + amount
        return breakdowns

    def get_total_by_breakdown_document(self, document_name):
        """指定された内訳書名に該当する勘定科目の合計残高を計算する。"""
        if document_name is None:
            return 0
        if self._soa_breakdowns:
            return self._soa_breakdowns.get(document_name, 0)
        balances = self._combined_balances()
        breakdowns = self._compute_breakdown_totals(balances)
        return breakdowns.get(document_name, 0)

    def create_balance_sheet(self):
        """貸借対照表を生成する。"""
        all_balances = self._combined_balances()
        self._account_balances = self._build_account_balances(all_balances)
        self._soa_breakdowns = self._compute_breakdown_totals(all_balances)

        _, net_income = self._create_profit_and_loss_statement_data(all_balances)

        final_bs_balances = {acc: amount for acc, amount in all_balances.items() if acc in self.bs_master.index}
        opening_retained_earnings = self.opening_balances.get('繰越利益剰余金', 0)
        final_bs_balances['繰越利益剰余金'] = opening_retained_earnings - net_income

        return self._build_statement_structure(final_bs_balances, self.bs_master, is_bs=True)

    def create_profit_loss_statement(self):
        """損益計算書を生成する。"""
        all_balances = self._combined_balances()
        if not self._account_balances:
            self._account_balances = self._build_account_balances(all_balances)
        pl_structure, _ = self._create_profit_and_loss_statement_data(all_balances)
        return pl_structure

    def get_soa_breakdowns(self):
        return dict(self._soa_breakdowns)

    def _create_profit_and_loss_statement_data(self, all_balances):
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
        勘定科目の残高とマスターデータから、ソートとグルーピング済みの財務諸表データ構造を構築する。
        - B/S(is_bs=True) と P/L(is_bs=False) の両方で、明細行は「決算書名」で集約・表示する。
        - 並び順は同一の決算書名グループに属する科目の No. 最小値を用いる。
        """
        from collections import defaultdict as _dd
        import math as _math
        structure = _dd(lambda: _dd(lambda: {'items': [], 'total': 0}))
        sign_inversion_majors = {'負債', '純資産'} if is_bs else set()

        # 共通: 「決算書名」に集約
        grouped = {}
        for acc, amount in balances.items():
            if acc in master_df.index:
                major = master_df.loc[acc, 'major_category']
                middle = master_df.loc[acc, 'middle_category']
                stmt_name = master_df.loc[acc, 'statement_name'] if 'statement_name' in master_df.columns else None
                if pd.isna(stmt_name) or not str(stmt_name).strip():
                    stmt_name = acc  # フォールバック
                key = (major, middle, str(stmt_name))
                grouped[key] = grouped.get(key, 0) + amount

        # 決算書名ごとの表示順（No.の最小値）
        stmt_order = {}
        try:
            for acc in master_df.index:
                major = master_df.at[acc, 'major_category']
                middle = master_df.at[acc, 'middle_category']
                sname = master_df.at[acc, 'statement_name'] if 'statement_name' in master_df.columns else None
                if pd.isna(sname) or not str(sname).strip():
                    sname = acc
                key = (major, middle, str(sname))
                num = master_df.at[acc, 'number']
                try:
                    n = int(num)
                except Exception:
                    continue
                if key not in stmt_order or n < stmt_order[key]:
                    stmt_order[key] = n
        except Exception:
            stmt_order = {}

        # 構造へ流し込み（B/Sは負債・純資産のみ符号反転）
        for (major, middle, sname), amt in grouped.items():
            display_amount = -amt if (is_bs and (major in sign_inversion_majors)) else amt
            structure[major][middle]['items'].append({'name': sname, 'amount': display_amount})

        # ここからは共通: メジャー/ミドル/明細の並びと小計・合計の算出
        final_structure = {}
        # majorの並び順: そのmajorを持つ行のNo.の最小値
        sorted_majors = sorted(structure.keys(), key=lambda m: master_df[master_df['major_category'] == m]['number'].min())

        for major in sorted_majors:
            middles = structure[major]
            major_total = 0

            # middleの並び順: そのmiddleを持つ行のNo.の最小値
            sorted_middles = sorted(
                middles.items(),
                key=lambda item: master_df[master_df['middle_category'] == item[0]]['number'].min()
            )

            sorted_major_content = {}
            for middle, data in sorted_middles:
                # 明細の並び順（決算書名グループのNo.最小でソート）
                def _order_fn(x):
                    try:
                        return stmt_order.get((major, middle, x['name']), _math.inf)
                    except Exception:
                        return _math.inf
                data['items'].sort(key=_order_fn)

                middle_total = sum(item['amount'] for item in data['items'])
                data['total'] = middle_total
                major_total += middle_total
                sorted_major_content[middle] = data

            final_structure[major] = sorted_major_content
            final_structure[major]['total'] = major_total

        return final_structure
