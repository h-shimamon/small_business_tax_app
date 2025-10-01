from __future__ import annotations

import pandas as pd

JOURNAL_COLUMN_ALIASES: dict[str, str] = {
    '取引No.': 'txn_id',
    '伝票No.': 'txn_id',
    '日付': 'date',
    '取引日': 'date',
    '借方勘定科目': 'debit_account',
    '貸方勘定科目': 'credit_account',
    '借方金額': 'debit_amount',
    '貸方金額': 'credit_amount',
    '税区分': 'tax_code',
}


def normalize_journal_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """仕訳DataFrameに正規化カラムを追加する。元の列は保持する。"""
    normalized = df.copy()
    for source, canonical in JOURNAL_COLUMN_ALIASES.items():
        if source in normalized.columns and canonical not in normalized.columns:
            normalized[canonical] = normalized[source]
    return normalized
