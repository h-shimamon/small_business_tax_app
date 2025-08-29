from __future__ import annotations

from typing import Optional, List

from app.integrations.houjinbangou.interface import HojinClient, HojinRecord


class CorporateNumberService:
    def __init__(self, client: HojinClient) -> None:
        self._client = client

    def _normalize_number(self, number: Optional[str]) -> str:
        if not number:
            return ""
        return "".join(ch for ch in number if ch.isdigit())

    def resolve_by_number(self, number: Optional[str]) -> Optional[HojinRecord]:
        num = self._normalize_number(number)
        if not num:
            return None
        return self._client.get_by_number(num)

    def suggest_by_name(self, q: Optional[str], prefecture: Optional[str] = None) -> List[HojinRecord]:
        query = (q or "").strip()
        if not query:
            return []
        return self._client.search_by_name(query, prefecture=prefecture)
