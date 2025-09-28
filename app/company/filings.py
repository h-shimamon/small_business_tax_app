from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple

from dateutil.relativedelta import relativedelta
from flask import render_template, request, abort, url_for, current_app, redirect, flash
from flask_login import current_user

from app.company import company_bp
from .auth import company_required
from app.navigation import get_navigation_state
from app.services.app_registry import get_default_pdf_year, get_post_create_cta, get_empty_state
from app.company.services.filings_service import FilingsService
from app.company.services.protocols import FilingsServiceProtocol
from app.company.services.corporate_tax_service import CorporateTaxCalculationService
from app.company.beppyo15 import Beppyo15Service
from app.company.beppyo15.constants import BEPPYO15_FIELD_DEFINITIONS
from app.company.forms import Beppyo15BreakdownForm

filings_service: FilingsServiceProtocol = FilingsService()
corporate_tax_service = CorporateTaxCalculationService()

@company_bp.app_template_filter('format_number')
def format_number(value):
    if value in (None, ''):
        return ''
    text = str(value)
    stripped = text.replace(',', '').strip()
    if not stripped:
        return ''
    try:
        number = Decimal(stripped)
    except (InvalidOperation, TypeError):
        return text
    if number == number.to_integral():
        return f"{int(number):,}"
    formatted = format(number, ',f').rstrip('0').rstrip('.')
    return formatted


def _parse_compact_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%Y%m%d").date()
    except (ValueError, AttributeError):
        return None


def _compute_manual_period(start_text: Optional[str], end_text: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    start_date = _parse_compact_date(start_text)
    end_date = _parse_compact_date(end_text)
    if not start_date or not end_date or end_date < start_date:
        return None, None
    delta = relativedelta(end_date, start_date)
    base_months = delta.years * 12 + delta.months
    months_ceil = max(base_months, 0)
    if delta.days > 0 or months_ceil == 0:
        months_ceil += 1
    if start_date.day == 1:
        months_floor = months_ceil
    elif start_date.year == end_date.year and start_date.month == end_date.month:
        months_floor = 1
    else:
        months_floor = max(months_ceil - 1, 0)
    return months_ceil, months_floor


def _get_capital_stock_amount(bs_data) -> int:
    """Extract capital stock amount from the balance sheet payload."""
    try:
        if not isinstance(bs_data, dict):
            return 0
        equity = bs_data.get('純資産')
        if not isinstance(equity, dict):
            return 0
        shareholders = equity.get('株主資本')
        if not isinstance(shareholders, dict):
            return 0
        items = shareholders.get('items') or []
        for item in items:
            if isinstance(item, dict):
                name = item.get('name')
                amount = item.get('amount')
            else:
                name = getattr(item, 'name', None)
                amount = getattr(item, 'amount', None)
            if name == '資本金':
                try:
                    return int(Decimal(str(amount))) if amount is not None else 0
                except (InvalidOperation, TypeError, ValueError):
                    return 0
    except Exception:
        return 0
    return 0


def _build_filings_context(page: str):
    title = filings_service.get_title(page)
    if not title:
        return None
    preview_pdf = filings_service.get_preview_pdf(page)
    has_preview = bool(preview_pdf)
    preview_src = url_for('company.filings_preview', page=page) if has_preview else None

    accounting_data = None
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
        accounting_data = None
        bs_data = None
        pl_data = None

    capital_stock_amount = _get_capital_stock_amount(bs_data) if bs_data else 0

    empty_cfg = get_empty_state(page)
    context = {
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
        'capital_stock_amount': capital_stock_amount,
        'cta_config': get_post_create_cta(page),
        'empty_state_config': {
            'headline': empty_cfg['headline'].format(title=title),
            'description': empty_cfg.get('description'),
            'action_label': (empty_cfg.get('action_label') or '').format(title=title),
        },
        'beppyo15_fields': BEPPYO15_FIELD_DEFINITIONS if page == 'beppyo_15' else None,

    }

    if page == 'beppyo_15':
        company = getattr(current_user, 'company', None)
        company_id = getattr(company, 'id', None)
        if company_id:
            beppyo15_service = Beppyo15Service(company_id)
            context['beppyo15_view'] = beppyo15_service.build_page_view(accounting_data=accounting_data)
        else:
            context['beppyo15_view'] = None

    return context


@company_bp.route('/filings', methods=['GET', 'POST'])
@company_required
def filings(company):
    page = request.values.get('page', 'beppyo_2')
    if page == 'corporate_tax_calculation' and not getattr(current_user, 'is_admin', False):
        abort(404)
    context = _build_filings_context(page)
    template_path = context and filings_service.get_template(page)
    if template_path and 'corporate_tax_calculation' in template_path:
        allow_manual_edit = bool(
            current_app.debug or current_app.config.get('ENABLE_CORP_TAX_MANUAL_EDIT')
        )
        input_fields = [
            'fiscal_start_date',
            'fiscal_end_date',
            'months_in_period',
            'months_truncated',
            'pre_tax_income',
            'corporate_tax_rate_low',
            'corporate_tax_rate_high',
            'local_corporate_tax_rate',
            'enterprise_tax_rate_u4m',
            'enterprise_tax_rate_4m_8m',
            'enterprise_tax_rate_o8m',
            'local_special_tax_rate',
            'prefectural_corporate_tax_rate',
            'prefectural_equalization_amount',
            'municipal_corporate_tax_rate',
            'municipal_equalization_amount',
        ]
        result_fields = [
            'corporate_tax',
            'local_corporate_tax',
            'local_tax',
            'total_tax',
            'payment_rate',
            'effective_rate',
            'enterprise_tax_amount',
            'local_special_tax',
            'enterprise_tax_total',
            'pref_corporate_tax',
            'pref_equalization_amount',
            'pref_tax_total',
            'enterprise_pref_total',
            'municipal_corporate_tax',
            'municipal_equalization_amount',
            'municipal_tax_total',
        ]
        breakdown_fields = [
            'income_u800',
            'income_o800',
            'corporate_tax_low_rate',
            'corporate_tax_high_rate',
            'enterprise_tax_base',
            'enterprise_income_u4m',
            'enterprise_base_u4m',
            'enterprise_income_4m_8m',
            'enterprise_base_4m_8m',
            'enterprise_income_o8m',
            'enterprise_base_o8m',
            'enterprise_tax_u4m',
            'enterprise_tax_4m_8m',
            'enterprise_tax_o8m',
            'pref_tax_base',
            'municipal_tax_base',
        ]

        def _stringify_map(data, keys):
            return {key: '' if data.get(key) in (None, '') else str(data.get(key)) for key in keys}

        if allow_manual_edit and request.method == 'POST':
            inputs = {key: request.form.get(f'inputs_{key}', '').strip() for key in input_fields}

            months_ceil, months_floor = _compute_manual_period(inputs.get('fiscal_start_date'), inputs.get('fiscal_end_date'))
            if months_ceil is not None:
                inputs['months_in_period'] = str(months_ceil)
            if months_floor is not None:
                inputs['months_truncated'] = str(months_floor)

            manual_inputs, manual_results, manual_breakdown = corporate_tax_service.build_from_manual(inputs)
            context['inputs'] = _stringify_map(manual_inputs, input_fields)
            context['results'] = _stringify_map(manual_results, result_fields)
            context['breakdown'] = _stringify_map(manual_breakdown, breakdown_fields)
            context['manual_edit'] = True
        else:
            inputs, results, breakdown = corporate_tax_service.build()
            context['inputs'] = _stringify_map(inputs, input_fields)
            context['results'] = _stringify_map(results, result_fields)
            context['breakdown'] = _stringify_map(breakdown, breakdown_fields)
            context['manual_edit'] = False

        context['allow_manual_edit'] = allow_manual_edit
    if not context:
        abort(404)
    template_path = filings_service.get_template(page)
    if template_path:
        view_model = context.get('beppyo15_view') if page == 'beppyo_15' else None
        field_definitions = context.get('beppyo15_fields') if page == 'beppyo_15' else None
        return render_template(template_path, **context, view=view_model, field_definitions=field_definitions)
    return render_template('company/statement_of_accounts.html', **context)


@company_bp.route('/filings/beppyo_15/add', methods=['GET', 'POST'])
@company_required
def beppyo15_add(company):
    form = Beppyo15BreakdownForm()
    service = Beppyo15Service(company.id)
    if form.validate_on_submit():
        success, _, error = service.create_item(form)
        if success:
            flash('別表15の内訳を登録しました。', 'success')
            return redirect(url_for('company.filings', page='beppyo_15'))
        flash(error or '登録に失敗しました。', 'error')
    return render_template(
        'company/filings/beppyo_15_form.html',
        form=form,
        form_title='別表15の内訳を登録',
        field_definitions=BEPPYO15_FIELD_DEFINITIONS,
    )


@company_bp.route('/filings/beppyo_15/edit/<int:item_id>', methods=['GET', 'POST'])
@company_required
def beppyo15_edit(company, item_id):
    service = Beppyo15Service(company.id)
    item = service.get_item(item_id)
    if item is None:
        abort(404)

    if request.method == 'POST':
        form = Beppyo15BreakdownForm()
    else:
        form = Beppyo15BreakdownForm(obj=item)

    if form.validate_on_submit():
        success, _, error = service.update_item(item, form)
        if success:
            flash('別表15の内訳を更新しました。', 'success')
            return redirect(url_for('company.filings', page='beppyo_15'))
        flash(error or '更新に失敗しました。', 'error')

    return render_template(
        'company/filings/beppyo_15_form.html',
        form=form,
        form_title='別表15の内訳を編集',
        field_definitions=BEPPYO15_FIELD_DEFINITIONS,
    )


@company_bp.route('/filings/beppyo_15/delete/<int:item_id>', methods=['POST'])
@company_required
def beppyo15_delete(company, item_id):
    service = Beppyo15Service(company.id)
    item = service.get_item(item_id)
    if item is None:
        abort(404)
    success, error = service.delete_item(item)
    if success:
        flash('別表15の内訳を削除しました。', 'success')
    else:
        flash(error or '削除に失敗しました。', 'error')
    return redirect(url_for('company.filings', page='beppyo_15'))


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
