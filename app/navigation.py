# app/navigation.py
from flask import current_app, session
from flask_login import current_user

from app.navigation_completion import compute_completed
from app.progress.evaluator import SoAProgressEvaluator

from .navigation_builder import navigation_tree


def _log_navigation_issue(event: str, **details) -> None:
    """Log navigation-related failures without breaking UX."""
    try:
        safe_details = {key: str(value) for key, value in details.items()}
        current_app.logger.warning("navigation.%s", event, extra={"navigation_error": safe_details})
    except Exception:
        pass


def _fetch_latest_accounting_data(company_id):
    from app.company.models import AccountingData

    return (
        AccountingData.query
        .filter_by(company_id=company_id)
        .order_by(AccountingData.created_at.desc())
        .first()
    )


def _get_soa_children():
    for node in navigation_tree:
        if node.key == 'statement_of_accounts_group':
            return node.children or []
    return []


def _first_soa_child_key():
    children = _get_soa_children()
    if not children:
        return None
    return children[0].key


def _resolve_company_and_user():
    try:
        company = getattr(current_user, 'company', None)
        user_id = getattr(current_user, 'id', None)
        return company, user_id
    except Exception as exc:
        _log_navigation_issue('resolve_current_user', error=exc)
        return None, None


def _determine_skipped_steps(company, preset):
    if preset is not None:
        return preset or set()
    if not company:
        return set()
    try:
        return compute_skipped_steps_for_company(company.id)
    except Exception as exc:
        _log_navigation_issue('get_navigation_state.skipped', error=exc, company_id=getattr(company, 'id', None))
        return set()


def _augment_completed_steps(company, user_id, base_completed: set[str]) -> set[str]:
    if not company or user_id is None:
        return base_completed
    try:
        return base_completed | compute_completed(company.id, user_id)
    except Exception as exc:
        _log_navigation_issue('get_navigation_state.completed', error=exc, company_id=getattr(company, 'id', None), user_id=user_id)
        return base_completed


def _append_progress_completion(company, completed_steps: set[str]) -> set[str]:
    if not company:
        return completed_steps
    try:
        for child in _get_soa_children():
            page = (child.params or {}).get('page') if child and getattr(child, 'params', None) else None
            if not page:
                continue
            try:
                if SoAProgressEvaluator.is_completed(company.id, page):
                    completed_steps.add(child.key)
            except Exception as exc:
                _log_navigation_issue('get_navigation_state.progress_check', error=exc, company_id=getattr(company, 'id', None), page=page)
    except Exception as exc:
        _log_navigation_issue('get_navigation_state.progress_loop', error=exc, company_id=getattr(company, 'id', None))
    return completed_steps


def _prune_filing_group(nav_state: list[dict], is_admin: bool) -> None:
    if is_admin:
        return
    for parent in nav_state:
        if parent.get('key') == 'filings_group':
            parent['children'] = [
                child for child in parent.get('children', [])
                if child.get('key') != 'corporate_tax_calc'
            ]
            break

def compute_skipped_steps_for_company(company_id, accounting_data=None):
    """Compute skipped steps (SoA pages with source total == 0) for the given company."""
    skipped: set[str] = set()
    try:
        from app.company.services.soa_summary_service import SoASummaryService

        accounting = accounting_data or _fetch_latest_accounting_data(company_id)
        if not accounting:
            first_key = _first_soa_child_key()
            if first_key:
                skipped.add(first_key)
            return skipped

        for child in _get_soa_children():
            child_page = (child.params or {}).get('page') if child and getattr(child, 'params', None) else None
            if not child_page:
                continue
            total = SoASummaryService.compute_skip_total(company_id, child_page, accounting_data=accounting)
            if total == 0:
                skipped.add(child.key)
    except Exception as exc:
        _log_navigation_issue('compute_skipped_steps', error=exc, company_id=company_id)
        return set()
    return skipped



def get_navigation_state(current_page_key, skipped_steps=None):
    """現在のページキーに基づき、ナビゲーション全体のUI状態を計算して返す。"""
    completed_steps = set(session.get('wizard_completed_steps', []))

    company, user_id = _resolve_company_and_user()
    effective_skipped = _determine_skipped_steps(company, skipped_steps)
    completed_steps = _augment_completed_steps(company, user_id, completed_steps)
    completed_steps = _append_progress_completion(company, completed_steps)

    nav_state = [
        node.to_dict(current_page_key, list(completed_steps), effective_skipped)
        for node in navigation_tree
    ]

    is_admin = bool(getattr(current_user, 'is_admin', False))
    _prune_filing_group(nav_state, is_admin)

    return nav_state

def mark_step_as_completed(step_key):
    """
    指定されたステップを完了済みとしてセッションに記録する。
    """
    completed_steps = session.get('wizard_completed_steps', [])
    if step_key not in completed_steps:
        completed_steps.append(step_key)
        session['wizard_completed_steps'] = completed_steps

def unmark_step_as_completed(step_key):
    """
    指定されたステップの完了状態を解除する（存在する場合のみ削除）。
    """
    completed_steps = session.get('wizard_completed_steps', [])
    if step_key in completed_steps:
        completed_steps = [s for s in completed_steps if s != step_key]
        session['wizard_completed_steps'] = completed_steps
