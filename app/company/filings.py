# app/company/filings.py
from __future__ import annotations

from flask import render_template, request, abort, url_for, current_app

from app.company import company_bp
from .auth import company_required
from app.navigation import get_navigation_state
from app.company.filings_registry import get_title, get_template, get_preview_pdf


def _build_filings_context(page: str):
    title = get_title(page)
    if not title:
        return None
    has_preview = bool(get_preview_pdf(page))
    preview_src = url_for('company.filings_preview', page=page) if has_preview else None

    # Try to fetch latest accounting data for B/S if available
    bs_data = None
    try:
        from flask_login import current_user
        from app.company.models import AccountingData
        if getattr(current_user, 'is_authenticated', False) and getattr(current_user, 'company', None):
            accounting_data = AccountingData.query.filter_by(
                company_id=current_user.company.id
            ).order_by(AccountingData.created_at.desc()).first()
            if accounting_data and accounting_data.data:
                bs_data = accounting_data.data.get('balance_sheet', {})
    except Exception:
        # Fail closed: do not break filings page if data is missing
        bs_data = None

    return {
        'page': page,
        'page_title': title,
        'items': [],
        'navigation_state': get_navigation_state(page),
        'generic_summary': {'bs_total': 0, 'breakdown_total': 0, 'difference': 0},
        'soa_next_url': None,
        'soa_next_name': None,
        'pdf_year': '2025',
        'has_preview': has_preview,
        'preview_src': preview_src,
        'bs_data': bs_data,
    }


@company_bp.route('/filings')
@company_required
def filings(company):
    """申告書グループの各ページ。
    テンプレート/タイトルは登録表から参照し、専用テンプレートがなければ
    既存の statement_of_accounts.html をフォールバックとして使用する。
    UI構造やコンテキストの形は従来どおり維持する。
    """
    page = request.args.get('page', 'beppyo_2')
    context = _build_filings_context(page)
    if not context:
        abort(404)
    template_path = get_template(page)
    if template_path:
        return render_template(template_path, **context)
    return render_template('company/statement_of_accounts.html', **context)


@company_bp.get('/filings/preview')
@company_required
def filings_preview(company):
    """登録表に基づくPDFプレビュー（読み取り専用）。
    対応エントリが無い場合は 404。
    """
    from flask import send_file
    import os as _os

    page = request.args.get('page', '').strip()
    pdf_rel = get_preview_pdf(page)
    if not pdf_rel:
        abort(404)

    try:
        # Resolve from project root (one level above app root)
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
