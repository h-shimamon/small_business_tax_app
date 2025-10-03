from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import lru_cache
from typing import Any

from app.services.master_data_loader import load_master_dataframe

DEFAULT_CURRENCY_SYMBOL = '円'
DEFAULT_ZERO_MONEY_TEXT = '0円'


def _coerce_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, int):
        decimal_value = Decimal(value)
    elif isinstance(value, float):
        decimal_value = Decimal(str(value))
    elif isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        stripped = stripped.replace(',', '')
        try:
            decimal_value = Decimal(stripped)
        except (InvalidOperation, ValueError):
            return None
    else:
        try:
            decimal_value = Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return None
    if not decimal_value.is_finite():
        return None
    return decimal_value


def _normalize_amount(value: Any) -> int | None:
    decimal_value = _coerce_decimal(value)
    if decimal_value is None:
        return None
    quantized = decimal_value.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return int(quantized)


def _normalize_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return date.fromisoformat(text)
        except ValueError:
            return None
    return None


def money(
    value: Any,
    *,
    currency_symbol: str = DEFAULT_CURRENCY_SYMBOL,
    zero_text: str | None = DEFAULT_ZERO_MONEY_TEXT,
    none_text: str | None = None,
) -> str:
    amount = _normalize_amount(value)
    if amount is None:
        if none_text is not None:
            return none_text
        if zero_text is not None:
            return zero_text
        return ''
    sign = '-' if amount < 0 else ''
    body = f"{abs(amount):,}"
    suffix = currency_symbol if currency_symbol else ''
    formatted = f"{sign}{body}{suffix}"
    if amount == 0 and zero_text is not None:
        return zero_text
    return formatted


def number(value: Any) -> str:
    amount = _normalize_amount(value)
    if amount is None:
        return ''
    return f"{amount:,}"


def date_iso(value: Any) -> str:
    normalized = _normalize_date(value)
    if normalized is None:
        return ''
    return normalized.strftime('%Y-%m-%d')


def date_compact(value: Any) -> str:
    normalized = _normalize_date(value)
    if normalized is None:
        return ''
    return normalized.strftime('%Y%m%d')


def date_kanji(value: Any) -> str:
    normalized = _normalize_date(value)
    if normalized is None:
        return ''
    return normalized.strftime('%Y年%m月%d日')


def format_currency(value):
    """Backward-compatible alias for templates that still expect |format_currency."""
    return money(value)


@lru_cache(maxsize=1)
def _load_master_frames():
    try:
        bs_master_df = load_master_dataframe('resources/masters/balance_sheet.csv', index_column='勘定科目名')
        pl_master_df = load_master_dataframe('resources/masters/profit_and_loss.csv', index_column='勘定科目名')
        return bs_master_df, pl_master_df
    except FileNotFoundError as e:
        raise RuntimeError(f"マスターファイルが見つかりません: {e}. アプリケーションを起動できません。") from e
    except Exception as e:
        raise RuntimeError(f"マスターファイルの読み込み中にエラーが発生しました: {e}") from e


def load_master_data():
    """マスターCSVを読み込み、呼び出し側には複製を返す。"""
    bs_master_df, pl_master_df = _load_master_frames()
    return {
        'bs_master': bs_master_df.copy(deep=True),
        'pl_master': pl_master_df.copy(deep=True)
    }


def format_number(value):
    """整数値を3桁区切りの文字列にフォーマット（単位や通貨記号は付けない）。"""
    amount = _normalize_amount(value)
    if amount is None:
        return ''
    return f"{amount:,}"
