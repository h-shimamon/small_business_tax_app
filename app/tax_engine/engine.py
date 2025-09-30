from __future__ import annotations

from decimal import Decimal

from .models import (
    EqualizationAmounts,
    IncomeBands,
    TaxCalculation,
    TaxComponents,
    TaxInput,
)
from .rounding import apply_rate, ceil_thousand, floor_hundred, floor_thousand

_DECIMAL_ZERO = Decimal('0')
_HUNDRED = Decimal('100')
_THOUSAND = Decimal('1000')
_TWELVE = Decimal('12')
_EIGHT_MILLION = Decimal('8000000')
_FOUR_MILLION = Decimal('4000000')


def calculate_tax(input_data: TaxInput) -> TaxCalculation:
    """純粋関数で法人税・地方税を集計。"""

    period = input_data.period
    months_in_period = max(period.months_in_period, 1)
    months_truncated = max(period.months_truncated, 1)
    months_in_period_decimal = Decimal(months_in_period)
    months_truncated_decimal = Decimal(months_truncated)

    taxable_income = max(input_data.taxable_income, _DECIMAL_ZERO)

    income_under_limit = (_EIGHT_MILLION * months_in_period_decimal) / _TWELVE
    income_under_limit = ceil_thousand(income_under_limit)
    income_under = min(taxable_income, income_under_limit)
    income_under = max(income_under, _DECIMAL_ZERO)
    income_over_raw = taxable_income - income_under
    income_over = floor_thousand(income_over_raw) if income_over_raw > _DECIMAL_ZERO else _DECIMAL_ZERO

    corporate_low_amount = apply_rate(income_under, input_data.rates.corporate_low)
    corporate_high_amount = apply_rate(income_over, input_data.rates.corporate_high)
    corporate_tax_amount = corporate_low_amount + corporate_high_amount
    corporate_tax_rounded = floor_hundred(corporate_tax_amount)

    enterprise_limit_u4m = (_FOUR_MILLION * months_in_period_decimal) / _TWELVE
    enterprise_tax_base = taxable_income

    enterprise_base_u4m = floor_thousand(min(enterprise_tax_base, enterprise_limit_u4m))
    enterprise_income_4m_8m = max(enterprise_tax_base - enterprise_limit_u4m, _DECIMAL_ZERO)
    enterprise_base_4m_8m = floor_thousand(min(enterprise_income_4m_8m, enterprise_limit_u4m))

    enterprise_income_over_8m = enterprise_tax_base - (enterprise_limit_u4m * 2)
    if enterprise_income_over_8m < _DECIMAL_ZERO:
        enterprise_income_over_8m = _DECIMAL_ZERO
    enterprise_base_over_8m = floor_thousand(enterprise_income_over_8m) if enterprise_income_over_8m > _DECIMAL_ZERO else _DECIMAL_ZERO

    enterprise_tax_low = apply_rate(enterprise_base_u4m, input_data.rates.enterprise_low)
    enterprise_tax_mid_raw = apply_rate(enterprise_base_4m_8m, input_data.rates.enterprise_mid)
    enterprise_tax_mid = floor_hundred(enterprise_tax_mid_raw)
    enterprise_tax_high_raw = apply_rate(enterprise_base_over_8m, input_data.rates.enterprise_high)
    enterprise_tax_high = floor_hundred(enterprise_tax_high_raw)

    enterprise_tax_amount = enterprise_tax_low + enterprise_tax_mid + enterprise_tax_high
    local_special_amount_raw = (enterprise_tax_amount * input_data.rates.local_special) / _HUNDRED
    local_special_amount = floor_hundred(local_special_amount_raw)

    local_corporate_base = floor_thousand(corporate_tax_rounded)
    local_corporate_amount = floor_hundred(apply_rate(local_corporate_base, input_data.rates.local_corporate))

    pref_tax_base = floor_thousand(corporate_tax_rounded)
    prefectural_amount = floor_hundred(apply_rate(pref_tax_base, input_data.rates.prefectural_corporate))
    prefectural_equalization = floor_hundred(
        (Decimal(input_data.equalization.prefectural) / _TWELVE) * months_truncated_decimal
    )

    municipal_tax_base = floor_thousand(corporate_tax_rounded)
    municipal_amount = floor_hundred(apply_rate(municipal_tax_base, input_data.rates.municipal_corporate))
    municipal_equalization = floor_hundred(
        (Decimal(input_data.equalization.municipal) / _TWELVE) * months_truncated_decimal
    )

    components = TaxComponents(
        corporate_low=corporate_low_amount,
        corporate_high=corporate_high_amount,
        corporate_total=corporate_tax_rounded,
        enterprise_low=enterprise_tax_low,
        enterprise_mid=enterprise_tax_mid,
        enterprise_high=enterprise_tax_high,
        local_corporate=local_corporate_amount,
        local_special=local_special_amount,
        prefectural=prefectural_amount,
        prefectural_equalization=prefectural_equalization,
        municipal=municipal_amount,
        municipal_equalization=municipal_equalization,
    )

    income_bands = IncomeBands(
        corporate_income_under=income_under,
        corporate_income_over=income_over,
        enterprise_income_limit_u4m=enterprise_limit_u4m,
        enterprise_income_4m_8m=enterprise_income_4m_8m,
        enterprise_income_over_8m=enterprise_income_over_8m,
        enterprise_base_u4m=enterprise_base_u4m,
        enterprise_base_4m_8m=enterprise_base_4m_8m,
        enterprise_base_over_8m=enterprise_base_over_8m,
    )

    return TaxCalculation(
        tax_input=input_data,
        income_bands=income_bands,
        components=components,
        taxable_income=taxable_income,
        enterprise_tax_base=enterprise_tax_base,
        local_corporate_base=local_corporate_base,
        pref_tax_base=pref_tax_base,
        municipal_tax_base=municipal_tax_base,
    )
