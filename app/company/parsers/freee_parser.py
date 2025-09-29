# app/company/parsers/freee_parser.py
from .base_parser import BaseParser

class FreeeParser(BaseParser):
    SUPPORTED = False
    """
    freeeのデータ形式を解析するためのパーサークラス。
    【注意】このクラスは雛形であり、まだ実装されていません。
    """

    def get_chart_of_accounts(self):
        """
        freee形式のファイルから勘定科目一覧を取得する。
        """
        # TODO: freeeの具体的なファイル仕様（ヘッダー行、列名など）に合わせて実装する
        raise NotImplementedError("freee用の勘定科目インポート機能は現在開発中です。")

    def get_journals(self):
        """
        freee形式のファイルから仕訳帳データを取得する。
        """
        # TODO: freeeの具体的なファイル仕様に合わせて実装する
        raise NotImplementedError("freee用の仕訳帳インポート機能は現在開発中です。")

    def get_fixed_assets(self):
        """
        固定資産データを取得する。（未実装）
        """
        raise NotImplementedError("このパーサーでは固定資産データの取得はまだ実装されていません。")
