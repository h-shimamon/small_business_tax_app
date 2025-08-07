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
        self.decoded_file, self.delimiter = self._analyze_file()

    def _analyze_file(self):
        """
        アップロードされたファイルを解析し、文字コードと区切り文字を特定する。
        これはすべてのパーサーで共通の処理。

        Returns:
            tuple: (デコードされたテキストIO, 区切り文字)

        Raises:
            Exception: 解析不可能な場合。
        """
        self.file_storage.seek(0)
        content_bytes = self.file_storage.read()
        self.file_storage.seek(0)

        decoded_text = None
        encodings_to_try = ['utf-8-sig', 'utf-8', 'shift_jis']
        for encoding in encodings_to_try:
            try:
                decoded_text = content_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if decoded_text is None:
            raise Exception("ファイルの文字コードを判別できませんでした。UTF-8またはShift-JISで保存してください。")

        try:
            first_line = ""
            for line in decoded_text.splitlines():
                if line.strip():
                    first_line = line
                    break
            if not first_line:
                raise csv.Error("ファイルにデータ行が見つかりません。")

            dialect = csv.Sniffer().sniff(first_line, delimiters=',\t')
            delimiter = dialect.delimiter
        except (csv.Error, IndexError):
            raise Exception("ファイルの区切り文字を判別できませんでした。カンマ(,)またはタブ区切りで保存してください。")

        return io.StringIO(decoded_text), delimiter

    @abstractmethod
    def get_chart_of_accounts(self):
        """
        勘定科目一覧を取得する。
        このメソッドはサブクラスで必ず実装されなければならない。
        """
        pass

    @abstractmethod
    def get_journals(self):
        """
        仕訳帳データを取得する。
        このメソッドはサブクラスで必ず実装されなければならない。
        """
        pass

    def _read_data(self, header_row):
        """
        共通のデータ読み込み処理。

        Args:
            header_row (int): ヘッダーとして使用する行の番号。

        Returns:
            pandas.DataFrame: 読み込まれたデータ。
        """
        try:
            df = pd.read_csv(
                self.decoded_file,
                delimiter=self.delimiter,
                header=header_row,
                skip_blank_lines=True,
                engine='python'
            )
            df.columns = [col.strip() for col in df.columns]
            return df
        except Exception as e:
            raise Exception(f'データ読み込みエラー: {e}')
