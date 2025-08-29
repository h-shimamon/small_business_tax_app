from __future__ import annotations

from typing import TypedDict


class DifferenceResult(TypedDict):
    difference: int
    source_total: int
    breakdown_total: int
