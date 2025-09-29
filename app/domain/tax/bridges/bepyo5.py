from __future__ import annotations

from decimal import Decimal
from typing import Dict, Iterable, Mapping


def summarize_retained_earnings(rows: Iterable[Mapping[str, object]]) -> Dict[str, Decimal]:
    """別表5(1)の期首・期末残高を集計。"""

    opening = Decimal('0')
    current = Decimal('0')
    for row in rows:
        opening += _safe_decimal(row.get('opening'))
        current += _safe_decimal(row.get('current'))
    return {
        'opening_balance': opening,
        'closing_balance': opening + current,
    }


def summarize_tax_reserve(rows: Iterable[Mapping[str, object]]) -> Dict[str, Decimal]:
    """別表5(2)の納税充当金変動を集計。"""

    addition = Decimal('0')
    usage = Decimal('0')
    for row in rows:
        addition += _safe_decimal(row.get('addition'))
        usage += _safe_decimal(row.get('usage'))
    return {
        'addition_total': addition,
        'usage_total': usage,
        'ending_balance': addition - usage,
    }


def _safe_decimal(value: object) -> Decimal:
    if value in (None, ''):
        return Decimal('0')
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal('0')
