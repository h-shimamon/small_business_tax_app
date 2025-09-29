# app/company/parsers/other_parser.py
from .base_parser import BaseParser

class OtherParser(BaseParser):
    SUPPORTED = False
    """
    特定の会計ソフトに依存しない、汎用的なデータ形式を解析するためのパーサークラス。
    【注意】このクラスは雛形であり、まだ実装されていません。
    """

    def get_chart_of_accounts(self):
        """
        汎用形式のファイルから勘定科目一覧を取得する。
        """
        # TODO: 「その他」の場合の仕様（例：ユーザーに列を選択させるなど）に合わせて実装する
        raise NotImplementedError("「その他」を選択した場合のインポート機能は現在開発中です。")

    def get_journals(self):
        """
        汎用形式のファイルから仕訳帳データを取得する。
        """
        # TODO: 「その他」の場合の仕様に合わせて実装する
        raise NotImplementedError("「その他」を選択した場合のインポート機能は現在開発中です。")

    def get_fixed_assets(self):
        """
        固定資産データを取得する。（未実装）
        """
        raise NotImplementedError("このパーサーでは固定資産データの取得はまだ実装されていません。")
