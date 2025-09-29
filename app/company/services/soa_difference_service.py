from __future__ import annotations

from typing import Dict, Optional

from flask import g, has_request_context

from app.company.models import AccountingData
from app.company.services.soa_summary_service import SoASummaryService
from app.domain.soa.evaluation import SoAPageEvaluation

class SoADifferenceBatch:
    """Batch computes difference metrics for SoA pages once per request."""

    def __init__(self, company_id: int, accounting_data: Optional[AccountingData] = None) -> None:
        self.company_id = company_id
        self.accounting_data = accounting_data
        self._cache: Dict[str, SoAPageEvaluation] = {}

    def bind_to_request(self) -> None:
        if has_request_context():
            cached = getattr(g, '_soa_difference_batch', None)
            if cached is None or getattr(cached, 'company_id', None) != self.company_id:
                g._soa_difference_batch = self

    def get(self, page: str) -> SoAPageEvaluation:
        if page in self._cache:
            return self._cache[page]
        evaluation = SoASummaryService.evaluate_page(
            self.company_id,
            page,
            accounting_data=self.accounting_data,
        )
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
