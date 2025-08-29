from __future__ import annotations

from typing import TypedDict, Protocol, Optional, List


class HojinRecord(TypedDict, total=False):
    corporate_number: str
    name: str
    name_kana: str
    prefecture: str
    city: str
    street: str
    postal_code: str
    en_name: str
    latest: bool
    excluded: bool


class HojinClient(Protocol):
    def get_by_number(self, number: str) -> Optional[HojinRecord]:
        ...

    def search_by_name(self, name: str, *, prefecture: Optional[str] = None) -> List[HojinRecord]:
        ...
