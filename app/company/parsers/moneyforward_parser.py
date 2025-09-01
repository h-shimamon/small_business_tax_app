# app/company/parsers/moneyforward_parser.py
import pandas as pd
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
        'debit_amount': '借方金額',
        'credit_account': '貸方勘定科目',
        'credit_amount': '貸方金額',
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
        マネーフォワード形式のファイルから仕訳帳データを解析し、
        正規化されたDataFrameを返す。
        """
        df = self._read_and_prepare_journals()
        
        # FinancialStatementServiceが期待する内部的な列名に統一する
        return df.rename(columns={
            'debit_account': '借方勘定科目',
            'credit_account': '貸方勘定科目',
            'debit_amount': '借方金額',
            'credit_amount': '貸方金額',
            'date': '日付'
        })

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

    def get_fixed_assets(self):
        """
        固定資産データ（マネーフォワード形式）を解析して正規化したリストを返す。
        返却形式: list[dict]
        - acquisition_date: ISO文字列 (YYYY-MM-DD) または None
        - asset_type, name, depreciation_method: str
        - quantity_or_area: float | None
        - useful_life: float | None
        - period_this_year: str | None  # 本年度中の償却期間（表示用に生値を保持）
        - opening_balance, planned_depreciation, special_depreciation, expense_amount, closing_balance, acquisition_cost: int
        - depreciation_rate: float | None
        - business_usage_ratio: float | None
        - note1, note2: str | None
        """
        import pandas as pd

        HEADER_KEYWORD = '取得日'
        header_row = self._find_header_row(HEADER_KEYWORD) or self._find_header_row('種類')
        if header_row is None:
            raise Exception("固定資産ファイルのヘッダー行（'取得日' などを含む行）が見つかりませんでした。")

        df = self._read_data(header_row=header_row)
        # 必須/想定カラム
        jp_cols = [
            '取得日','種類','名前','数量/面積','取得価額','償却保証額','償却の基礎になる金額','減価償却方法','耐用年数',
            '今期償却前残高','今期償却予定額','特別償却額','償却率','本年度中の償却期間','今期償却後残高','経費算入額','事業利用比率(%)','摘要1','摘要2'
        ]
        missing = [c for c in jp_cols if c not in df.columns]
        if missing:
            # 必須最小セットで再判定（画面表示に使うカラム）
            min_set = ['取得日','種類','名前','数量/面積','取得価額','減価償却方法','耐用年数','本年度中の償却期間','今期償却前残高','今期償却予定額','特別償却額','経費算入額','今期償却後残高']
            still_missing = [c for c in min_set if c not in df.columns]
            if still_missing:
                raise Exception(f"固定資産ファイルに必要な列が見つかりません: {still_missing}")
            # 最小セットで進む（将来拡張のため列が有れば使う）

        # 数値変換ヘルパ
        def _num(series):
            return pd.to_numeric(series, errors='coerce')

        # 正規化用の安全コピー
        s = lambda name: df[name] if name in df.columns else pd.Series([None]*len(df))
        out = pd.DataFrame({
            'acquisition_date': pd.to_datetime(s('取得日'), errors='coerce').dt.date.astype('string'),
            'asset_type': s('種類').astype('string').str.strip(),
            'name': s('名前').astype('string').str.strip(),
            'quantity_or_area': _num(s('数量/面積')),
            'acquisition_cost': _num(s('取得価額')).fillna(0).astype('Int64'),
            'depreciation_method': s('減価償却方法').astype('string').str.strip(),
            'useful_life': _num(s('耐用年数')),
            'period_this_year': s('本年度中の償却期間').astype('string').str.strip(),
            'opening_balance': _num(s('今期償却前残高')).fillna(0).astype('Int64'),
            'planned_depreciation': _num(s('今期償却予定額')).fillna(0).astype('Int64'),
            'special_depreciation': _num(s('特別償却額')).fillna(0).astype('Int64'),
            'expense_amount': _num(s('経費算入額')).fillna(0).astype('Int64'),
            'closing_balance': _num(s('今期償却後残高')).fillna(0).astype('Int64'),
            'depreciation_rate': _num(s('償却率')),
            'business_usage_ratio': _num(s('事業利用比率(%)')),
            'note1': s('摘要1').astype('string'),
            'note2': s('摘要2').astype('string'),
        })

        # 文字列Noneを本当のNoneへ（後段で扱いやすく）
        out = out.replace({pd.NA: None, 'NaT': None, '': None})
        # 日付はISO文字列に整形
        if 'acquisition_date' in out.columns:
            out['acquisition_date'] = out['acquisition_date'].apply(lambda d: None if d in (None, 'NaT') else str(d))

        return out.to_dict(orient='records')
