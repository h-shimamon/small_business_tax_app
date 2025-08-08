# app/company/parsers/moneyforward_parser.py
import pandas as pd
import io
from .base_parser import BaseParser

class MoneyForwardParser(BaseParser):
    """
    マネーフォワードのデータ形式を解析するためのパーサークラス。
    ヘッダーの有無を自動判別して処理する。
    """
    # --- ヘッダーありファイル用の設定 ---
    CHART_OF_ACCOUNTS_HEADER_KEYWORD = '勘定科目'
    JOURNALS_HEADER_KEYWORD = '取引No.'
    JOURNALS_COL_NAMES = {
        'id': '取引No.',
        'date': '取引日',
        'debit_account': '借方勘定科目',
        'debit_amount': '借方金額(円)',
        'credit_account': '貸方勘定科目',
        'credit_amount': '貸方金額(円)',
    }

    # --- ヘッダーなしファイル用の設定 ---
    JOURNALS_COL_INDICES = {
        'id': 1,
        'date': 3,
        'debit_account': 4,
        'debit_amount': 8,
        'credit_account': 10,
        'credit_amount': 14,
    }

    def _find_header_row(self, keyword):
        """指定されたキーワードが含まれる行をヘッダー行として特定する。見つからない場合はNoneを返す。"""
        try:
            decoded_text = self.file_content_bytes.decode(self.encoding)
            lines = decoded_text.splitlines()
            for i, line in enumerate(lines):
                if keyword in line:
                    return i
        except Exception:
            return None
        return None

    def get_chart_of_accounts(self):
        """
        マネーフォワード形式のファイルから勘定科目一覧を取得する。
        """
        header_row = self._find_header_row(self.CHART_OF_ACCOUNTS_HEADER_KEYWORD)
        if header_row is None:
            # 勘定科目ファイルはヘッダーが必須と判断
            raise Exception(f"勘定科目ファイルのヘッダー行（'{self.CHART_OF_ACCOUNTS_HEADER_KEYWORD}'を含む行）が見つかりませんでした。")

        df = self._read_data(header_row=header_row)
        
        if self.CHART_OF_ACCOUNTS_HEADER_KEYWORD not in df.columns:
            raise Exception(f"列 '{self.CHART_OF_ACCOUNTS_HEADER_KEYWORD}' が見つかりません。")
            
        return df[self.CHART_OF_ACCOUNTS_HEADER_KEYWORD].dropna().astype(str).str.strip().unique().tolist()

    def get_journals(self):
        """
        マネーフォワード形式のファイルから仕訳帳データを解析し、財務諸表用のデータを返す。
        """
        df = self._read_and_prepare_journals()
        opening_balance_df, mid_year_transactions_df = self._separate_transactions(df)
        opening_balances = self._calculate_balances(opening_balance_df)
        mid_year_balances = self._calculate_balances(mid_year_transactions_df)
        
        return {
            'opening_balances': opening_balances,
            'mid_year_balances': mid_year_balances
        }

    def _read_and_prepare_journals(self):
        """仕訳帳CSVを読み込み、前処理を行う。ヘッダーの有無を自動判別する。"""
        header_row = self._find_header_row(self.JOURNALS_HEADER_KEYWORD)
        
        if header_row is not None:
            # ヘッダーがある場合
            df = self._read_data(header_row=header_row, usecols=self.JOURNALS_COL_NAMES.values())
            df.rename(columns={v: k for k, v in self.JOURNALS_COL_NAMES.items()}, inplace=True)
        else:
            # ヘッダーがない場合
            df = self._read_data(header_row=None, usecols=self.JOURNALS_COL_INDICES.values())
            df.columns = self.JOURNALS_COL_INDICES.keys()

        # --- 共通のデータクレンジング処理 ---
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['debit_amount'] = pd.to_numeric(df['debit_amount'], errors='coerce').fillna(0)
        df['credit_amount'] = pd.to_numeric(df['credit_amount'], errors='coerce').fillna(0)
        
        df['debit_account'] = df['debit_account'].astype(str).str.strip()
        df['credit_account'] = df['credit_account'].astype(str).str.strip()

        df.dropna(subset=['id', 'date'], inplace=True)
        
        return df

    def _separate_transactions(self, df):
        """データフレームを期首残高と期中取引に分離する。"""
        start_month = df['date'].min().month
        start_month_df = df[df['date'].dt.month == start_month]
        capital_transactions = start_month_df[start_month_df['credit_account'] == '資本金']
        
        if capital_transactions.empty:
            return pd.DataFrame(), df

        opening_balance_tx_ids = capital_transactions['id'].unique()
        opening_balance_mask = df['id'].isin(opening_balance_tx_ids)
        opening_balance_df = df[opening_balance_mask]
        mid_year_transactions_df = df[~opening_balance_mask]
        
        return opening_balance_df, mid_year_transactions_df

    def _calculate_balances(self, df):
        """勘定科目ごとの純残高を計算する。借方はプラス、貸方はマイナスとして集計。"""
        if df.empty:
            return {}

        debits = df[['debit_account', 'debit_amount']].rename(
            columns={'debit_account': 'account', 'debit_amount': 'amount'}
        )
        credits = df[['credit_account', 'credit_amount']].rename(
            columns={'credit_account': 'account', 'credit_amount': 'amount'}
        )
        credits['amount'] = -credits['amount']
        
        all_transactions = pd.concat([debits, credits])
        all_transactions = all_transactions[
            all_transactions['account'].notna() & (all_transactions['account'] != 'nan') & (all_transactions['account'] != '')
        ]
        balances = all_transactions.groupby('account')['amount'].sum()
        
        return {k: int(v) for k, v in balances.items() if v != 0}