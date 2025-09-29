from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from typing import Optional, Tuple

from app.company.models import CorporateTaxMaster

from .models import EqualizationAmounts, TaxRates


@dataclass(frozen=True)
class TaxRateDefaults:
    """税率のデフォルト値。"""

    corporate_low: Decimal = Decimal('15.0')
    corporate_high: Decimal = Decimal('23.2')
    local_corporate: Decimal = Decimal('10.3')
    enterprise_low: Decimal = Decimal('3.5')
    enterprise_mid: Decimal = Decimal('5.3')
    enterprise_high: Decimal = Decimal('7.0')
    local_special: Decimal = Decimal('37.0')
    prefectural_corporate: Decimal = Decimal('1.0')
    municipal_corporate: Decimal = Decimal('6.0')


@dataclass(frozen=True)
class EqualizationDefaults:
    """均等割のデフォルト値。"""

    prefectural: int = 20_000
    municipal: int = 50_000


DEFAULT_RATE_DEFAULTS = TaxRateDefaults()
DEFAULT_EQUALIZATION_DEFAULTS = EqualizationDefaults()


def build_tax_rates(master: Optional[CorporateTaxMaster]) -> TaxRates:
    """DBのマスタ行から税率を構築。マスタが無ければデフォルトを返す。"""

    key = _rates_cache_key(master)
    return _build_tax_rates_cached(key)


def build_equalization_amounts(master: Optional[CorporateTaxMaster]) -> EqualizationAmounts:
    """DBのマスタ行から均等割額を構築。"""

    key = _equalization_cache_key(master)
    return _build_equalization_cached(key)


def _rates_cache_key(master: Optional[CorporateTaxMaster]) -> Tuple:
    if master is None:
        return ('default',)
    return (
        'master',
        getattr(master, 'id', None),
        str(master.corporate_tax_rate_u8m),
        str(master.corporate_tax_rate_o8m),
        str(master.local_corporate_tax_rate),
        str(master.enterprise_tax_rate_u4m),
        str(master.enterprise_tax_rate_4m_8m),
        str(master.enterprise_tax_rate_o8m),
        str(master.local_special_tax_rate),
        str(master.prefectural_corporate_tax_rate),
        str(master.municipal_corporate_tax_rate),
    )


@lru_cache(maxsize=64)
def _build_tax_rates_cached(key: Tuple) -> TaxRates:
    defaults = DEFAULT_RATE_DEFAULTS
    if key == ('default',):
        return TaxRates(
            corporate_low=defaults.corporate_low,
            corporate_high=defaults.corporate_high,
            local_corporate=defaults.local_corporate,
            enterprise_low=defaults.enterprise_low,
            enterprise_mid=defaults.enterprise_mid,
            enterprise_high=defaults.enterprise_high,
            local_special=defaults.local_special,
            prefectural_corporate=defaults.prefectural_corporate,
            municipal_corporate=defaults.municipal_corporate,
        )

    (
        _,
        _master_id,
        corporate_low,
        corporate_high,
        local_corporate,
        enterprise_low,
        enterprise_mid,
        enterprise_high,
        local_special,
        prefectural_corporate,
        municipal_corporate,
    ) = key

    return TaxRates(
        corporate_low=Decimal(corporate_low),
        corporate_high=Decimal(corporate_high),
        local_corporate=Decimal(local_corporate),
        enterprise_low=Decimal(enterprise_low),
        enterprise_mid=Decimal(enterprise_mid),
        enterprise_high=Decimal(enterprise_high),
        local_special=Decimal(local_special),
        prefectural_corporate=Decimal(prefectural_corporate),
        municipal_corporate=Decimal(municipal_corporate),
    )


def _equalization_cache_key(master: Optional[CorporateTaxMaster]) -> Tuple:
    if master is None:
        return ('default',)
    return (
        'master',
        getattr(master, 'id', None),
        int(getattr(master, 'prefectural_equalization_amount', DEFAULT_EQUALIZATION_DEFAULTS.prefectural) or 0),
        int(getattr(master, 'municipal_equalization_amount', DEFAULT_EQUALIZATION_DEFAULTS.municipal) or 0),
    )


@lru_cache(maxsize=64)
def _build_equalization_cached(key: Tuple) -> EqualizationAmounts:
    defaults = DEFAULT_EQUALIZATION_DEFAULTS
    if key == ('default',):
        return EqualizationAmounts(
            prefectural=defaults.prefectural,
            municipal=defaults.municipal,
        )

    _, _master_id, prefectural, municipal = key
    prefectural_value = int(prefectural) if prefectural else defaults.prefectural
    municipal_value = int(municipal) if municipal else defaults.municipal
    return EqualizationAmounts(
        prefectural=prefectural_value,
        municipal=municipal_value,
    )
