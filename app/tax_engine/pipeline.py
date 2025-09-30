from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Optional

from .engine import calculate_tax
from .models import TaxCalculation, TaxInput
from .rates import build_equalization_amounts, build_tax_rates


@dataclass
class TaxComputationContext:
    """税計算パイプラインへの入力コンテキスト。"""

    tax_input: TaxInput


class TaxComputationPipeline:
    """会計データから税額を算出するための薄いパイプライン。"""

    def __init__(self, default_master_resolver: Callable[[], Optional[object]]) -> None:
        if not callable(default_master_resolver):
            raise ValueError('default_master_resolver must be callable')
        self._default_master_resolver = default_master_resolver

    def build_tax_input(
        self,
        *,
        taxable_income: Decimal,
        period,
        master,
    ) -> TaxInput:
        rates = build_tax_rates(master)
        equalization = build_equalization_amounts(master)
        return TaxInput(period=period, taxable_income=taxable_income, rates=rates, equalization=equalization)

    def compute(
        self,
        *,
        taxable_income: Decimal,
        period,
        master=None,
    ) -> TaxCalculation:
        resolved_master = master if master is not None else self._default_master_resolver()
        if resolved_master is None:
            raise ValueError('Corporate tax master could not be resolved')
        tax_input = self.build_tax_input(taxable_income=taxable_income, period=period, master=resolved_master)
        return calculate_tax(tax_input)
