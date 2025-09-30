from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

_DECIMAL_ZERO = Decimal("0")
_HUNDRED = Decimal("100")
_THOUSAND = Decimal("1000")


def apply_rate(base: Decimal, rate: Decimal) -> Decimal:
    """基本額に税率を掛け、1円未満四捨五入で整数化。"""
    if base <= _DECIMAL_ZERO or rate <= _DECIMAL_ZERO:
        return _DECIMAL_ZERO
    value = base * rate / _HUNDRED
    return value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def ceil_thousand(value: Decimal) -> Decimal:
    """千円単位で切り上げ。"""
    if value <= _DECIMAL_ZERO:
        return _DECIMAL_ZERO
    quotient = value // _THOUSAND
    remainder = value % _THOUSAND
    if remainder == _DECIMAL_ZERO:
        return quotient * _THOUSAND
    return (quotient + 1) * _THOUSAND


def floor_thousand(value: Decimal) -> Decimal:
    """千円単位で切り捨て。"""
    if value <= _DECIMAL_ZERO:
        return _DECIMAL_ZERO
    return (value // _THOUSAND) * _THOUSAND


def floor_hundred(value: Decimal) -> Decimal:
    """百円単位で切り捨て。"""
    if value <= _DECIMAL_ZERO:
        return _DECIMAL_ZERO
    return (value // _HUNDRED) * _HUNDRED
