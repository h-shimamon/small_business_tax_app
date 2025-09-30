from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class SoAPageEvaluation:
    """Statement of Accounts ページの計算結果スナップショット。"""

    difference: Dict[str, int]
    skip_total: int
    is_balanced: bool
    should_skip: bool

    def as_dict(self) -> Dict[str, object]:
        return {
            'difference': self.difference,
            'skip_total': self.skip_total,
            'is_balanced': self.is_balanced,
            'should_skip': self.should_skip,
        }
