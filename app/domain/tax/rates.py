from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

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
    """DBのマスタ行から税率を構築。マスタが無ければデフォルト。"""

    defaults = DEFAULT_RATE_DEFAULTS
    if master is None:
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

    return TaxRates(
        corporate_low=Decimal(master.corporate_tax_rate_u8m),
        corporate_high=Decimal(master.corporate_tax_rate_o8m),
        local_corporate=Decimal(master.local_corporate_tax_rate),
        enterprise_low=Decimal(master.enterprise_tax_rate_u4m),
        enterprise_mid=Decimal(master.enterprise_tax_rate_4m_8m),
        enterprise_high=Decimal(master.enterprise_tax_rate_o8m),
        local_special=Decimal(master.local_special_tax_rate),
        prefectural_corporate=Decimal(master.prefectural_corporate_tax_rate),
        municipal_corporate=Decimal(master.municipal_corporate_tax_rate),
    )


def build_equalization_amounts(master: Optional[CorporateTaxMaster]) -> EqualizationAmounts:
    """DBのマスタ行から均等割額を構築。"""

    defaults = DEFAULT_EQUALIZATION_DEFAULTS
    if master is None:
        return EqualizationAmounts(
            prefectural=defaults.prefectural,
            municipal=defaults.municipal,
        )

    return EqualizationAmounts(
        prefectural=int(master.prefectural_equalization_amount or defaults.prefectural),
        municipal=int(master.municipal_equalization_amount or defaults.municipal),
    )
