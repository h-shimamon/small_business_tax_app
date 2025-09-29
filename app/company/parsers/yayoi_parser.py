# app/company/parsers/yayoi_parser.py
from .base_parser import BaseParser

class YayoiParser(BaseParser):
    SUPPORTED = False
    """
    弥生会計のデータ形式を解析するためのパーサークラス。
    """

    # 弥生会計の仕様
    CHART_OF_ACCOUNTS_HEADER_ROW = 1
    CHART_OF_ACCOUNTS_COLUMN_NAME = '科目名'

    def get_chart_of_accounts(self):
        """
        弥生会計形式のファイルから勘定科目一覧を取得する。
        """
        df = self._read_data(header_row=self.CHART_OF_ACCOUNTS_HEADER_ROW)
        
        if self.CHART_OF_ACCOUNTS_COLUMN_NAME not in df.columns:
            raise Exception(f"列 '{self.CHART_OF_ACCOUNTS_COLUMN_NAME}' が見つかりません。")
            
        return df[self.CHART_OF_ACCOUNTS_COLUMN_NAME].dropna().astype(str).str.strip().unique().tolist()

    def get_journals(self):
        """
        （未実装）弥生会計形式のファイルから仕訳帳データを取得する。
        """
        # TODO: 将来的に仕訳帳のインポート機能をここに実装
        raise NotImplementedError("この機能は現在開発中です。")

    def get_fixed_assets(self):
        """
        固定資産データを取得する。（未実装）
        """
        raise NotImplementedError("このパーサーでは固定資産データの取得はまだ実装されていません。")
