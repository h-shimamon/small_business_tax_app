from __future__ import annotations

from typing import Optional

from app.types import DifferenceResult


class SoAProgressEvaluator:
    """
    Read-only evaluator for Statement of Accounts (SoA) completion metrics.
    - No side effects here. Purely computes difference/source/breakdown totals.
    - State transitions (mark/unmark) will be handled by callers (e.g., POST success or background recompute)
      in subsequent PRs.
    """

    @staticmethod
    def compute_difference(company_id: int, page: str) -> DifferenceResult:
        """
        Returns normalized difference result for a SoA page.
        {'difference': int, 'source_total': int, 'breakdown_total': int}
        """
        # Lazy imports to avoid cycles and keep import cost low for tests
        from app.company.services.soa_summary_service import SoASummaryService
        from app.company.soa_config import STATEMENT_PAGES_CONFIG

        cfg = STATEMENT_PAGES_CONFIG.get(page) or {}
        model = cfg.get('model')
        total_field = cfg.get('total_field', 'amount')

        # Source (dict) → normalized totals
        source_dict = SoASummaryService.compute_source_total(company_id, page)
        source_total = int(source_dict.get('source_total', 0) or 0)

        # Breakdown total via existing service (page-aware)
        breakdown_total = int(
            SoASummaryService.compute_breakdown_total(company_id, page, model, total_field) or 0
        )

        return {
            'difference': source_total - breakdown_total,
            'source_total': source_total,
            'breakdown_total': breakdown_total,
        }

    @staticmethod
    def is_completed(company_id: int, page: str) -> bool:
        res = SoAProgressEvaluator.compute_difference(company_id, page)
        return res['difference'] == 0
