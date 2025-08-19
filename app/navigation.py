# app/navigation.py
from flask import session
from flask_login import current_user
from .navigation_builder import navigation_tree

def compute_skipped_steps_for_company(company_id, accounting_data=None):
    """Compute skipped steps (SoA pages with source total == 0) for the given company.
    Optionally accepts pre-fetched accounting_data to avoid duplicate queries.
    Safe no-op if company or accounting data is missing.
    """
    skipped = set()
    try:
        from app.company.models import AccountingData
        from app.company.services.soa_summary_service import SoASummaryService
        if accounting_data is None:
            accounting_data = (
                AccountingData.query
                .filter_by(company_id=company_id)
                .order_by(AccountingData.created_at.desc())
                .first()
            )
        if not accounting_data:
            return skipped
        soa_children = []
        for node in navigation_tree:
            if node.key == 'statement_of_accounts_group':
                soa_children = node.children
                break
        for child in soa_children:
            child_page = (child.params or {}).get('page')
            if child_page:
                total = SoASummaryService.compute_skip_total(company_id, child_page, accounting_data=accounting_data)
                if total == 0:
                    skipped.add(child.key)
    except Exception:
        # ここでは安全側に倒す（スキップなしとして扱う）。詳細は呼び出し元でログ済みのはず。
        return set()
    return skipped

def get_navigation_state(current_page_key, skipped_steps=None):
    """
    現在のページキーに基づき、ナビゲーション全体のUI状態を計算して返す。
    計算ロジックはNavigationNodeクラスに委譲する。
    """
    completed_steps = session.get('wizard_completed_steps', [])
    # skipped_steps が未指定の場合は、認証済みユーザーの会社に基づいてSoAスキップを自動計算
    if skipped_steps is None:
        try:
            company = getattr(current_user, 'company', None)
            skipped_steps = compute_skipped_steps_for_company(company.id) if company else set()
        except Exception:
            skipped_steps = set()
    else:
        skipped_steps = skipped_steps or set()
    
    nav_state = [
        node.to_dict(current_page_key, completed_steps, skipped_steps)
        for node in navigation_tree
    ]
    
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
