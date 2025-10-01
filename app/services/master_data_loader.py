from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache

import pandas as pd


def _strip_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    for column in columns:
        if column in df.columns:
            df[column] = df[column].astype(str).str.strip()


@lru_cache(maxsize=8)
def load_master_dataframe(
    path: str,
    *,
    index_column: str | None = None,
    strip_columns: Iterable[str] = ('勘定科目名',),
) -> pd.DataFrame:
    """共通のマスタCSV読み込みロジック。"""
    df = pd.read_csv(path, encoding='utf-8-sig')
    df.dropna(how='all', inplace=True)
    _strip_columns(df, strip_columns)
    if index_column and index_column in df.columns:
        df = df.set_index(index_column)
    return df


def clear_master_dataframe_cache() -> None:
    """キャッシュを明示的に破棄する。"""
    load_master_dataframe.cache_clear()  # type: ignore[attr-defined]
