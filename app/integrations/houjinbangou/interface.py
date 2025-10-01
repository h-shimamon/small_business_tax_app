from __future__ import annotations

from typing import Protocol, TypedDict


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
    def get_by_number(self, number: str) -> HojinRecord | None:
        ...

    def search_by_name(self, name: str, *, prefecture: str | None = None) -> list[HojinRecord]:
        ...
