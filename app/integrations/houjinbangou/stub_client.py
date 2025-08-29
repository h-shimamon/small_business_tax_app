from __future__ import annotations

from typing import Dict, List, Optional

from .interface import HojinClient, HojinRecord


class StubHojinClient(HojinClient):
    """
    開発用のインメモリ・スタブ。HTTPなどの外部通信は行わない。
    """

    _FIXTURES: Dict[str, HojinRecord] = {
        "0000000000000": {
            "corporate_number": "0000000000000",
            "name": "サンプル株式会社",
            "name_kana": "サンプルカブシキガイシャ",
            "prefecture": "東京都",
            "city": "千代田区",
            "street": "丸の内1-1-1",
            "postal_code": "1000001",
            "en_name": "Sample Co., Ltd.",
            "latest": True,
            "excluded": False,
        },
        "1234567890123": {
            "corporate_number": "1234567890123",
            "name": "例示合同会社",
            "name_kana": "レイジゴウドウガイシャ",
            "prefecture": "大阪府",
            "city": "大阪市北区",
            "street": "梅田1-2-3",
            "postal_code": "5300001",
            "latest": True,
            "excluded": False,
        },
        "7777777777777": {
            "corporate_number": "7777777777777",
            "name": "テスト商事株式会社",
            "prefecture": "愛知県",
            "city": "名古屋市中村区",
            "street": "名駅1-1-4",
            "postal_code": "4500002",
            "latest": True,
            "excluded": False,
        },
    }

    def _norm(self, s: str) -> str:
        return "".join(ch for ch in (s or "") if ch.isalnum())

    def get_by_number(self, number: str) -> Optional[HojinRecord]:
        num = self._norm(number)
        return self._FIXTURES.get(num)

    def search_by_name(self, name: str, *, prefecture: Optional[str] = None) -> List[HojinRecord]:
        q = (name or "").strip()
        if not q:
            return []
        pref = (prefecture or "").strip()
        results: List[HojinRecord] = []
        for rec in self._FIXTURES.values():
            if q in rec.get("name", "") or q in rec.get("name_kana", ""):
                if pref and pref != rec.get("prefecture"):
                    continue
                results.append(rec)
        return results
