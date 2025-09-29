from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Tuple

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_

from app import db
from app.company.models import AccountingData, Company, CorporateTaxMaster
from app.tax_engine import (
    DEFAULT_EQUALIZATION_DEFAULTS,
    DEFAULT_RATE_DEFAULTS,
    EqualizationAmounts,
    TaxInput,
    TaxPeriod,
    TaxRates,
    build_equalization_amounts,
    build_tax_rates,
    calculate_tax,
)


_DECIMAL_ZERO = Decimal("0")

class CorporateTaxCalculationService:
    """Builds the context dictionaries for the corporate tax calculation page."""

    def build(self, company_id: Optional[int] = None) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        company = db.session.get(Company, company_id) if company_id else None
        master = self._resolve_master(company)
        accounting_data = self._latest_accounting_data(company_id) if company_id else None
        return self._compile(company, master, accounting_data)

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
        months_truncated = self._resolve_truncated_months(master)
        pre_tax_income = self._extract_pre_tax_income(accounting_data)

        months_in_period_int = self._coerce_int(period_months)
        if months_in_period_int is None or months_in_period_int <= 0:
            months_in_period_int = self._calculate_period_months(fiscal_start, fiscal_end) or 12
        months_truncated_int = self._coerce_int(months_truncated)
        if months_truncated_int is None or months_truncated_int <= 0:
            months_truncated_int = months_in_period_int

        taxable_income = self._decimal(pre_tax_income)
        if taxable_income <= _DECIMAL_ZERO:
            taxable_income = _DECIMAL_ZERO

        rates = build_tax_rates(master)
        equalization = build_equalization_amounts(master)
        tax_input = self._build_tax_input(
            fiscal_start,
            fiscal_end,
            months_in_period_int,
            months_truncated_int,
            taxable_income,
            rates,
            equalization,
        )
        calculation = calculate_tax(tax_input)
        payload = calculation.to_payload()
        return payload.inputs, payload.results, payload.breakdown

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

        months_in_period_int = self._coerce_int(period_months) or 12
        months_truncated_int = self._coerce_int(months_truncated) or months_in_period_int

        taxable_income = self._decimal(self._clean_numeric(cleaned.get('pre_tax_income')))
        if taxable_income <= _DECIMAL_ZERO:
            taxable_income = _DECIMAL_ZERO

        rates = self._construct_rates_from_values(cleaned)
        equalization = self._construct_equalization_from_values(cleaned)

        tax_input = self._build_tax_input(
            fiscal_start,
            fiscal_end,
            months_in_period_int,
            months_truncated_int,
            taxable_income,
            rates,
            equalization,
        )
        calculation = calculate_tax(tax_input)
        payload = calculation.to_payload()
        return payload.inputs, payload.results, payload.breakdown

    def _build_tax_input(
        self,
        fiscal_start: Optional[date],
        fiscal_end: Optional[date],
        months_in_period: int,
        months_truncated: int,
        taxable_income: Decimal,
        rates: TaxRates,
        equalization: EqualizationAmounts,
    ) -> TaxInput:
        period = TaxPeriod(
            fiscal_start=fiscal_start,
            fiscal_end=fiscal_end,
            months_in_period=max(months_in_period, 1),
            months_truncated=max(months_truncated, 1),
        )
        return TaxInput(
            period=period,
            taxable_income=taxable_income,
            rates=rates,
            equalization=equalization,
        )

    def _construct_rates_from_values(self, values: Dict[str, Any]) -> TaxRates:
        defaults = DEFAULT_RATE_DEFAULTS
        return TaxRates(
            corporate_low=self._decimal_with_default(values.get('corporate_tax_rate_low'), defaults.corporate_low),
            corporate_high=self._decimal_with_default(values.get('corporate_tax_rate_high'), defaults.corporate_high),
            local_corporate=self._decimal_with_default(values.get('local_corporate_tax_rate'), defaults.local_corporate),
            enterprise_low=self._decimal_with_default(values.get('enterprise_tax_rate_u4m'), defaults.enterprise_low),
            enterprise_mid=self._decimal_with_default(values.get('enterprise_tax_rate_4m_8m'), defaults.enterprise_mid),
            enterprise_high=self._decimal_with_default(values.get('enterprise_tax_rate_o8m'), defaults.enterprise_high),
            local_special=self._decimal_with_default(values.get('local_special_tax_rate'), defaults.local_special),
            prefectural_corporate=self._decimal_with_default(values.get('prefectural_corporate_tax_rate'), defaults.prefectural_corporate),
            municipal_corporate=self._decimal_with_default(values.get('municipal_corporate_tax_rate'), defaults.municipal_corporate),
        )

    def _construct_equalization_from_values(self, values: Dict[str, Any]) -> EqualizationAmounts:
        defaults = DEFAULT_EQUALIZATION_DEFAULTS
        return EqualizationAmounts(
            prefectural=self._int_with_default(values.get('prefectural_equalization_amount'), defaults.prefectural),
            municipal=self._int_with_default(values.get('municipal_equalization_amount'), defaults.municipal),
        )

    @staticmethod
    def _int_with_default(value: Any, default: int) -> int:
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return int(value) if value not in (None, '') else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _decimal_with_default(value: Any, default: Decimal) -> Decimal:
        if value in (None, ''):
            return default
        try:
            cleaned = str(value).replace('%', '').replace(',', '').strip()
            if not cleaned:
                return default
            result = Decimal(cleaned)
            return result if result > _DECIMAL_ZERO else default
        except (InvalidOperation, TypeError):
            return default

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

    def _resolve_period_months(
        self,
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
    def _decimal(value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if value in (None, ''):
            return _DECIMAL_ZERO
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError):
            return _DECIMAL_ZERO

    def _calculate_period_months(self, start: Optional[date], end: Optional[date]) -> Optional[int]:
        months = self._calculate_manual_months(start, end)
        return months[0]

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
