# app/company/statement_of_accounts.py
import os
from datetime import datetime

from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from app.company import company_bp
from app.company.models import AccountingData
from app.company.services.protocols import StatementOfAccountsServiceProtocol
from app.company.services.statement_of_accounts_flow import (
    RedirectRequired,
    StatementOfAccountsFlow,
)
from app.company.services.statement_of_accounts_service import (
    StatementOfAccountsService,
)
from app.models_utils.date_readers import ensure_date
from app.navigation import (
    compute_skipped_steps_for_company,
    get_navigation_state,
    mark_step_as_completed,
    unmark_step_as_completed,
)
from app.progress.evaluator import SoAProgressEvaluator
from app.services.app_registry import get_default_pdf_year
from app.services.pdf_registry import get_statement_pdf_config
from app.services.soa_registry import STATEMENT_PAGES_CONFIG

from .auth import company_required

# mappings are centralized in app.services.soa_registry




def _get_statement_config(page_key: str) -> dict:
    config = STATEMENT_PAGES_CONFIG.get(page_key)
    if not config:
        abort(404)
    return config


def _build_statement_service(company_id: int) -> StatementOfAccountsServiceProtocol:
    return StatementOfAccountsService(company_id)


def _prefill_form_defaults(form, page_key: str) -> None:
    try:
        if hasattr(form, 'account_name'):
            if page_key == 'misc_income':
                form.account_name.data = '雑収入'
            elif page_key == 'misc_losses':
                form.account_name.data = '雑損失'
    except Exception:
        pass


def _normalize_edit_form(form, page_key: str) -> None:
    if page_key != 'notes_receivable':
        return
    try:
        if hasattr(form, 'issue_date'):
            form.issue_date.data = ensure_date(form.issue_date.data)
        if hasattr(form, 'due_date'):
            form.due_date.data = ensure_date(form.due_date.data)
    except Exception:
        pass


def _latest_accounting_data(company_id: int):
    return (
        AccountingData.query
        .filter_by(company_id=company_id)
        .order_by(AccountingData.created_at.desc())
        .first()
    )


def _navigation_state(company_id: int, page_key: str):
    accounting_data = _latest_accounting_data(company_id)
    skipped = compute_skipped_steps_for_company(company_id, accounting_data=accounting_data)
    return get_navigation_state(page_key, skipped_steps=skipped)


def _maybe_update_completion(company_id: int, page_key: str) -> None:
    if not current_app.config.get('SOA_MARK_ON_POST', True):
        return
    try:
        if SoAProgressEvaluator.is_completed(company_id, page_key):
            mark_step_as_completed(page_key)
        else:
            unmark_step_as_completed(page_key)
    except Exception as exc:
        current_app.logger.warning('SoA mark (POST) failed for page %s: %s', page_key, exc)


def _render_statement_form(company_id: int, page_key: str, config: dict, form, *, form_title: str):
    navigation_state = _navigation_state(company_id, page_key)
    template_name = f"company/{config['template']}"
    return render_template(
        template_name,
        form=form,
        form_title=form_title,
        navigation_state=navigation_state,
        form_fields=config.get('form_fields', []),
    )


def _handle_create_submission(company, page_key: str, config: dict, form):
    service = _build_statement_service(company.id)
    success, created_item, error = service.create_item(page_key, form)
    if not success:
        flash(error or '登録に失敗しました。', 'error')
        return None
    _maybe_update_completion(company.id, page_key)
    flash(f"{config['title']}情報を登録しました。", 'success')
    return redirect(
        url_for(
            'company.statement_of_accounts',
            page=page_key,
            created=1,
            created_id=getattr(created_item, 'id', None),
        )
    )


def _handle_update_submission(company, page_key: str, config: dict, form, item):
    service = _build_statement_service(company.id)
    success, updated_item, error = service.update_item(page_key, item, form)
    if not success:
        flash(error or '更新に失敗しました。', 'error')
        return None
    _maybe_update_completion(company.id, page_key)
    flash(f"{config['title']}情報を更新しました。", 'success')
    return redirect(url_for('company.statement_of_accounts', page=page_key))

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

@company_bp.route('/statement/<string:page_key>/pdf')
@company_required
def statement_pdf(company, page_key):
    """汎用的な勘定科目内訳書PDF出力エンドポイント。"""
    config = get_statement_pdf_config(page_key)
    if not config:
        abort(404)

    year = get_default_pdf_year()
    base_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
    filled_dir = os.path.join(base_dir, 'temporary', 'filled')
    os.makedirs(filled_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    filename = config.filename_pattern.format(company_id=company.id, timestamp=timestamp)
    output_path = os.path.join(filled_dir, filename)

    try:
        generated_path = config.generator(company_id=company.id, year=year, output_path=output_path)
        if generated_path:
            output_path = generated_path
    except Exception as exc:
        current_app.logger.exception('Failed to generate PDF for %s: %s', page_key, exc)
        flash('PDF生成中にエラーが発生しました。時間をおいて再度お試しください。', 'danger')
        return redirect(url_for('company.statement_of_accounts', page=page_key))

    download_name = config.download_name_pattern.format(year=year)
    return send_file(
        output_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=download_name,
    )

@company_bp.route('/statement/<string:page_key>/add', methods=['GET', 'POST'])
@company_required

def add_item(company, page_key):
    """汎用的な項目追加ビュー"""
    config = _get_statement_config(page_key)
    form = config['form'](request.form)

    if request.method == 'GET':
        _prefill_form_defaults(form, page_key)

    if form.validate_on_submit():
        response = _handle_create_submission(company, page_key, config, form)
        if response is not None:
            return response

    return _render_statement_form(
        company.id,
        page_key,
        config,
        form,
        form_title=f"{config['title']}の新規登録",
    )

@company_bp.route('/statement/<string:page_key>/edit/<int:item_id>', methods=['GET', 'POST'])
@company_required

def edit_item(company, page_key, item_id):
    """汎用的な項目編集ビュー"""
    config = _get_statement_config(page_key)
    service = _build_statement_service(company.id)
    item = service.get_item_by_id(page_key, item_id)
    if item is None:
        abort(404)

    if request.method == 'POST':
        form = config['form'](request.form, obj=item)
        if form.validate_on_submit():
            response = _handle_update_submission(company, page_key, config, form, item)
            if response is not None:
                return response
    else:
        form = config['form'](obj=item)
        _normalize_edit_form(form, page_key)

    return _render_statement_form(
        company.id,
        page_key,
        config,
        form,
        form_title=f"{config['title']}の編集",
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


