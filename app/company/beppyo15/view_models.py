from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .constants import Beppyo15FieldDefinition


@dataclass(frozen=True)
class Beppyo15ItemViewModel:
    id: int
    subject: str
    expense_amount: int
    deductible_amount: int
    net_amount: int
    hospitality_amount: int
    remarks: str | None = None


@dataclass(frozen=True)
class Beppyo15SummaryViewModel:
    expense_total: int
    deductible_total: int
    net_total: int
    hospitality_total: int
    spending_cross: int
    hospitality_deduction: int
    small_corp_limit: int
    deductible_limit: int
    non_deductible_amount: int


@dataclass(frozen=True)
class Beppyo15PageViewModel:
    items: List[Beppyo15ItemViewModel]
    summary: Beppyo15SummaryViewModel
    field_definitions: List[Beppyo15FieldDefinition]
