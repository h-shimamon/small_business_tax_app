from __future__ import annotations

from typing import Any, Dict, Optional

from flask import g, has_request_context

from app.company.models import AccountingData
from app.company.services.soa_summary_service import SoASummaryService
from app.services.soa_registry import STATEMENT_PAGES_CONFIG

class SoADifferenceBatch:
    """Batch computes difference metrics for SoA pages once per request."""

    def __init__(self, company_id: int, accounting_data: Optional[AccountingData] = None) -> None:
        self.company_id = company_id
        self.accounting_data = accounting_data
        self._cache: Dict[str, Dict[str, Any]] = {}

    def bind_to_request(self) -> None:
        if has_request_context():
            cached = getattr(g, '_soa_difference_batch', None)
            if cached is None or getattr(cached, 'company_id', None) != self.company_id:
                g._soa_difference_batch = self

    def get(self, page: str) -> Dict[str, Any]:
        if page in self._cache:
            return self._cache[page]
        evaluation = SoASummaryService.evaluate_page(
            self.company_id,
            page,
            accounting_data=self.accounting_data,
        )
        config = STATEMENT_PAGES_CONFIG.get(page, {})
        evaluation.setdefault('model', config.get('model'))
        evaluation.setdefault('total_field', config.get('total_field'))
        self._cache[page] = evaluation
        return evaluation

    @staticmethod
    def current(company_id: int) -> Optional['SoADifferenceBatch']:
        if not has_request_context():
            return None
        batch = getattr(g, '_soa_difference_batch', None)
        if batch and getattr(batch, 'company_id', None) == company_id:
            return batch
        return None
