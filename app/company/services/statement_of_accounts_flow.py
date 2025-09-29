"""statement_of_accounts ビュー向けの分離ロジック。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from flask import flash, url_for

from app.constants import FLASH_SKIP
from app.company.models import AccountingData
from app.company.services.protocols import StatementOfAccountsServiceProtocol

if TYPE_CHECKING:
    from app.company.services.statement_of_accounts_service import StatementOfAccountsService
from app.navigation import (
    compute_skipped_steps_for_company,
    get_navigation_state,
    mark_step_as_completed,
    unmark_step_as_completed,
)
from app.navigation_helpers import get_soa_child_key, get_next_soa_page
from app.services.app_registry import get_default_pdf_year, get_post_create_cta, get_empty_state
from app.services.soa_registry import SUMMARY_PAGE_MAP, STATEMENT_PAGES_CONFIG
from app.company.services.soa_difference_service import SoADifferenceBatch


@dataclass(frozen=True)
class StatementContext:
    context: dict
    skipped_steps: set[str]


class StatementOfAccountsFlow:
    def __init__(self, company_id: int, accounting_data: Optional[AccountingData] = None) -> None:
        self.company_id = company_id
        self.accounting_data = accounting_data
        from app.company.services.statement_of_accounts_service import StatementOfAccountsService
        self.service: StatementOfAccountsServiceProtocol = StatementOfAccountsService(company_id)
        self._difference_batch = SoADifferenceBatch(company_id, accounting_data=accounting_data)
        self._difference_batch.bind_to_request()

    def compute_skipped(self) -> set[str]:
        return compute_skipped_steps_for_company(self.company_id, accounting_data=self.accounting_data)

    def maybe_redirect_skipped(self, page: str, skipped_steps: set[str]):
        child_key = get_soa_child_key(page)
        if child_key and child_key in skipped_steps:
            next_page, _ = get_next_soa_page(page, skipped_keys=skipped_steps)
            if next_page:
                flash('財務諸表に計上されていない勘定科目は自動でスキップされます。', FLASH_SKIP)
                return url_for('company.statement_of_accounts', page=next_page)
        return None

    def load_items(self, page: str) -> tuple[list, int]:
        items = self.service.list_items(page)
        total = self.service.calculate_total(page, items)
        return items, total

    def compute_pdf_year(self) -> Optional[int]:
        try:
            return self.accounting_data.period_end.year if self.accounting_data and self.accounting_data.period_end else None
        except Exception:
            return None

    def compute_post_create(self, page: str, created_flag: Optional[str], created_id: Optional[str]) -> Optional[dict]:
        if not created_flag:
            return None
        cta_cfg = get_post_create_cta(page)
        config = STATEMENT_PAGES_CONFIG.get(page, {})
        return {
            'title': f"{config.get('title', '')}を登録しました",
            'desc': None,
            'ctas': [
                {
                    'label': cta_cfg.add_label.format(title=config.get('title', '')),
                    'href': url_for('company.add_item', page_key=page),
                    'class': cta_cfg.add_class,
                },
                {
                    'label': cta_cfg.back_label,
                    'href': url_for('company.statement_of_accounts', page=page),
                    'class': cta_cfg.back_class,
                },
            ],
            'created_id': created_id,
        }

    def compute_summaries_and_mark(self, page: str, config: dict) -> tuple[dict, Optional[str]]:
        summaries: dict = {'generic_summary': {'bs_total': 0, 'breakdown_total': 0, 'difference': 0}}
        if page in SUMMARY_PAGE_MAP:
            evaluation = self._difference_batch.get(page)
            diff = evaluation.get('difference', {})
            if page == 'borrowings':
                summaries['borrowings_summary'] = {
                    'bs_total': diff.get('bs_total', 0),
                    'pl_interest_total': diff.get('pl_interest_total', 0),
                    'breakdown_total': diff.get('breakdown_total', 0),
                    'difference': diff.get('difference', 0),
                }
                generic = summaries['borrowings_summary']
                label = 'B/S上の借入金残高'
            else:
                generic = {
                    'bs_total': diff.get('bs_total', 0),
                    'breakdown_total': diff.get('breakdown_total', 0),
                    'difference': diff.get('difference', 0),
                }
                label = f"{'B/S上の' if SUMMARY_PAGE_MAP[page][0] == 'BS' else 'P/L上の'}{config['title']}残高"
                summaries['generic_summary'] = generic
            step_key = 'fixed_assets_soa' if page == 'fixed_assets' else page
            if evaluation.get('is_balanced', False):
                mark_step_as_completed(step_key)
            else:
                unmark_step_as_completed(step_key)
            summaries['generic_summary'] = generic
            summaries['generic_summary_label'] = label
            if page == 'deposits':
                summaries['deposit_summary'] = generic
            elif page == 'notes_receivable':
                summaries['notes_receivable_summary'] = generic
            elif page == 'accounts_receivable':
                summaries['accounts_receivable_summary'] = generic
            return summaries, step_key
        summaries['generic_summary_label'] = config.get('title', '')
        return summaries, None

    def prepare_context(
        self,
        page: str,
        created_flag: Optional[str],
        created_id: Optional[str],
    ) -> StatementContext:
        config = STATEMENT_PAGES_CONFIG.get(page)
        items, total = self.load_items(page)
        skipped = self.compute_skipped()
        redirect_url = self.maybe_redirect_skipped(page, skipped)
        if redirect_url:
            raise RedirectRequired(redirect_url)
        pdf_year = self.compute_pdf_year() or get_default_pdf_year()
        empty_state_cfg = get_empty_state(page)
        post_create = self.compute_post_create(page, created_flag, created_id)
        summaries, step_key = self.compute_summaries_and_mark(page, config)
        next_page, next_name = get_next_soa_page(page, skipped_keys=skipped)
        nav_state = get_navigation_state(page, skipped_steps=skipped)
        context = {
            'page': page,
            'page_title': config['title'],
            'items': items,
            'total': total,
            'navigation_state': nav_state,
            'cta_config': get_post_create_cta(page),
            'pdf_year': pdf_year,
            'empty_state_config': {
                'headline': empty_state_cfg['headline'].format(title=config['title']),
                'description': empty_state_cfg.get('description'),
                'action_label': (empty_state_cfg.get('action_label') or '').format(title=config['title']),
            },
            'post_create': post_create,
            'soa_next_url': url_for('company.statement_of_accounts', page=next_page) if next_page else None,
            'soa_next_name': next_name,
        }
        context.update(summaries)
        return StatementContext(context=context, skipped_steps=skipped)


class RedirectRequired(Exception):
    def __init__(self, target_url: str) -> None:
        super().__init__(target_url)
        self.target_url = target_url
