# app/company/services/financial_statement_service.py
from collections import defaultdict
from datetime import datetime
from typing import Optional

import pandas as pd

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
        self._account_balances: dict[int, int] = {}
        self._name_to_id_cache = self._build_name_to_id_map()
        self._pl_cache_key: Optional[tuple] = None
        self._pl_structure_cache: Optional[dict] = None
        self._net_income_cache: Optional[int] = None

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

    def _build_name_to_id_map(self) -> dict[str, int]:
        mapping: dict[str, int] = {}
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

    def _build_account_balances(self, balances) -> dict[int, int]:
        totals: dict[int, int] = {}
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

    def get_account_balances(self) -> dict[str, int]:
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

    def _get_pl_statement(self, balances):
        cache_key = tuple(sorted(balances.items())) if balances else None
        if (
            cache_key is not None
            and self._pl_cache_key == cache_key
            and self._pl_structure_cache is not None
        ):
            return self._pl_structure_cache, self._net_income_cache or 0

        pl_structure, net_income = self._create_profit_and_loss_statement_data(balances)
        self._pl_cache_key = cache_key
        self._pl_structure_cache = pl_structure
        self._net_income_cache = net_income
        return pl_structure, net_income

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
        _, net_income = self._get_pl_statement(all_balances)

        adjusted_balances = dict(all_balances)
        final_bs_balances = {acc: amount for acc, amount in adjusted_balances.items() if acc in self.bs_master.index}
        opening_retained_earnings = self.opening_balances.get('繰越利益剰余金', 0)
        final_bs_balances['繰越利益剰余金'] = opening_retained_earnings - net_income
        adjusted_balances['繰越利益剰余金'] = final_bs_balances['繰越利益剰余金']

        self._account_balances = self._build_account_balances(adjusted_balances)
        self._soa_breakdowns = self._compute_breakdown_totals(adjusted_balances)

        return self._build_statement_structure(final_bs_balances, self.bs_master, is_bs=True)

    def create_profit_loss_statement(self):
        """損益計算書を生成する。"""
        all_balances = self._combined_balances()
        if not self._account_balances:
            self._account_balances = self._build_account_balances(all_balances)
        pl_structure, _ = self._get_pl_statement(all_balances)
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

    def _group_balances_by_statement(self, balances, master_df) -> dict[tuple[str | None, str | None, str], int]:
        grouped: dict[tuple[str | None, str | None, str], int] = {}
        if master_df is None or master_df.empty:
            return grouped
        for account_name, amount in balances.items():
            if account_name not in master_df.index:
                continue
            try:
                row = master_df.loc[account_name]
            except Exception:
                continue
            major = row.get('major_category') if isinstance(row, pd.Series) else None
            middle = row.get('middle_category') if isinstance(row, pd.Series) else None
            statement_name = row.get('statement_name') if isinstance(row, pd.Series) else None
            if pd.isna(statement_name) or not str(statement_name).strip():
                statement_name = account_name
            key = (str(major) if major is not None else None, str(middle) if middle is not None else None, str(statement_name))
            grouped[key] = grouped.get(key, 0) + amount
        return grouped

    def _calculate_sort_orders(self, master_df):
        major_order: dict[str, int] = {}
        middle_order: dict[str, int] = {}
        statement_order: dict[tuple[str | None, str | None, str], int] = {}
        if master_df is None or master_df.empty:
            return major_order, middle_order, statement_order
        for account_name in master_df.index:
            try:
                row = master_df.loc[account_name]
            except Exception:
                continue
            number = row.get('number') if isinstance(row, pd.Series) else None
            try:
                numeric_number = int(number)
            except (TypeError, ValueError):
                continue
            major = row.get('major_category') if isinstance(row, pd.Series) else None
            middle = row.get('middle_category') if isinstance(row, pd.Series) else None
            statement_name = row.get('statement_name') if isinstance(row, pd.Series) else None
            if pd.isna(statement_name) or not str(statement_name).strip():
                statement_name = account_name
            if isinstance(major, str) and (major not in major_order or numeric_number < major_order[major]):
                major_order[major] = numeric_number
            if isinstance(middle, str) and (middle not in middle_order or numeric_number < middle_order[middle]):
                middle_order[middle] = numeric_number
            stmt_key = (
                str(major) if major is not None else None,
                str(middle) if middle is not None else None,
                str(statement_name),
            )
            if stmt_key not in statement_order or numeric_number < statement_order[stmt_key]:
                statement_order[stmt_key] = numeric_number
        return major_order, middle_order, statement_order

    def _build_initial_structure(self, grouped_amounts, is_bs: bool):
        from collections import defaultdict as _dd

        structure = _dd(lambda: _dd(lambda: {'items': [], 'total': 0}))
        sign_inversion_majors = {'負債', '純資産'} if is_bs else set()
        for (major, middle, statement_name), amount in grouped_amounts.items():
            safe_major = major or 'その他'
            safe_middle = middle or 'その他'
            display_amount = -amount if (is_bs and safe_major in sign_inversion_majors) else amount
            structure[safe_major][safe_middle]['items'].append({'name': statement_name, 'amount': display_amount})
        return structure

    def _finalize_structure(self, structure, major_order, middle_order, statement_order):
        final_structure: dict[str, dict] = {}
        from math import inf as _inf

        def _major_sort_key(major_name: str):
            return major_order.get(major_name, _inf)

        def _middle_sort_key(middle_name: str):
            return middle_order.get(middle_name, _inf)

        def _statement_sort_key(major_name: str, middle_name: str, statement_name: str):
            return statement_order.get((major_name, middle_name, statement_name), _inf)

        sorted_majors = sorted(structure.keys(), key=_major_sort_key)

        for major in sorted_majors:
            middles = structure[major]
            sorted_middles = sorted(middles.items(), key=lambda item: _middle_sort_key(item[0]))
            major_total = 0
            major_bucket: dict[str, dict] = {}

            for middle, payload in sorted_middles:
                payload['items'].sort(key=lambda item: _statement_sort_key(major, middle, item['name']))
                middle_total = sum(item['amount'] for item in payload['items'])
                payload['total'] = middle_total
                major_total += middle_total
                major_bucket[middle] = payload

            major_bucket['total'] = major_total
            final_structure[major] = major_bucket

        return final_structure

    def _build_statement_structure(self, balances, master_df, is_bs=False):
        """勘定科目残高を財務諸表表示用のネスト構造へ変換する。"""
        grouped_amounts = self._group_balances_by_statement(balances, master_df)
        major_order, middle_order, statement_order = self._calculate_sort_orders(master_df)
        initial_structure = self._build_initial_structure(grouped_amounts, is_bs=is_bs)
        return self._finalize_structure(initial_structure, major_order, middle_order, statement_order)
