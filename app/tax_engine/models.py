from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

PayloadValue = str | int


@dataclass(frozen=True)
class TaxRates:
    """税率・控除率の集合。"""

    corporate_low: Decimal
    corporate_high: Decimal
    local_corporate: Decimal
    enterprise_low: Decimal
    enterprise_mid: Decimal
    enterprise_high: Decimal
    local_special: Decimal
    prefectural_corporate: Decimal
    municipal_corporate: Decimal


@dataclass(frozen=True)
class EqualizationAmounts:
    """地方税の均等割額。"""

    prefectural: int
    municipal: int


@dataclass(frozen=True)
class TaxPeriod:
    """会計期間情報。"""

    fiscal_start: date | None
    fiscal_end: date | None
    months_in_period: int
    months_truncated: int


@dataclass(frozen=True)
class TaxInput:
    """税計算の入力定義。"""

    period: TaxPeriod
    taxable_income: Decimal
    rates: TaxRates
    equalization: EqualizationAmounts


@dataclass(frozen=True)
class IncomeBands:
    """法人税・外形標準課税の税基準区分と基準額。"""

    corporate_income_under: Decimal
    corporate_income_over: Decimal
    enterprise_income_limit_u4m: Decimal
    enterprise_income_4m_8m: Decimal
    enterprise_income_over_8m: Decimal
    enterprise_base_u4m: Decimal
    enterprise_base_4m_8m: Decimal
    enterprise_base_over_8m: Decimal


@dataclass(frozen=True)
class TaxComponents:
    """税種別の算出額。"""

    corporate_low: Decimal
    corporate_high: Decimal
    corporate_total: Decimal
    enterprise_low: Decimal
    enterprise_mid: Decimal
    enterprise_high: Decimal
    local_corporate: Decimal
    local_special: Decimal
    prefectural: Decimal
    prefectural_equalization: Decimal
    municipal: Decimal
    municipal_equalization: Decimal

    @property
    def corporate(self) -> Decimal:
        return self.corporate_total

    @property
    def enterprise(self) -> Decimal:
        return self.enterprise_low + self.enterprise_mid + self.enterprise_high

    @property
    def enterprise_with_special(self) -> Decimal:
        return self.enterprise + self.local_special

    @property
    def local_tax_total(self) -> Decimal:
        return (
            self.local_corporate
            + self.enterprise
            + self.local_special
            + self.prefectural
            + self.prefectural_equalization
            + self.municipal
            + self.municipal_equalization
        )

    @property
    def total_tax(self) -> Decimal:
        return self.corporate + self.local_tax_total


@dataclass(frozen=True)
class TaxBreakdown:
    """集計済みの税額と診断情報。"""

    inputs: dict[str, PayloadValue]
    results: dict[str, PayloadValue]
    breakdown: dict[str, int]


@dataclass(frozen=True)
class TaxCalculation:
    """税計算の中間結果。"""

    tax_input: TaxInput
    income_bands: IncomeBands
    components: TaxComponents
    taxable_income: Decimal
    enterprise_tax_base: Decimal
    local_corporate_base: Decimal
    pref_tax_base: Decimal
    municipal_tax_base: Decimal

    def to_payload(self) -> TaxBreakdown:
        """UI互換の辞書ペイロードへ変換。"""
        return TaxBreakdown(
            inputs=self._build_inputs_payload(),
            results=self._build_results_payload(),
            breakdown=self._build_breakdown_payload(),
        )

    def _build_inputs_payload(self) -> dict[str, PayloadValue]:
        period = self.tax_input.period
        return {
            'fiscal_start_date': self._format_date(period.fiscal_start),
            'fiscal_end_date': self._format_date(period.fiscal_end),
            'months_in_period': period.months_in_period,
            'months_truncated': period.months_truncated,
            'pre_tax_income': int(self.taxable_income),
            'corporate_tax_rate_low': self._format_rate(self.tax_input.rates.corporate_low),
            'corporate_tax_rate_high': self._format_rate(self.tax_input.rates.corporate_high),
            'local_corporate_tax_rate': self._format_rate(self.tax_input.rates.local_corporate),
            'enterprise_tax_rate_u4m': self._format_rate(self.tax_input.rates.enterprise_low),
            'enterprise_tax_rate_4m_8m': self._format_rate(self.tax_input.rates.enterprise_mid),
            'enterprise_tax_rate_o8m': self._format_rate(self.tax_input.rates.enterprise_high),
            'local_special_tax_rate': self._format_rate(self.tax_input.rates.local_special),
            'prefectural_corporate_tax_rate': self._format_rate(self.tax_input.rates.prefectural_corporate),
            'prefectural_equalization_amount': self.tax_input.equalization.prefectural,
            'municipal_corporate_tax_rate': self._format_rate(self.tax_input.rates.municipal_corporate),
            'municipal_equalization_amount': self.tax_input.equalization.municipal,
        }

    def _build_results_payload(self) -> dict[str, PayloadValue]:
        enterprise_total = self.components.enterprise
        enterprise_with_special = self.components.enterprise_with_special
        pref_equalization = self.components.prefectural_equalization
        municipal_equalization = self.components.municipal_equalization
        pref_corporate = self.components.prefectural
        municipal_corporate = self.components.municipal

        return {
            'corporate_tax': int(self.components.corporate),
            'local_corporate_tax': int(self.components.local_corporate),
            'local_tax': int(self.components.local_tax_total),
            'total_tax': int(self.components.total_tax),
            'payment_rate': self._format_percent(self.components.total_tax, self.taxable_income),
            'effective_rate': self._format_percent(
                self.components.total_tax,
                self.taxable_income + enterprise_total + self.components.local_special,
            ),
            'enterprise_tax_amount': int(enterprise_total),
            'local_special_tax': int(self.components.local_special),
            'enterprise_tax_total': int(enterprise_with_special),
            'pref_corporate_tax': int(pref_corporate),
            'pref_equalization_amount': int(pref_equalization),
            'pref_tax_total': int(pref_corporate + pref_equalization),
            'enterprise_pref_total': int(enterprise_with_special + pref_corporate + pref_equalization),
            'municipal_corporate_tax': int(municipal_corporate),
            'municipal_equalization_amount': int(municipal_equalization),
            'municipal_tax_total': int(municipal_corporate + municipal_equalization),
        }

    def _build_breakdown_payload(self) -> dict[str, int]:
        bands = self.income_bands
        return {
            'income_u800': int(bands.corporate_income_under),
            'income_o800': int(bands.corporate_income_over),
            'corporate_tax_low_rate': int(self.components.corporate_low),
            'corporate_tax_high_rate': int(self.components.corporate_high),
            'enterprise_tax_base': int(self.enterprise_tax_base),
            'enterprise_income_u4m': int(bands.enterprise_income_limit_u4m),
            'enterprise_base_u4m': int(bands.enterprise_base_u4m),
            'enterprise_income_4m_8m': int(bands.enterprise_income_4m_8m),
            'enterprise_base_4m_8m': int(bands.enterprise_base_4m_8m),
            'enterprise_income_o8m': int(bands.enterprise_income_over_8m),
            'enterprise_base_o8m': int(bands.enterprise_base_over_8m),
            'enterprise_tax_u4m': int(self.components.enterprise_low),
            'enterprise_tax_4m_8m': int(self.components.enterprise_mid),
            'enterprise_tax_o8m': int(self.components.enterprise_high),
            'pref_tax_base': int(self.pref_tax_base),
            'municipal_tax_base': int(self.municipal_tax_base),
        }

    @staticmethod
    def _format_date(value: date | None) -> str:
        if value is None:
            return ''
        return value.strftime('%Y%m%d')

    @staticmethod
    def _format_rate(value: Decimal) -> str:
        if value <= Decimal('0'):
            return ''
        quantized = value.quantize(Decimal('0.01'))
        text = format(quantized, 'f').rstrip('0').rstrip('.')
        return f"{text}%"

    @staticmethod
    def _format_percent(numerator: Decimal, denominator: Decimal) -> str:
        if denominator <= Decimal('0'):
            return ''
        percent = (numerator / denominator * Decimal('100')).quantize(Decimal('0.1'))
        text = format(percent, 'f').rstrip('0').rstrip('.')
        return f"{text}%"
