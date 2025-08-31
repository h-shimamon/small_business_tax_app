# app/company/statement_of_accounts.py
from flask import render_template, request, redirect, url_for, flash, abort, current_app
from app.constants import FLASH_SKIP
from app.company import company_bp
from app.company.models import (
    Deposit, NotesReceivable, AccountsReceivable, TemporaryPayment,
    LoansReceivable, Inventory, Security, FixedAsset, NotesPayable,
    AccountsPayable, TemporaryReceipt, Borrowing, ExecutiveCompensation,
    LandRent, Miscellaneous, AccountingData
)
from app.company.forms import (
    DepositForm, NotesReceivableForm, AccountsReceivableForm, TemporaryPaymentForm,
    LoansReceivableForm, InventoryForm, SecurityForm, FixedAssetForm, NotesPayableForm,
    AccountsPayableForm, TemporaryReceiptForm, BorrowingForm, ExecutiveCompensationForm,
    LandRentForm, MiscellaneousForm
)
from app import db
from app.navigation import (
    get_navigation_state,
    mark_step_as_completed,
    unmark_step_as_completed,
    compute_skipped_steps_for_company,
)
from .auth import company_required
from app.company.services.master_data_service import MasterDataService
from app.company.services.soa_summary_service import SoASummaryService
from app.progress.evaluator import SoAProgressEvaluator
from app.company.soa_mappings import SUMMARY_PAGE_MAP, PL_PAGE_ACCOUNTS
from app.company.soa_config import STATEMENT_PAGES_CONFIG
from app.pdf.uchiwakesyo_yocyokin import generate_uchiwakesyo_yocyokin
from app.pdf.uchiwakesyo_urikakekin import generate_uchiwakesyo_urikakekin
from app.pdf.uchiwakesyo_uketoritegata import generate_uchiwakesyo_uketoritegata
from app.pdf.uchiwakesyo_karibaraikin_kashitukekin import generate_uchiwakesyo_karibaraikin_kashitukekin
from app.models_utils.date_readers import ensure_date

# mappings are centralized in app.company.soa_mappings


"""STATEMENT_PAGES_CONFIG moved to app.company.soa_config and imported above."""

@company_bp.route('/statement_of_accounts')
@company_required
def statement_of_accounts(company):
    """勘定科目内訳書ページ"""
    page = request.args.get('page', 'deposits')
    # 旧ページキー 'miscellaneous' は分割済みのため、雑収入へ案内
    if page == 'miscellaneous':
        flash('「雑益・雑損失等」は「雑収入」「雑損失」に分割されました。雑収入のページへ案内します。', 'info')
        return redirect(url_for('company.statement_of_accounts', page='misc_income'))
    config = STATEMENT_PAGES_CONFIG.get(page)
    if not config:
        abort(404)

    # Pre-fetch latest AccountingData to avoid duplicate queries in skip computations
    accounting_data = AccountingData.query.filter_by(company_id=company.id).order_by(AccountingData.created_at.desc()).first()

    # Compute skipped pages (source total == 0) for SoA group and optionally redirect forward
    skipped_steps = compute_skipped_steps_for_company(company.id, accounting_data=accounting_data)

    # If current page should be skipped, redirect to the next non-skipped page (forward search only)
    # Collect SoA children (navigation order) for forward search
    try:
        from app.navigation_builder import navigation_tree
        soa_children = []
        for node in navigation_tree:
            if node.key == 'statement_of_accounts_group':
                soa_children = node.children
                break
    except Exception:
        soa_children = []
    current_child_index = None
    for idx, child in enumerate(soa_children):
        if (child.params or {}).get('page') == page:
            current_child_index = idx
            break
    if current_child_index is not None and soa_children:
        current_child = soa_children[current_child_index]
        if current_child.key in skipped_steps:
            # forward search to next non-skipped
            for nxt in soa_children[current_child_index+1:]:
                if nxt.key not in skipped_steps:
                    flash('財務諸表に計上されていない勘定科目は自動でスキップされます。', FLASH_SKIP)
                    return redirect(url_for('company.statement_of_accounts', page=(nxt.params or {}).get('page')))
            # wrap-around to 申告書データ は保留のため遷移しない

    # Build base query and allow optional page-specific filter from config
    query = db.session.query(config['model']).filter_by(company_id=company.id)
    try:
        qf = config.get('query_filter')
    except Exception:
        qf = None
    if callable(qf):
        try:
            query = qf(query)
        except Exception:
            pass
    items = query.all()
    total = sum(getattr(item, config['total_field'], 0) for item in items)
    
    # Provide pdf_year for template-level PDF button rendering (fallback to accounting period or default)
    try:
        _pdf_year = (accounting_data.period_end.year if accounting_data and accounting_data.period_end else None)
    except Exception:
        _pdf_year = None
    context = {
        'page': page,
        'page_title': config['title'],
        'items': items,
        'total': total,
        'navigation_state': get_navigation_state(page, skipped_steps=skipped_steps),
        'deposit_summary': None,
        'soa_next_url': None,
        'soa_next_name': None,
        'pdf_year': _pdf_year or '2025',
    }

    # Safe defaults to avoid template errors if summary computation fails
    if 'generic_summary' not in locals():
        pass
    context.setdefault('generic_summary', {'bs_total': 0, 'breakdown_total': 0, 'difference': 0})
    if page == 'deposits':
        context.setdefault('deposit_summary', context['generic_summary'])
    elif page == 'notes_receivable':
        context.setdefault('notes_receivable_summary', context['generic_summary'])
    elif page == 'accounts_receivable':
        context.setdefault('accounts_receivable_summary', context['generic_summary'])

    # Optional: legacy GET-side marking (controlled by flag)
    try:
        if current_app.config.get('SOA_MARK_ON_GET', True):
            diff = SoASummaryService.compute_difference(company.id, page, config['model'], config['total_field'], accounting_data=accounting_data)
            if isinstance(diff, dict) and (diff.get('difference', None) == 0):
                mark_step_as_completed(page)
            else:
                unmark_step_as_completed(page)
    except Exception as e:
        current_app.logger.warning('SoA mark (GET) failed for page %s: %s', page, e)

    # Post-create success panel context (soft commonization)
    try:
        created_flag = request.args.get('created')
        created_id = request.args.get('created_id')
        if created_flag:
            # Default CTAs: continue adding and back to list
            ctas = [
                {'label': f'続けて{config["title"]}を登録', 'href': url_for('company.add_item', page_key=page), 'class': 'button-primary'},
                {'label': '一覧へ戻る', 'href': url_for('company.statement_of_accounts', page=page), 'class': 'button-secondary'},
            ]
            context['post_create'] = {
                'title': f'{config["title"]}を登録しました',
                'desc': None,
                'ctas': ctas,
                'created_id': created_id,
            }
    except Exception:
        pass

    # Helper: compute next Statement of Accounts page URL and name
    def compute_next_soa(page_key):
        """Return URL and name of the next SoA page; log expected issues instead of silencing all exceptions."""
        try:
            from app.navigation_builder import navigation_tree
        except ImportError as e:
            current_app.logger.warning('navigation_tree import failed: %s', e)
            return None, None

        try:
            for node in navigation_tree:
                if node.key == 'statement_of_accounts_group':
                    children = node.children
                    for idx, child in enumerate(children):
                        child_page = (child.params or {}).get('page')
                        if child_page == page_key:
                            if idx + 1 < len(children):
                                nxt = children[idx + 1]
                                return url_for('company.statement_of_accounts', page=(nxt.params or {}).get('page')), nxt.name
                            break
        except (AttributeError, KeyError, IndexError, TypeError) as e:
            current_app.logger.warning('compute_next_soa failed for page %s: %s', page_key, e)
            return None, None
        return None, None

    # Compute generic summary using service (no UI/keys change)
    if page in SUMMARY_PAGE_MAP:
        master_type, _ = SUMMARY_PAGE_MAP[page]
        model = config['model']
        total_field_name = config['total_field']
        diff = SoASummaryService.compute_difference(company.id, page, model, total_field_name, accounting_data=accounting_data)
        if page == 'borrowings':
            context['borrowings_summary'] = {
                'bs_total': diff.get('bs_total', 0),
                'pl_interest_total': diff.get('pl_interest_total', 0),
                'breakdown_total': diff.get('breakdown_total', 0),
                'difference': diff.get('difference', 0),
            }
            # Keep generic_summary aligned for header logic
            context['generic_summary'] = context['borrowings_summary']
            context['generic_summary_label'] = 'B/S上の借入金残高'
        else:
            context['generic_summary'] = {
                'bs_total': diff.get('bs_total', 0),
                'breakdown_total': diff.get('breakdown_total', 0),
                'difference': diff.get('difference', 0),
            }
            context['generic_summary_label'] = f"{'B/S上の' if master_type == 'BS' else 'P/L上の'}{config['title']}残高"
        # Map to page-specific summary keys for templates
        if page == 'deposits':
            context['deposit_summary'] = context['generic_summary']
        elif page == 'notes_receivable':
            context['notes_receivable_summary'] = context['generic_summary']
        elif page == 'accounts_receivable':
            context['accounts_receivable_summary'] = context['generic_summary']
        # Mark step completed if reconciled
        step_key = 'fixed_assets_soa' if page == 'fixed_assets' else page
        difference = context.get('generic_summary', {}).get('difference', 0)
        if difference == 0:
            mark_step_as_completed(step_key)
        else:
            unmark_step_as_completed(step_key)
        # Next link
        # NOTE: `soa_next_url` はヘッダ右上の主要CTA（「次の内訳へ」）表示にのみ使用する。サマリー内にCTAは置かない（UI方針）。

        context['soa_next_url'], context['soa_next_name'] = compute_next_soa(page)
    # Refresh navigation after potential step completion
    context['navigation_state'] = get_navigation_state(page, skipped_steps=skipped_steps)
    return render_template('company/statement_of_accounts.html', **context)

@company_bp.route('/statement/deposits/pdf')
@company_required
def deposits_pdf(company):
    """預貯金等の内訳をPDFに出力（検証用）。"""
    from flask import current_app, send_file
    import os
    from datetime import datetime
    year = request.args.get('year', '2025')
    base_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
    filled_dir = os.path.join(base_dir, 'temporary', 'filled')
    os.makedirs(filled_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    out_path = os.path.join(filled_dir, f"uchiwakesyo_yocyokin_{company.id}_{ts}.pdf")
    generate_uchiwakesyo_yocyokin(company_id=company.id, year=year, output_path=out_path)
    return send_file(
        out_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"uchiwakesyo_yocyokin_{year}.pdf"
    )

@company_bp.route('/statement/accounts_receivable/pdf')
@company_required
def accounts_receivable_pdf(company):
    """売掛金（未収入金）の内訳をPDFに出力（検証用）。"""
    from flask import current_app, send_file
    import os
    from datetime import datetime
    year = request.args.get('year', '2025')
    base_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
    filled_dir = os.path.join(base_dir, 'temporary', 'filled')
    os.makedirs(filled_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    out_path = os.path.join(filled_dir, f"uchiwakesyo_urikakekin_{company.id}_{ts}.pdf")
    generate_uchiwakesyo_urikakekin(company_id=company.id, year=year, output_path=out_path)
    return send_file(
        out_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"uchiwakesyo_urikakekin_{year}.pdf"
    )

@company_bp.route('/statement/temporary_payments/pdf')
@company_required
def temporary_payments_pdf(company):
    """仮払金（前渡金）の内訳をPDFに出力（検証用）。"""
    from flask import current_app, send_file
    import os
    from datetime import datetime
    year = request.args.get('year', '2025')
    base_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
    filled_dir = os.path.join(base_dir, 'temporary', 'filled')
    os.makedirs(filled_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    out_path = os.path.join(filled_dir, f"uchiwakesyo_karibaraikin-kashitukekin_{company.id}_{ts}.pdf")
    generate_uchiwakesyo_karibaraikin_kashitukekin(company_id=company.id, year=year, output_path=out_path)
    return send_file(
        out_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"uchiwakesyo_karibaraikin-kashitukekin_{year}.pdf"
    )

@company_bp.route('/statement/notes_receivable/pdf')
@company_required
def notes_receivable_pdf(company):
    """受取手形の内訳をPDFに出力（検証用）。"""
    from flask import current_app, send_file
    import os
    from datetime import datetime
    year = request.args.get('year', '2025')
    base_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
    filled_dir = os.path.join(base_dir, 'temporary', 'filled')
    os.makedirs(filled_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    out_path = os.path.join(filled_dir, f"uchiwakesyo_uketoritegata_{company.id}_{ts}.pdf")
    generate_uchiwakesyo_uketoritegata(company_id=company.id, year=year, output_path=out_path)
    return send_file(
        out_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"uchiwakesyo_uketoritegata_{year}.pdf"
    )

@company_bp.route('/statement/notes_payable/pdf')
@company_required
def notes_payable_pdf(company):
    """支払手形の内訳をPDFに出力（検証用）。"""
    from flask import current_app, send_file
    import os
    from datetime import datetime
    from app.pdf.uchiwakesyo_shiharaitegata import generate_uchiwakesyo_shiharaitegata
    year = request.args.get('year', '2025')
    base_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
    filled_dir = os.path.join(base_dir, 'temporary', 'filled')
    os.makedirs(filled_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    out_path = os.path.join(filled_dir, f"uchiwakesyo_shiharaitegata_{company.id}_{ts}.pdf")
    generate_uchiwakesyo_shiharaitegata(company_id=company.id, year=year, output_path=out_path)
    return send_file(
        out_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"uchiwakesyo_shiharaitegata_{year}.pdf"
    )

@company_bp.route('/statement/accounts_payable/pdf')
@company_required
def accounts_payable_pdf(company):
    """買掛金（未払金・未払費用）の内訳をPDFに出力（検証用）。"""
    from flask import current_app, send_file
    import os
    from datetime import datetime
    from app.pdf.uchiwakesyo_kaikakekin import generate_uchiwakesyo_kaikakekin
    year = request.args.get('year', '2025')
    base_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
    filled_dir = os.path.join(base_dir, 'temporary', 'filled')
    os.makedirs(filled_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    out_path = os.path.join(filled_dir, f"uchiwakesyo_kaikakekin_{company.id}_{ts}.pdf")
    generate_uchiwakesyo_kaikakekin(company_id=company.id, year=year, output_path=out_path)
    return send_file(
        out_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"uchiwakesyo_kaikakekin_{year}.pdf"
    )

@company_bp.route('/statement/loans_receivable/pdf')
@company_required
def loans_receivable_pdf(company):
    """貸付金・受取利息の内訳をPDFに出力（検証用）。"""
    from flask import current_app, send_file
    import os
    from datetime import datetime
    year = request.args.get('year', '2025')
    base_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
    filled_dir = os.path.join(base_dir, 'temporary', 'filled')
    os.makedirs(filled_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    # 同一様式（上段: 仮払金 / 下段: 貸付金）を使用
    out_path = os.path.join(filled_dir, f"uchiwakesyo_karibaraikin-kashitukekin_{company.id}_{ts}.pdf")
    generate_uchiwakesyo_karibaraikin_kashitukekin(company_id=company.id, year=year, output_path=out_path)
    return send_file(
        out_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"uchiwakesyo_karibaraikin-kashitukekin_{year}.pdf"
    )

@company_bp.route('/statement/<string:page_key>/add', methods=['GET', 'POST'])
@company_required
def add_item(company, page_key):
    """汎用的な項目追加ビュー"""
    config = STATEMENT_PAGES_CONFIG.get(page_key)
    if not config:
        abort(404)
    form = config['form'](request.form)
    # ページに応じて初期値を与える（雑収入/雑損失の科目固定）
    try:
        if request.method == 'GET' and hasattr(form, 'account_name'):
            if page_key == 'misc_income':
                form.account_name.data = '雑収入'
            elif page_key == 'misc_losses':
                form.account_name.data = '雑損失'
    except Exception:
        pass
    if form.validate_on_submit():
        new_item = config['model'](company_id=company.id)
        form.populate_obj(new_item)
        # Optional: POST-side completion marking
        try:
            if current_app.config.get('SOA_MARK_ON_POST', True):
                if SoAProgressEvaluator.is_completed(company.id, page_key):
                    mark_step_as_completed(page_key)
                else:
                    unmark_step_as_completed(page_key)
        except Exception as e:
            current_app.logger.warning('SoA mark (POST) failed for page %s: %s', page_key, e)
        db.session.add(new_item)
        db.session.commit()
        flash(f"{config['title']}情報を登録しました。", 'success')
        return redirect(url_for('company.statement_of_accounts', page=page_key, created=1, created_id=new_item.id))
    # Compute skipped steps for sidebar consistency (same logic as main SoA view)
    # Pre-fetch latest AccountingData once then compute skipped steps via helper
    accounting_data = AccountingData.query.filter_by(company_id=company.id).order_by(AccountingData.created_at.desc()).first()
    skipped_steps = compute_skipped_steps_for_company(company.id, accounting_data=accounting_data)
    form_template = f"company/{config['template']}"
    return render_template(
        form_template,
        form=form,
        form_title=f"{config['title']}の新規登録",
        navigation_state=get_navigation_state(page_key, skipped_steps=skipped_steps)
    )

@company_bp.route('/statement/<string:page_key>/edit/<int:item_id>', methods=['GET', 'POST'])
@company_required
def edit_item(company, page_key, item_id):
    """汎用的な項目編集ビュー"""
    config = STATEMENT_PAGES_CONFIG.get(page_key)
    if not config:
        abort(404)
    item = db.session.query(config['model']).filter_by(id=item_id, company_id=company.id).first_or_404()
    form = config['form'](request.form, obj=item)
    if form.validate_on_submit():
        form.populate_obj(item)
        # Optional: POST-side completion marking
        try:
            if current_app.config.get('SOA_MARK_ON_POST', True):
                if SoAProgressEvaluator.is_completed(company.id, page_key):
                    mark_step_as_completed(page_key)
                else:
                    unmark_step_as_completed(page_key)
        except Exception as e:
            current_app.logger.warning('SoA mark (POST) failed for page %s: %s', page_key, e)
        db.session.commit()
        flash(f"{config['title']}情報を更新しました。", 'success')
        return redirect(url_for('company.statement_of_accounts', page=page_key))
    if request.method == 'GET':
        form = config['form'](obj=item)
        # Ensure date fields are date objects for templates
        try:
            if page_key == 'notes_receivable':
                if hasattr(form, 'issue_date'):
                    form.issue_date.data = ensure_date(form.issue_date.data)
                if hasattr(form, 'due_date'):
                    form.due_date.data = ensure_date(form.due_date.data)
        except Exception:
            pass
    # Compute skipped steps for sidebar consistency
    accounting_data = AccountingData.query.filter_by(company_id=company.id).order_by(AccountingData.created_at.desc()).first()
    skipped_steps = compute_skipped_steps_for_company(company.id, accounting_data=accounting_data)
    form_template = f"company/{config['template']}"
    return render_template(
        form_template,
        form=form,
        form_title=f"{config['title']}の編集",
        navigation_state=get_navigation_state(page_key, skipped_steps=skipped_steps)
    )

@company_bp.route('/statement/<string:page_key>/delete/<int:item_id>', methods=['POST'])
@company_required
def delete_item(company, page_key, item_id):
    """汎用的な項目削除ビュー"""
    config = STATEMENT_PAGES_CONFIG.get(page_key)
    if not config:
        abort(404)
    item = db.session.query(config['model']).filter_by(id=item_id, company_id=company.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash(f"{config['title']}情報を削除しました。", 'success')
    # Optional: POST-side completion marking after delete (move before redirect)
    try:
        if current_app.config.get('SOA_MARK_ON_POST', True):
            if SoAProgressEvaluator.is_completed(company.id, page_key):
                mark_step_as_completed(page_key)
            else:
                unmark_step_as_completed(page_key)
    except Exception as e:
        current_app.logger.warning('SoA mark (DELETE) failed for page %s: %s', page_key, e)
    return redirect(url_for('company.statement_of_accounts', page=page_key))


# 旧パス互換のための薄いエイリアスのみ追加（既存の /statement_of_accounts は重複させない）
@company_bp.route('/statement/<page_key>/add')
def legacy_add_item(page_key):
    # 互換: /statement/accounts_payable/add → 新実装の add_item に誘導
    return redirect(url_for('company.add_item', page_key=page_key), code=302)


