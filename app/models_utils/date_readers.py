"""共通の日付ユーティリティ。

- normalize_date: あらゆる入力（date/datetime/ISO文字列/空文字）を date | None に正規化。
- to_iso: date | None を ISO 文字列へ変換（None は None を返す）。
- DateValue: 正規化結果と ISO 表現を保持する簡易 Value Object。
- company_* / notes_*: 既存モデル向けのアクセッサを DateValue ベースで再実装。

従来の ensure_date/to_iso API は後方互換のため残しつつ、新ロジックへ委譲する。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable


@dataclass(frozen=True)
class DateValue:
    """日付の正規化結果と ISO 表現を併せて扱うための Value Object。"""

    raw: Any
    date: date | None
    iso: str | None

    @classmethod
    def from_value(cls, value: Any) -> "DateValue":
        normalized = normalize_date(value)
        return cls(raw=value, date=normalized, iso=to_iso(normalized))

    def __bool__(self) -> bool:  # pragma: no cover - 単純判定
        return self.date is not None


def normalize_date(value: Any) -> date | None:
    """date/datetime/ISO文字列/空文字などを安全に date | None へ変換する。"""
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        # datetime は date のサブクラス扱いになるので順序に注意
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, DateValue):
        return value.date

    text = str(value).strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except Exception:
        return None


def to_iso(value: Any) -> str | None:
    """date | None | DateValue から ISO 文字列 (YYYY-MM-DD) を取得する。"""
    if isinstance(value, DateValue):
        return value.iso
    normalized = normalize_date(value)
    return normalized.isoformat() if isinstance(normalized, date) else None


# 従来 API との互換用エイリアス
ensure_date = normalize_date


def _first_valid_date(values: Iterable[Any]) -> DateValue:
    """複数候補から最初に有効な DateValue を返す。すべて無効なら最初の値を保持した DateValue を返す。"""
    values = list(values)
    for value in values:
        candidate = DateValue.from_value(value)
        if candidate.date is not None:
            return candidate
    return DateValue.from_value(values[0] if values else None)


# --- Company ---
def company_accounting_period_start(company) -> date | None:
    value = _first_valid_date(
        (
            getattr(company, 'accounting_period_start_date', None),
            getattr(company, 'accounting_period_start', None),
        )
    )
    return value.date


def company_accounting_period_end(company) -> date | None:
    value = _first_valid_date(
        (
            getattr(company, 'accounting_period_end_date', None),
            getattr(company, 'accounting_period_end', None),
        )
    )
    return value.date


def company_closing_date(company) -> date | None:
    value = _first_valid_date(
        (
            getattr(company, 'closing_date_date', None),
            getattr(company, 'closing_date', None),
        )
    )
    return value.date


# --- NotesReceivable ---
def notes_receivable_issue_date(nr) -> date | None:
    return normalize_date(getattr(nr, 'issue_date', None))


def notes_receivable_due_date(nr) -> date | None:
    return normalize_date(getattr(nr, 'due_date', None))


__all__ = [
    'DateValue',
    'normalize_date',
    'ensure_date',
    'to_iso',
    'company_accounting_period_start',
    'company_accounting_period_end',
    'company_closing_date',
    'notes_receivable_issue_date',
    'notes_receivable_due_date',
]
