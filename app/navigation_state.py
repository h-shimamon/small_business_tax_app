from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Set

from flask import session
from flask_login import current_user

from app.navigation_builder import navigation_tree
from app.navigation_models import NavigationNode
from app.navigation_logging import log_navigation_issue as _log_issue
from app.navigation_completion import compute_completed
from app.progress.evaluator import SoAProgressEvaluator


def _soa_children() -> list[NavigationNode]:
    for node in navigation_tree:
        if node.key == 'statement_of_accounts_group':
            return node.children or []
    return []


def _first_soa_child_key() -> Optional[str]:
    children = _soa_children()
    return children[0].key if children else None


@dataclass
class NavigationState:
    items: list[dict]
    skipped_keys: Set[str]
    completed_keys: Set[str]


class NavigationStateMachine:
    def __init__(self, current_page_key: str, *, preset_skipped: Optional[Iterable[str]] = None) -> None:
        self.current_page_key = current_page_key
        self.preset_skipped = set(preset_skipped or [])
        self.session_step_key = 'wizard_completed_steps'

    def compute(self) -> NavigationState:
        company = getattr(current_user, 'company', None)
        user_id = getattr(current_user, 'id', None)

        completed = set(session.get(self.session_step_key, []))
        skipped = set(self.preset_skipped)

        if company is not None:
            skipped |= self._compute_skipped(company.id)
            completed |= self._augment_completed(company.id, user_id)

        items = [
            node.to_dict(self.current_page_key, list(completed), skipped)
            for node in navigation_tree
        ]
        self._prune_filing_group(items)
        return NavigationState(items=items, skipped_keys=skipped, completed_keys=completed)

    def mark_completed(self, step_key: str) -> None:
        completed = session.get(self.session_step_key, [])
        if step_key not in completed:
            completed.append(step_key)
            session[self.session_step_key] = completed

    def unmark_completed(self, step_key: str) -> None:
        completed = session.get(self.session_step_key, [])
        if step_key in completed:
            session[self.session_step_key] = [s for s in completed if s != step_key]

    def _compute_skipped(self, company_id: int) -> Set[str]:
        skipped: Set[str] = set()
        try:
            from app.company.services.soa_summary_service import SoASummaryService
            from app.company.models import AccountingData

            latest = (
                AccountingData.query
                .filter_by(company_id=company_id)
                .order_by(AccountingData.created_at.desc())
                .first()
            )
            if not latest:
                first_key = _first_soa_child_key()
                if first_key:
                    skipped.add(first_key)
                return skipped

            for child in _soa_children():
                page = (child.params or {}).get('page') if getattr(child, 'params', None) else None
                if not page:
                    continue
                total = SoASummaryService.compute_skip_total(company_id, page, accounting_data=latest)
                if total == 0:
                    skipped.add(child.key)
        except Exception as exc:  # pragma: no cover - log only
            _log_issue('state_machine.compute_skipped', error=exc, company_id=company_id)
        return skipped

    def _augment_completed(self, company_id: int, user_id: Optional[int]) -> Set[str]:
        results: Set[str] = set()
        if user_id is None:
            return results
        try:
            results |= compute_completed(company_id, user_id)
            for child in _soa_children():
                page = (child.params or {}).get('page') if getattr(child, 'params', None) else None
                if not page:
                    continue
                if SoAProgressEvaluator.is_completed(company_id, page):
                    results.add(child.key)
        except Exception as exc:  # pragma: no cover
            _log_issue('state_machine.completed', error=exc, company_id=company_id, user_id=user_id)
        return results

    @staticmethod
    def _prune_filing_group(items: list[dict]) -> None:
        is_admin = bool(getattr(current_user, 'is_admin', False))
        if is_admin:
            return
        for parent in items:
            if parent.get('key') == 'filings_group':
                parent['children'] = [
                    child for child in parent.get('children', [])
                    if child.get('key') != 'corporate_tax_calc'
                ]
                break
