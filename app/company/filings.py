from __future__ import annotations

from flask import render_template, request, abort, url_for, current_app

from app.company import company_bp
from .auth import company_required
from app.navigation import get_navigation_state
from app.services.app_registry import get_default_pdf_year, get_post_create_cta, get_empty_state
from app.company.services.filings_service import FilingsService
from app.company.services.protocols import FilingsServiceProtocol

filings_service: FilingsServiceProtocol = FilingsService()


def _build_filings_context(page: str):
    title = filings_service.get_title(page)
    if not title:
        return None
    preview_pdf = filings_service.get_preview_pdf(page)
    has_preview = bool(preview_pdf)
    preview_src = url_for('company.filings_preview', page=page) if has_preview else None

    bs_data = None
    pl_data = None
    try:
        from flask_login import current_user
        from app.company.models import AccountingData
        if getattr(current_user, 'is_authenticated', False) and getattr(current_user, 'company', None):
            accounting_data = (
                AccountingData.query
                .filter_by(company_id=current_user.company.id)
                .order_by(AccountingData.created_at.desc())
                .first()
            )
            if accounting_data and accounting_data.data:
                payload = accounting_data.data if isinstance(accounting_data.data, dict) else {}
                bs_data = payload.get('balance_sheet', {})
                pl_data = payload.get('profit_loss_statement', {})
    except Exception:
        bs_data = None
        pl_data = None

    empty_cfg = get_empty_state(page)
    return {
        'page': page,
        'page_title': title,
        'items': [],
        'navigation_state': get_navigation_state(page),
        'generic_summary': {'bs_total': 0, 'breakdown_total': 0, 'difference': 0},
        'soa_next_url': None,
        'soa_next_name': None,
        'pdf_year': get_default_pdf_year(),
        'has_preview': has_preview,
        'preview_src': preview_src,
        'bs_data': bs_data,
        'pl_data': pl_data,
        'cta_config': get_post_create_cta(page),
        'empty_state_config': {
            'headline': empty_cfg['headline'].format(title=title),
            'description': empty_cfg.get('description'),
            'action_label': (empty_cfg.get('action_label') or '').format(title=title),
        },
    }


@company_bp.route('/filings')
@company_required
def filings(company):
    page = request.args.get('page', 'beppyo_2')
    context = _build_filings_context(page)
    if not context:
        abort(404)
    template_path = filings_service.get_template(page)
    if template_path:
        return render_template(template_path, **context)
    return render_template('company/statement_of_accounts.html', **context)


@company_bp.get('/filings/preview')
@company_required
def filings_preview(company):
    from flask import send_file
    import os as _os

    page = request.args.get('page', '').strip()
    pdf_rel = filings_service.get_preview_pdf(page)
    if not pdf_rel:
        abort(404)

    try:
        repo_root = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..'))
        pdf_path = _os.path.join(repo_root, *pdf_rel.split('/'))
        if not _os.path.exists(pdf_path):
            abort(404)
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=False,
        )
    except Exception:
        abort(404)
