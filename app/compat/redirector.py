from __future__ import annotations

from datetime import date
from typing import Optional

from flask import Blueprint, redirect, url_for, request, current_app, abort, flash
from flask_login import current_user

from app.messages import MSG_SKIP_AUTOSKIP

bp_redirector = Blueprint("redirector", __name__)


def _compat_enabled() -> bool:
    cfg = current_app.config
    if not cfg.get("COMPAT_LEGACY_ENABLED", True):
        return False
    deadline: Optional[str] = cfg.get("COMPAT_DEADLINE")
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


@bp_redirector.route("/statement_of_accounts")
def legacy_statement_of_accounts_root():
    """Old root-level URL with optional page query → new SoA route.
    Adds forward-skip logic to keep legacy behavior consistent with tests.
    """
    if not _compat_enabled():
        abort(404)

    page = request.args.get("page", "deposits")

    # forward-skip logic mirrors app/__init__.py legacy handler previously used
    try:
        from app.navigation_builder import navigation_tree
        from app.navigation import compute_skipped_steps_for_company
        company = getattr(current_user, "company", None)
        skipped = compute_skipped_steps_for_company(company.id) if company else set()
        if skipped:
            soa_children = []
            for node in navigation_tree:
                if node.key == "statement_of_accounts_group":
                    soa_children = node.children
                    break
            current_idx = None
            for idx, child in enumerate(soa_children):
                if (child.params or {}).get("page") == page:
                    current_idx = idx
                    break
            if current_idx is not None and (soa_children[current_idx].key in skipped):
                for nxt in soa_children[current_idx + 1 :]:
                    if nxt.key not in skipped:
                        page = (nxt.params or {}).get("page", page)
                        try:
                            flash(MSG_SKIP_AUTOSKIP, "skip")
                        except Exception:
                            pass
                        break
    except Exception:
        pass

    return redirect(url_for("company.statement_of_accounts", page=page), code=302)
