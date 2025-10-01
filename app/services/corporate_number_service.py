from __future__ import annotations

from app.integrations.houjinbangou.interface import HojinClient, HojinRecord


class CorporateNumberService:
    def __init__(self, client: HojinClient) -> None:
        self._client = client

    def _normalize_number(self, number: str | None) -> str:
        if not number:
            return ""
        return "".join(ch for ch in number if ch.isdigit())

    def resolve_by_number(self, number: str | None) -> HojinRecord | None:
        num = self._normalize_number(number)
        if not num:
            return None
        return self._client.get_by_number(num)

    def suggest_by_name(self, q: str | None, prefecture: str | None = None) -> list[HojinRecord]:
        query = (q or "").strip()
        if not query:
            return []
        return self._client.search_by_name(query, prefecture=prefecture)
