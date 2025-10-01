from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal

from ..models import EqualizationAmounts, TaxInput, TaxPeriod, TaxRates


def derive_taxable_income(pre_tax_income: Decimal, rows: Iterable[Mapping[str, object]]) -> Decimal:
    """別表4の加算・減算情報から課税所得を復元する。"""

    add_total = Decimal('0')
    deduct_total = Decimal('0')
    for row in rows:
        add_total += _safe_decimal(row.get('add'))
        deduct_total += _safe_decimal(row.get('deduct'))
    return pre_tax_income + add_total - deduct_total


def build_tax_input(
    period: TaxPeriod,
    rates: TaxRates,
    equalization: EqualizationAmounts,
    pre_tax_income: Decimal,
    bepyo4_rows: Iterable[Mapping[str, object]],
) -> TaxInput:
    """別表4を起点に TaxInput を構築。"""

    taxable_income = derive_taxable_income(pre_tax_income, bepyo4_rows)
    return TaxInput(
        period=period,
        taxable_income=taxable_income,
        rates=rates,
        equalization=equalization,
    )


def _safe_decimal(value: object) -> Decimal:
    if value in (None, ''):
        return Decimal('0')
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal('0')
