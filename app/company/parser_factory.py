# app/company/parser_factory.py
from .parsers.moneyforward_parser import MoneyForwardParser
from .parsers.yayoi_parser import YayoiParser
from .parsers.freee_parser import FreeeParser
from .parsers.other_parser import OtherParser

class ParserFactory:
    """
    会計ソフト名に応じて適切なパーサークラスのインスタンスを生成するファクトリー。
    """
    
    _parsers = {
        'moneyforward': MoneyForwardParser,
        'yayoi': YayoiParser,
        'freee': FreeeParser,
        'other': OtherParser,
    }

    @classmethod
    def create_parser(cls, software_name, file_storage):
        """
        指定された会計ソフトのパーサーインスタンスを生成して返す。

        Args:
            software_name (str): 会計ソフト名 (e.g., 'moneyforward', 'yayoi')。
            file_storage: アップロードされたファイルオブジェクト。

        Returns:
            BaseParser: software_nameに対応するパーサーのインスタンス。

        Raises:
            ValueError: 対応するパーサーが見つからない場合。
        """
        parser_class = cls._parsers.get(software_name)
        if not parser_class:
            raise ValueError(f"'{software_name}' に対応するパーサーが見つかりません。")
        
        return parser_class(file_storage)
