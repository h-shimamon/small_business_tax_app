# app/company/parsers/moneyforward_parser.py
from .base_parser import BaseParser

class MoneyForwardParser(BaseParser):
    """
    マネーフォワードのデータ形式を解析するためのパーサークラス。
    """
    
    # マネーフォワードの仕様
    CHART_OF_ACCOUNTS_HEADER_ROW = 0
    CHART_OF_ACCOUNTS_COLUMN_NAME = '勘定科目'

    def get_chart_of_accounts(self):
        """
        マネーフォワード形式のファイルから勘定科目一覧を取得する。
        """
        df = self._read_data(header_row=self.CHART_OF_ACCOUNTS_HEADER_ROW)
        
        if self.CHART_OF_ACCOUNTS_COLUMN_NAME not in df.columns:
            raise Exception(f"列 '{self.CHART_OF_ACCOUNTS_COLUMN_NAME}' が見つかりません。")
            
        return df[self.CHART_OF_ACCOUNTS_COLUMN_NAME].dropna().astype(str).str.strip().unique().tolist()

    def get_journals(self):
        """
        （未実装）マネーフォワード形式のファイルから仕訳帳データを取得する。
        """
        # TODO: 将来的に仕訳帳のインポート機能をここに実装
        raise NotImplementedError("この機能は現在開発中です。")
