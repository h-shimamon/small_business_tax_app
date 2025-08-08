# app/company/parsers/base_parser.py
import pandas as pd
import csv
import io
from abc import ABC, abstractmethod

class BaseParser(ABC):
    """
    ファイル解析のための共通インターフェースと基本機能を提供する抽象基底クラス。
    """
    def __init__(self, file_storage):
        """
        Args:
            file_storage: アップロードされたファイルオブジェクト (FileStorage)。
        """
        self.file_storage = file_storage
        self.file_content_bytes = self.file_storage.read()
        self.file_storage.seek(0)
        self.encoding = self._detect_encoding()
        self.delimiter = self._detect_delimiter()

    def _detect_encoding(self):
        """
        ファイル全体のバイト内容から文字コードを判定する。
        日本語のCSV/TXTで一般的なShift_JIS系統を先に試すことで、誤判定を減らす。
        """
        encodings_to_try = ['shift_jis', 'cp932', 'utf-8-sig', 'utf-8']
        for encoding in encodings_to_try:
            try:
                self.file_content_bytes.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        raise Exception("ファイルの文字コードを判別できませんでした。UTF-8またはShift-JIS系統で保存してください。")

    def _detect_delimiter(self):
        """
        ファイル内容から区切り文字を判定する。
        """
        try:
            decoded_text = self.file_content_bytes.decode(self.encoding)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(decoded_text[:2048], delimiters=',\t')
            return dialect.delimiter
        except (csv.Error, IndexError):
            return ','

    @abstractmethod
    def get_chart_of_accounts(self):
        """
        勘定科目一覧を取得する。
        """
        pass

    @abstractmethod
    def get_journals(self):
        """
        仕訳帳データを取得する。
        """
        pass

    def _read_data(self, header_row, **kwargs):
        """
        共通のデータ読み込み処理。
        """
        try:
            file_buffer = io.BytesIO(self.file_content_bytes)
            
            df = pd.read_csv(
                file_buffer,
                delimiter=self.delimiter,
                header=header_row,
                encoding=self.encoding,
                skip_blank_lines=True,
                engine='python',
                **kwargs
            )
            if header_row is not None and df.columns.size > 0:
                df.columns = [str(col).strip() for col in df.columns]
            return df
        except Exception as e:
            raise Exception(f'データ読み込みエラー: {e}')