from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Optional, Tuple

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_

from app import db
from app.company.models import AccountingData, Company, CorporateTaxMaster


_DECIMAL_ZERO = Decimal("0")
_HUNDRED = Decimal("100")
_EIGHT_MILLION = Decimal("8000000")
_FOUR_MILLION = Decimal("4000000")
_TWELVE = Decimal("12")
_THOUSAND = Decimal("1000")


DEFAULT_RATE_VALUES = {
    'corporate_tax_rate_low': Decimal('15.0'),
    'corporate_tax_rate_high': Decimal('23.2'),
    'local_corporate_tax_rate': Decimal('10.3'),
    'enterprise_tax_rate_u4m': Decimal('3.5'),
    'enterprise_tax_rate_4m_8m': Decimal('5.3'),
    'enterprise_tax_rate_o8m': Decimal('7.0'),
    'local_special_tax_rate': Decimal('37.0'),
    'prefectural_corporate_tax_rate': Decimal('1.0'),
    'municipal_corporate_tax_rate': Decimal('6.0'),
}

DEFAULT_AMOUNT_VALUES = {
    'prefectural_equalization_amount': 20000,
    'municipal_equalization_amount': 50000,
}

class CorporateTaxCalculationService:
    """Builds the context dictionaries for the corporate tax calculation page."""

    def build(self, company_id: Optional[int] = None) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        company = db.session.get(Company, company_id) if company_id else None
        master = self._resolve_master(company)
        accounting_data = self._latest_accounting_data(company_id) if company_id else None
        return self._compile(company, master, accounting_data)

    # ----------------------------
    # Internal helpers
    # ----------------------------

    @staticmethod
    def _empty_response() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        return ({}, {}, {})

    @staticmethod
    def _latest_accounting_data(company_id: int) -> Optional[AccountingData]:
        return (
            AccountingData.query
            .filter_by(company_id=company_id)
            .order_by(AccountingData.created_at.desc())
            .first()
        )

    @staticmethod
    def _resolve_master(company: Optional[Company]) -> Optional[CorporateTaxMaster]:
        if company is None:
            return CorporateTaxMaster.query.order_by(CorporateTaxMaster.fiscal_start_date.desc()).first()
        start = CorporateTaxCalculationService._coerce_date(
            company.accounting_period_start_date,
            company.accounting_period_start,
        )
        query = CorporateTaxMaster.query
        if start:
            query = query.filter(
                and_(
                    CorporateTaxMaster.fiscal_start_date <= start,
                    CorporateTaxMaster.fiscal_end_date >= start,
                )
            )
        master = query.order_by(CorporateTaxMaster.fiscal_start_date.desc()).first()
        if master:
            return master
        return CorporateTaxMaster.query.order_by(CorporateTaxMaster.fiscal_start_date.desc()).first()

    @staticmethod
    def _coerce_date(value: Optional[date], fallback: Optional[str]) -> Optional[date]:
        if isinstance(value, date):
            return value
        if isinstance(fallback, str) and fallback:
            try:
                return datetime.strptime(fallback, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None

    def _compile(
        self,
        company: Optional[Company],
        master: Optional[CorporateTaxMaster],
        accounting_data: Optional[AccountingData],
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        fiscal_start = self._coerce_date(
            company.accounting_period_start_date,
            company.accounting_period_start,
        ) if company else None
        fiscal_end = self._coerce_date(
            company.accounting_period_end_date,
            company.accounting_period_end,
        ) if company else None
        if not fiscal_start and master is not None:
            fiscal_start = master.fiscal_start_date
        if not fiscal_end and master is not None:
            fiscal_end = master.fiscal_end_date
        period_months = self._resolve_period_months(company, master, fiscal_start, fiscal_end)

        pre_tax_income = self._extract_pre_tax_income(accounting_data)

        rate_values = {
            'corporate_tax_rate_low': getattr(master, 'corporate_tax_rate_u8m', None) if master else None,
            'corporate_tax_rate_high': getattr(master, 'corporate_tax_rate_o8m', None) if master else None,
            'local_corporate_tax_rate': getattr(master, 'local_corporate_tax_rate', None) if master else None,
            'enterprise_tax_rate_u4m': getattr(master, 'enterprise_tax_rate_u4m', None) if master else None,
            'enterprise_tax_rate_4m_8m': getattr(master, 'enterprise_tax_rate_4m_8m', None) if master else None,
            'enterprise_tax_rate_o8m': getattr(master, 'enterprise_tax_rate_o8m', None) if master else None,
            'local_special_tax_rate': getattr(master, 'local_special_tax_rate', None) if master else None,
            'prefectural_corporate_tax_rate': getattr(master, 'prefectural_corporate_tax_rate', None) if master else None,
            'municipal_corporate_tax_rate': getattr(master, 'municipal_corporate_tax_rate', None) if master else None,
        }
        amount_values = {
            'prefectural_equalization_amount': getattr(master, 'prefectural_equalization_amount', None) if master else None,
            'municipal_equalization_amount': getattr(master, 'municipal_equalization_amount', None) if master else None,
        }
        months_truncated = self._resolve_truncated_months(master)

        return self._compute_values(
            fiscal_start,
            fiscal_end,
            period_months,
            months_truncated,
            pre_tax_income,
            rate_values,
            amount_values,
        )

    def _compute_values(
        self,
        fiscal_start: Optional[date],
        fiscal_end: Optional[date],
        period_months: Optional[Any],
        months_truncated: Optional[Any],
        pre_tax_income: Any,
        rate_values: Dict[str, Any],
        amount_values: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        months_in_period_int = self._coerce_int(period_months)
        if months_in_period_int is None or months_in_period_int <= 0:
            months_in_period_int = self._calculate_period_months(fiscal_start, fiscal_end) or 12
        months_truncated_int = self._coerce_int(months_truncated)
        if months_truncated_int is None or months_truncated_int <= 0:
            months_truncated_int = months_in_period_int

        pre_tax_income_decimal = self._decimal(pre_tax_income)
        taxable_income = pre_tax_income_decimal if pre_tax_income_decimal > _DECIMAL_ZERO else _DECIMAL_ZERO

        rate_low = self._with_rate_default(rate_values.get('corporate_tax_rate_low'), 'corporate_tax_rate_low')
        rate_high = self._with_rate_default(rate_values.get('corporate_tax_rate_high'), 'corporate_tax_rate_high')
        local_corp_rate = self._with_rate_default(rate_values.get('local_corporate_tax_rate'), 'local_corporate_tax_rate')
        ent_rate_low = self._with_rate_default(rate_values.get('enterprise_tax_rate_u4m'), 'enterprise_tax_rate_u4m')
        ent_rate_mid = self._with_rate_default(rate_values.get('enterprise_tax_rate_4m_8m'), 'enterprise_tax_rate_4m_8m')
        ent_rate_high = self._with_rate_default(rate_values.get('enterprise_tax_rate_o8m'), 'enterprise_tax_rate_o8m')
        local_special_rate = self._with_rate_default(rate_values.get('local_special_tax_rate'), 'local_special_tax_rate')
        pref_rate = self._with_rate_default(rate_values.get('prefectural_corporate_tax_rate'), 'prefectural_corporate_tax_rate')
        municipal_rate = self._with_rate_default(rate_values.get('municipal_corporate_tax_rate'), 'municipal_corporate_tax_rate')

        pref_equalization_amount = self._with_amount_default(amount_values.get('prefectural_equalization_amount'), 'prefectural_equalization_amount')
        municipal_equalization_amount = self._with_amount_default(amount_values.get('municipal_equalization_amount'), 'municipal_equalization_amount')

        months_in_period_decimal = Decimal(months_in_period_int)

        corporate_income_limit = (_EIGHT_MILLION * months_in_period_decimal) / _TWELVE
        income_u800_limit = self._ceil_thousand(corporate_income_limit)
        income_u800 = min(income_u800_limit, taxable_income)
        if income_u800 < _DECIMAL_ZERO:
            income_u800 = _DECIMAL_ZERO
        income_o800_raw = taxable_income - income_u800
        income_o800 = self._floor_thousand(income_o800_raw) if income_o800_raw > _DECIMAL_ZERO else _DECIMAL_ZERO

        corporate_tax_low_base = min(taxable_income, income_u800)
        corporate_tax_low = self._apply_rate(corporate_tax_low_base, rate_low)

        corporate_tax_high_base = income_o800 if income_o800 > _DECIMAL_ZERO else _DECIMAL_ZERO
        corporate_tax_high = self._apply_rate(corporate_tax_high_base, rate_high)
        enterprise_income_u4m = (_FOUR_MILLION * months_in_period_decimal) / _TWELVE
        enterprise_tax_base_value = taxable_income
        enterprise_base_u4m = self._floor_thousand(min(enterprise_tax_base_value, enterprise_income_u4m))

        enterprise_income_4m_8m = max(enterprise_tax_base_value - enterprise_income_u4m, _DECIMAL_ZERO)
        enterprise_base_4m_8m = self._floor_thousand(min(enterprise_income_4m_8m, enterprise_income_u4m))

        enterprise_income_o8m = enterprise_tax_base_value - (enterprise_income_u4m * 2)
        if enterprise_income_o8m < _DECIMAL_ZERO:
            enterprise_income_o8m = _DECIMAL_ZERO
        enterprise_base_o8m = self._floor_thousand(enterprise_income_o8m) if enterprise_income_o8m > _DECIMAL_ZERO else _DECIMAL_ZERO

        enterprise_tax_u4m = self._apply_rate(enterprise_base_u4m, ent_rate_low)

        enterprise_tax_4m_8m_raw = self._apply_rate(enterprise_base_4m_8m, ent_rate_mid)
        enterprise_tax_4m_8m = self._floor_hundred(enterprise_tax_4m_8m_raw)

        enterprise_tax_o8m_raw = self._apply_rate(enterprise_base_o8m, ent_rate_high)
        enterprise_tax_o8m = self._floor_hundred(enterprise_tax_o8m_raw)

        enterprise_tax_amount = enterprise_tax_u4m + enterprise_tax_4m_8m + enterprise_tax_o8m
        local_special_amount_raw = (enterprise_tax_amount * local_special_rate) / _HUNDRED
        local_special_amount = self._floor_hundred(local_special_amount_raw)

        corporate_tax_amount = corporate_tax_low + corporate_tax_high
        corporate_tax_rounded = self._floor_hundred(corporate_tax_amount)

        local_corporate_base = self._floor_thousand(corporate_tax_rounded)
        local_corporate_tax_amount = self._floor_hundred(self._apply_rate(local_corporate_base, local_corp_rate))

        pref_base = self._floor_thousand(corporate_tax_rounded)
        pref_corporate_amount = self._floor_hundred(self._apply_rate(pref_base, pref_rate))
        months_truncated_decimal = Decimal(months_truncated_int)
        pref_equalization_component = self._floor_hundred(
            (Decimal(pref_equalization_amount) / _TWELVE) * months_truncated_decimal
        )
        pref_tax_amount = pref_corporate_amount + pref_equalization_component

        municipal_corporate_amount = self._floor_hundred(self._apply_rate(pref_base, municipal_rate))
        municipal_equalization_component = self._floor_hundred(
            (Decimal(municipal_equalization_amount) / _TWELVE) * months_truncated_decimal
        )
        municipal_tax_amount = municipal_corporate_amount + municipal_equalization_component

        local_tax_total = (
            local_corporate_tax_amount
            + enterprise_tax_amount
            + local_special_amount
            + pref_tax_amount
            + municipal_tax_amount
        )
        total_tax = corporate_tax_rounded + local_tax_total

        inputs = {
            'fiscal_start_date': self._format_date(fiscal_start),
            'fiscal_end_date': self._format_date(fiscal_end),
            'months_in_period': months_in_period_int,
            'months_truncated': months_truncated_int,
            'pre_tax_income': self._to_int(pre_tax_income_decimal),
            'corporate_tax_rate_low': self._format_rate(rate_low),
            'corporate_tax_rate_high': self._format_rate(rate_high),
            'local_corporate_tax_rate': self._format_rate(local_corp_rate),
            'enterprise_tax_rate_u4m': self._format_rate(ent_rate_low),
            'enterprise_tax_rate_4m_8m': self._format_rate(ent_rate_mid),
            'enterprise_tax_rate_o8m': self._format_rate(ent_rate_high),
            'local_special_tax_rate': self._format_rate(local_special_rate),
            'prefectural_corporate_tax_rate': self._format_rate(pref_rate),
            'prefectural_equalization_amount': pref_equalization_amount,
            'municipal_corporate_tax_rate': self._format_rate(municipal_rate),
            'municipal_equalization_amount': municipal_equalization_amount,
        }

        results = {
            'corporate_tax': self._to_int(corporate_tax_rounded),
            'local_corporate_tax': self._to_int(local_corporate_tax_amount),
            'local_tax': self._to_int(local_tax_total),
            'total_tax': self._to_int(total_tax),
            'payment_rate': self._format_percent(total_tax, pre_tax_income_decimal),
            'effective_rate': self._format_percent(total_tax, pre_tax_income_decimal + enterprise_tax_amount + local_special_amount),
            'enterprise_tax_amount': self._to_int(enterprise_tax_amount),
            'local_special_tax': self._to_int(local_special_amount),
            'enterprise_tax_total': self._to_int(enterprise_tax_amount + local_special_amount),
            'pref_corporate_tax': self._to_int(pref_corporate_amount),
            'pref_equalization_amount': self._to_int(pref_equalization_component),
            'pref_tax_total': self._to_int(pref_tax_amount),
            'enterprise_pref_total': self._to_int(enterprise_tax_amount + local_special_amount + pref_tax_amount),
            'municipal_corporate_tax': self._to_int(municipal_corporate_amount),
            'municipal_equalization_amount': self._to_int(municipal_equalization_component),
            'municipal_tax_total': self._to_int(municipal_tax_amount),
        }

        breakdown = {
            'income_u800': self._to_int(income_u800),
            'income_o800': self._to_int(income_o800),
            'corporate_tax_low_rate': self._to_int(corporate_tax_low),
            'corporate_tax_high_rate': self._to_int(corporate_tax_high),
            'enterprise_tax_base': self._to_int(enterprise_tax_base_value),
            'enterprise_income_u4m': self._to_int(enterprise_income_u4m),
            'enterprise_base_u4m': self._to_int(enterprise_base_u4m),
            'enterprise_income_4m_8m': self._to_int(enterprise_income_4m_8m),
            'enterprise_base_4m_8m': self._to_int(enterprise_base_4m_8m),
            'enterprise_income_o8m': self._to_int(enterprise_income_o8m),
            'enterprise_base_o8m': self._to_int(enterprise_base_o8m),
            'enterprise_tax_u4m': self._to_int(enterprise_tax_u4m),
            'enterprise_tax_4m_8m': self._to_int(enterprise_tax_4m_8m),
            'enterprise_tax_o8m': self._to_int(enterprise_tax_o8m),
            'pref_tax_base': self._to_int(self._floor_thousand(corporate_tax_rounded)),
            'municipal_tax_base': self._to_int(self._floor_thousand(corporate_tax_rounded)),
        }

        return inputs, results, breakdown

    def build_from_manual(self, raw_inputs: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        cleaned = {key: (value.strip() if isinstance(value, str) else value) for key, value in raw_inputs.items()}

        fiscal_start = self._parse_compact_date_text(cleaned.get('fiscal_start_date'))
        fiscal_end = self._parse_compact_date_text(cleaned.get('fiscal_end_date'))

        periods = self._calculate_manual_months(fiscal_start, fiscal_end)

        period_months = self._clean_numeric(cleaned.get('months_in_period'))
        if not period_months and periods[0] is not None:
            period_months = str(periods[0])
        months_truncated = self._clean_numeric(cleaned.get('months_truncated'))
        if not months_truncated and periods[1] is not None:
            months_truncated = str(periods[1])

        if not period_months:
            period_months = '12'
        if not months_truncated:
            months_truncated = period_months

        pre_tax_income = self._clean_numeric(cleaned.get('pre_tax_income'))

        rate_values = {
            'corporate_tax_rate_low': self._clean_rate(cleaned.get('corporate_tax_rate_low')),
            'corporate_tax_rate_high': self._clean_rate(cleaned.get('corporate_tax_rate_high')),
            'local_corporate_tax_rate': self._clean_rate(cleaned.get('local_corporate_tax_rate')),
            'enterprise_tax_rate_u4m': self._clean_rate(cleaned.get('enterprise_tax_rate_u4m')),
            'enterprise_tax_rate_4m_8m': self._clean_rate(cleaned.get('enterprise_tax_rate_4m_8m')),
            'enterprise_tax_rate_o8m': self._clean_rate(cleaned.get('enterprise_tax_rate_o8m')),
            'local_special_tax_rate': self._clean_rate(cleaned.get('local_special_tax_rate')),
            'prefectural_corporate_tax_rate': self._clean_rate(cleaned.get('prefectural_corporate_tax_rate')),
            'municipal_corporate_tax_rate': self._clean_rate(cleaned.get('municipal_corporate_tax_rate')),
        }
        amount_values = {
            'prefectural_equalization_amount': self._clean_numeric(cleaned.get('prefectural_equalization_amount')),
            'municipal_equalization_amount': self._clean_numeric(cleaned.get('municipal_equalization_amount')),
        }

        return self._compute_values(
            fiscal_start,
            fiscal_end,
            period_months,
            months_truncated,
            pre_tax_income,
            rate_values,
            amount_values,
        )

    @staticmethod
    def _format_date(value: Optional[date]) -> str:
        if not isinstance(value, date):
            return ''
        return value.strftime('%Y%m%d')

    @staticmethod
    def _resolve_period_months(
        company: Optional[Company],
        master: Optional[CorporateTaxMaster],
        start: Optional[date] = None,
        end: Optional[date] = None,
    ) -> Optional[int]:
        if start is None and company is not None:
            start = CorporateTaxCalculationService._coerce_date(
                company.accounting_period_start_date,
                company.accounting_period_start,
            )
        if end is None and company is not None:
            end = CorporateTaxCalculationService._coerce_date(
                company.accounting_period_end_date,
                company.accounting_period_end,
            )
        if start and end and end >= start:
            delta = relativedelta(end, start)
            months = delta.years * 12 + delta.months
            if delta.days > 0 or months == 0:
                months += 1
            return max(months, 1)
        if master is not None:
            try:
                return int(master.months_standard)
            except (TypeError, ValueError):
                return None
        return None
        return None

    @staticmethod
    def _resolve_truncated_months(master: Optional[CorporateTaxMaster]):
        if master is None:
            return ''
        try:
            return int(master.months_truncated)
        except (TypeError, ValueError):
            return ''

    @staticmethod
    def _calculate_manual_months(start: Optional[date], end: Optional[date]) -> Tuple[Optional[int], Optional[int]]:
        if not start or not end or end < start:
            return None, None
        delta = relativedelta(end, start)
        base_months = delta.years * 12 + delta.months
        months_ceil = max(base_months, 0)
        if delta.days > 0 or months_ceil == 0:
            months_ceil += 1
        if start.day == 1:
            months_floor = months_ceil
        elif start.year == end.year and start.month == end.month:
            months_floor = 1
        else:
            months_floor = max(months_ceil - 1, 0)
        return months_ceil, months_floor

    def _calculate_period_months(self, start: Optional[date], end: Optional[date]) -> Optional[int]:
        months = self._calculate_manual_months(start, end)
        return months[0]

    @staticmethod
    def _parse_compact_date_text(value: Optional[str]) -> Optional[date]:
        if not value:
            return None
        try:
            return datetime.strptime(value.strip(), "%Y%m%d").date()
        except ValueError:
            return None

    @staticmethod
    def _clean_numeric(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        cleaned = value.replace(',', '').strip()
        return cleaned or None

    @staticmethod
    def _clean_rate(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        cleaned = value.replace('%', '').replace(',', '').strip()
        return cleaned or None

    @staticmethod
    def _coerce_int(value: Any) -> Optional[int]:
        if isinstance(value, int):
            return value
        if isinstance(value, Decimal):
            return int(value)
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            try:
                return int(Decimal(value))
            except (InvalidOperation, ValueError):
                return None
        return None

    @staticmethod
    def _with_rate_default(value: Any, key: str) -> Decimal:
        rate = CorporateTaxCalculationService._decimal(value)
        default = DEFAULT_RATE_VALUES.get(key)
        if rate <= _DECIMAL_ZERO and default is not None:
            return default
        return rate

    @staticmethod
    def _with_amount_default(value: Any, key: str) -> int:
        try:
            amount = int(value)
        except (TypeError, ValueError):
            amount = 0
        default = DEFAULT_AMOUNT_VALUES.get(key)
        if amount <= 0 and default is not None:
            return default
        return amount

    @staticmethod
    def _ceil_thousand(value: Decimal) -> Decimal:
        if value <= _DECIMAL_ZERO:
            return _DECIMAL_ZERO
        quotient = value // _THOUSAND
        remainder = value % _THOUSAND
        if remainder == _DECIMAL_ZERO:
            return quotient * _THOUSAND
        return (quotient + 1) * _THOUSAND

    @staticmethod
    def _floor_thousand(value: Decimal) -> Decimal:
        if value <= _DECIMAL_ZERO:
            return _DECIMAL_ZERO
        return (value // _THOUSAND) * _THOUSAND

    @staticmethod
    def _floor_hundred(value: Decimal) -> Decimal:
        if value <= _DECIMAL_ZERO:
            return _DECIMAL_ZERO
        return (value // _HUNDRED) * _HUNDRED

    @staticmethod
    def _decimal(value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if value in (None, ''):
            return _DECIMAL_ZERO
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError):
            return _DECIMAL_ZERO

    @staticmethod
    def _apply_rate(base: Decimal, rate: Decimal) -> Decimal:
        if base <= _DECIMAL_ZERO or rate <= _DECIMAL_ZERO:
            return _DECIMAL_ZERO
        return (base * rate / _HUNDRED).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

    @staticmethod
    def _to_int(value: Any) -> int:
        if isinstance(value, Decimal):
            return int(value)
        if value in (None, ''):
            return 0
        return int(value)

    @staticmethod
    def _format_rate(rate: Decimal) -> str:
        if rate <= _DECIMAL_ZERO:
            return ''
        quantized = rate.quantize(Decimal('0.01'))
        text = format(quantized, 'f').rstrip('0').rstrip('.')
        return f"{text}%"

    @staticmethod
    def _format_percent(numerator: Decimal, denominator: Decimal) -> str:
        if denominator <= _DECIMAL_ZERO:
            return ''
        percent = (numerator / denominator * _HUNDRED).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
        text = format(percent, 'f').rstrip('0').rstrip('.')
        return f"{text}%"

    @staticmethod
    def _extract_pre_tax_income(accounting_data: Optional[AccountingData]) -> Decimal:
        if not accounting_data:
            return _DECIMAL_ZERO
        payload = accounting_data.data or {}
        if not isinstance(payload, dict):
            return _DECIMAL_ZERO
        pl_section = payload.get('profit_loss_statement')
        if not isinstance(pl_section, dict):
            return _DECIMAL_ZERO
        profit_calc = pl_section.get('利益計算')
        if not isinstance(profit_calc, dict):
            return _DECIMAL_ZERO
        pre_tax_entry = profit_calc.get('税引前当期純利益')
        if isinstance(pre_tax_entry, dict):
            value = pre_tax_entry.get('total')
        else:
            value = pre_tax_entry
        return CorporateTaxCalculationService._decimal(value)
