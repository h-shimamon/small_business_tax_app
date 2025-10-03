# app/navigation.py
from __future__ import annotations

from app.navigation_logging import log_navigation_issue
from app.navigation_state import NavigationStateMachine


def get_navigation_state(current_page_key, skipped_steps=None):
    machine = NavigationStateMachine(current_page_key, preset_skipped=skipped_steps)
    return machine.compute().items


def mark_step_as_completed(step_key):
    machine = NavigationStateMachine(step_key)
    machine.mark_completed(step_key)


def unmark_step_as_completed(step_key):
    machine = NavigationStateMachine(step_key)
    machine.unmark_completed(step_key)


def compute_skipped_steps_for_company(company_id, accounting_data=None):
    try:
        machine = NavigationStateMachine(current_page_key='')
        return machine._compute_skipped(company_id)
    except Exception as exc:  # pragma: no cover - logging only
        log_navigation_issue('compute_skipped_steps', error=exc, company_id=company_id)
        return set()