# app/company/statement_of_accounts.py
from flask import render_template, request, redirect, url_for, flash, abort
from app.company import company_bp
from app.company.models import (
    AccountingData
)
from app.navigation import (
    get_navigation_state,
    compute_skipped_steps_for_company,
    mark_step_as_completed,
    unmark_step_as_completed,
)
from .auth import company_required
from app.company.services.statement_of_accounts_flow import (
    StatementOfAccountsFlow,
    RedirectRequired,
)
from app.company.services.statement_of_accounts_service import StatementOfAccountsService
from app.company.services.protocols import StatementOfAccountsServiceProtocol
from app.progress.evaluator import SoAProgressEvaluator
from app.services.soa_registry import STATEMENT_PAGES_CONFIG
from app.pdf.uchiwakesyo_yocyokin import generate_uchiwakesyo_yocyokin
from app.pdf.uchiwakesyo_urikakekin import generate_uchiwakesyo_urikakekin
from app.pdf.uchiwakesyo_uketoritegata import generate_uchiwakesyo_uketoritegata
from app.pdf.uchiwakesyo_karibaraikin_kashitukekin import generate_uchiwakesyo_karibaraikin_kashitukekin
from app.models_utils.date_readers import ensure_date

# mappings are centralized in app.services.soa_registry


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

    accounting_data = AccountingData.query.filter_by(company_id=company.id).order_by(AccountingData.created_at.desc()).first()

    flow = StatementOfAccountsFlow(company.id, accounting_data=accounting_data)
    try:
        context_data = flow.prepare_context(
            page,
            created_flag=request.args.get('created'),
            created_id=request.args.get('created_id'),
        )
    except RedirectRequired as exc:
        return redirect(exc.target_url)

    context = context_data.context
    return render_template('company/statement_of_accounts.html', **context)

@company_bp.route('/statement/deposits/pdf')
@company_required
def deposits_pdf(company):
    """預貯金等の内訳をPDFに出力（検証用）。"""
    from flask import current_app, send_file
    import os
    from datetime import datetime
    # Always print on the latest available template year (hint only)
    year = '2099'
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
    # Always print on the latest available template year (hint only)
    year = '2099'
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
    # Always print on the latest available template year (hint only)
    year = '2099'
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
    # Always print on the latest available template year (hint only)
    year = '2099'
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
    # Always print on the latest available template year (hint only)
    year = '2099'
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
    # Always print on the latest available template year (hint only)
    year = '2099'
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
    # Always print on the latest available template year (hint only)
    year = '2099'
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

@company_bp.route('/statement/borrowings/pdf')
@company_required
def borrowings_pdf(company):
    """借入金及び支払利子の内訳（上下二段）をPDFに出力（検証用）。"""
    from flask import current_app, send_file
    import os
    from datetime import datetime
    from app.pdf.borrowings_two_tier import generate_borrowings_two_tier
    # Always print on the latest available template year (hint only)
    year = '2099'
    base_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
    filled_dir = os.path.join(base_dir, 'temporary', 'filled')
    os.makedirs(filled_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    out_path = os.path.join(filled_dir, f"borrowings_two_tier_{company.id}_{ts}.pdf")
    generate_borrowings_two_tier(company_id=company.id, year=year, output_path=out_path)
    return send_file(
        out_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f"borrowings_two_tier_{year}.pdf"
    )

@company_bp.route('/statement/<string:page_key>/add', methods=['GET', 'POST'])
@company_required
def add_item(company, page_key):
    """汎用的な項目追加ビュー"""
    config = STATEMENT_PAGES_CONFIG.get(page_key)
    if not config:
        abort(404)
    soa_service: StatementOfAccountsServiceProtocol = StatementOfAccountsService(company.id)
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
        success, created_item, error = soa_service.create_item(page_key, form)
        if success:
            try:
                if current_app.config.get('SOA_MARK_ON_POST', True):
                    if SoAProgressEvaluator.is_completed(company.id, page_key):
                        mark_step_as_completed(page_key)
                    else:
                        unmark_step_as_completed(page_key)
            except Exception as e:
                current_app.logger.warning('SoA mark (POST) failed for page %s: %s', page_key, e)
            flash(f"{config['title']}情報を登録しました。", 'success')
            return redirect(url_for('company.statement_of_accounts', page=page_key, created=1, created_id=getattr(created_item, 'id', None)))
        flash(error or '登録に失敗しました。', 'error')
    # Compute skipped steps for sidebar consistency (same logic as main SoA view)
    # Pre-fetch latest AccountingData once then compute skipped steps via helper
    accounting_data = AccountingData.query.filter_by(company_id=company.id).order_by(AccountingData.created_at.desc()).first()
    skipped_steps = compute_skipped_steps_for_company(company.id, accounting_data=accounting_data)
    form_template = f"company/{config['template']}"
    return render_template(
        form_template,
        form=form,
        form_title=f"{config['title']}の新規登録",
        navigation_state=get_navigation_state(page_key, skipped_steps=skipped_steps),
        form_fields=config.get('form_fields', []),
    )

@company_bp.route('/statement/<string:page_key>/edit/<int:item_id>', methods=['GET', 'POST'])
@company_required
def edit_item(company, page_key, item_id):
    """汎用的な項目編集ビュー"""
    config = STATEMENT_PAGES_CONFIG.get(page_key)
    if not config:
        abort(404)
    soa_service: StatementOfAccountsServiceProtocol = StatementOfAccountsService(company.id)
    item = soa_service.get_item_by_id(page_key, item_id)
    if item is None:
        abort(404)
    form = config['form'](request.form, obj=item)
    if form.validate_on_submit():
        success, updated_item, error = soa_service.update_item(page_key, item, form)
        if success:
            try:
                if current_app.config.get('SOA_MARK_ON_POST', True):
                    if SoAProgressEvaluator.is_completed(company.id, page_key):
                        mark_step_as_completed(page_key)
                    else:
                        unmark_step_as_completed(page_key)
            except Exception as e:
                current_app.logger.warning('SoA mark (POST) failed for page %s: %s', page_key, e)
            flash(f"{config['title']}情報を更新しました。", 'success')
            return redirect(url_for('company.statement_of_accounts', page=page_key))
        flash(error or '更新に失敗しました。', 'error')
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
        navigation_state=get_navigation_state(page_key, skipped_steps=skipped_steps),
        form_fields=config.get('form_fields', []),
    )

@company_bp.route('/statement/<string:page_key>/delete/<int:item_id>', methods=['POST'])
@company_required
def delete_item(company, page_key, item_id):
    """汎用的な項目削除ビュー"""
    config = STATEMENT_PAGES_CONFIG.get(page_key)
    if not config:
        abort(404)
    soa_service: StatementOfAccountsServiceProtocol = StatementOfAccountsService(company.id)
    item = soa_service.get_item_by_id(page_key, item_id)
    if item is None:
        abort(404)
    success, message = soa_service.delete_item(page_key, item_id)
    if success:
        flash(message or f"{config['title']}情報を削除しました。", 'success')
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
    flash(message or '削除に失敗しました。', 'error')
    return redirect(url_for('company.statement_of_accounts', page=page_key))


# 旧パス互換のための薄いエイリアスのみ追加（既存の /statement_of_accounts は重複させない）
@company_bp.route('/statement/<page_key>/add')
def legacy_add_item(page_key):
    # 互換: /statement/accounts_payable/add → 新実装の add_item に誘導
    return redirect(url_for('company.add_item', page_key=page_key), code=302)


