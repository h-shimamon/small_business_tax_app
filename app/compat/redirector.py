from __future__ import annotations

from datetime import date
from flask import Blueprint, abort, current_app, flash, redirect, request, url_for
from flask_login import current_user

from app.messages import MSG_SKIP_AUTOSKIP

bp_redirector = Blueprint("redirector", __name__)


def _compat_enabled() -> bool:
    cfg = current_app.config
    if not cfg.get("COMPAT_LEGACY_ENABLED", True):
        return False
    deadline: str | None = cfg.get("COMPAT_DEADLINE")
    if deadline:
        try:
            y, m, d = map(int, deadline.split("-"))
            return date.today() <= date(y, m, d)
        except Exception:
            # フォーマット不正時は許容（安全側）
            return True
    return True


@bp_redirector.route("/statement/<page_key>/add")
def legacy_add_item_root(page_key: str):
    """Old root-level URL → new generic add-item view under company_bp.
    Authentication is enforced by the destination blueprint.
    """
    if not _compat_enabled():
        abort(404)
    return redirect(url_for("company.add_item", page_key=page_key), code=302)




def _get_company():
    try:
        return getattr(current_user, "company", None)
    except Exception:
        return None


def _load_soa_children():
    from app.navigation_builder import navigation_tree

    for node in navigation_tree:
        if node.key == "statement_of_accounts_group":
            return node.children or []
    return []


def _safe_flash_skip_message():
    try:
        flash(MSG_SKIP_AUTOSKIP, "skip")
    except Exception:
        pass


def _next_unskipped_child(children, start_index, skipped):
    for child in children[start_index:]:
        if child.key not in skipped:
            return child
    return None


def _resolve_forward_page(page: str) -> str:
    try:
        from app.navigation import compute_skipped_steps_for_company

        company = _get_company()
        skipped = compute_skipped_steps_for_company(company.id) if company else set()
        if not skipped:
            return page
        soa_children = _load_soa_children()
        current_idx = None
        for idx, child in enumerate(soa_children):
            if (child.params or {}).get("page") == page:
                current_idx = idx
                break
        if current_idx is None:
            return page
        if soa_children[current_idx].key not in skipped:
            return page
        next_child = _next_unskipped_child(soa_children, current_idx + 1, skipped)
        if not next_child:
            return page
        _safe_flash_skip_message()
        return (next_child.params or {}).get("page", page)
    except Exception:
        return page

@bp_redirector.route("/statement_of_accounts")

def legacy_statement_of_accounts_root():
    """Old root-level URL with optional page query → new SoA route."""
    if not _compat_enabled():
        abort(404)

    requested_page = request.args.get("page", "deposits")
    target_page = _resolve_forward_page(requested_page)

    return redirect(url_for("company.statement_of_accounts", page=target_page), code=302)
