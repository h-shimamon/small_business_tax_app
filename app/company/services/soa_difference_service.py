from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from flask import g, has_request_context

from app.company.models import AccountingData
from app.company.services.soa_summary_service import SoASummaryService
from app.services.soa_registry import STATEMENT_PAGES_CONFIG


@dataclass(frozen=True)
class PageDifference:
    difference: Dict[str, int]
    step_key: str


class SoADifferenceBatch:
    """Batch computes difference metrics for SoA pages once per request."""

    def __init__(self, company_id: int, accounting_data: Optional[AccountingData] = None) -> None:
        self.company_id = company_id
        self.accounting_data = accounting_data
        self._cache: Dict[str, Dict[str, int]] = {}

    def bind_to_request(self) -> None:
        if has_request_context():
            cached = getattr(g, '_soa_difference_batch', None)
            if cached is None or getattr(cached, 'company_id', None) != self.company_id:
                g._soa_difference_batch = self

    def get(self, page: str) -> Dict[str, int]:
        if page in self._cache:
            return self._cache[page]
        config = STATEMENT_PAGES_CONFIG.get(page, {})
        model = config.get('model')
        total_field = config.get('total_field', 'amount')
        diff = SoASummaryService.compute_difference(
            self.company_id,
            page,
            model,
            total_field,
            accounting_data=self.accounting_data,
        )
        self._cache[page] = diff
        return diff

    @staticmethod
    def current(company_id: int) -> Optional['SoADifferenceBatch']:
        if not has_request_context():
            return None
        batch = getattr(g, '_soa_difference_batch', None)
        if batch and getattr(batch, 'company_id', None) == company_id:
            return batch
        return None
