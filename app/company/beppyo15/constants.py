from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Beppyo15FieldDefinition:
    key: str
    label: str
    placeholder: str | None = None
    help_text: str | None = None


BEPPYO15_FIELD_DEFINITIONS: List[Beppyo15FieldDefinition] = [
    Beppyo15FieldDefinition('subject', '科目', '例：交際費'),
    Beppyo15FieldDefinition('expense_amount', '支出額', '例：500000'),
    Beppyo15FieldDefinition('deductible_amount', '交際費等の額から控除される費用の額', '例：100000'),
    Beppyo15FieldDefinition('net_amount', '差引交際費等の額(A)'),
    Beppyo15FieldDefinition('hospitality_amount', '(A)のうち接待飲食費の額', '例：200000'),
]
