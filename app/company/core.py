# app/company/core.py
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.company import company_bp
from app.company.forms import CompanyForm, DeclarationForm
from app.navigation import get_navigation_state, mark_step_as_completed
from .services import DeclarationService
from .auth import company_required
from .services.company_service import CompanyService
from app.primitives.dates import get_company_period, company_closing_date
from app.models_utils.date_readers import ensure_date

@company_bp.route('/info', methods=['GET', 'POST'])
@login_required
def info():
    """基本情報ページの表示と更新"""
    company = CompanyService.get_company_by_user(current_user.id)
    form = CompanyForm(request.form, obj=company)

    if form.validate_on_submit():
        CompanyService.create_or_update_company(form, current_user.id)
        mark_step_as_completed('company_info')
        flash('基本情報を更新しました。', 'success')
        # 次のステップである会計ソフト選択画面へリダイレクト
        return redirect(url_for('company.shareholders'))

    navigation_state = get_navigation_state('company_info')
    # テンプレート名を register.html から company/info.html のような適切なものに変更すべきだが、
    # UI変更禁止の原則に基づき、既存の register.html を使用する
    return render_template('register.html', form=form, navigation_state=navigation_state)

@company_bp.route('/declaration', methods=['GET', 'POST'])
@company_required
def declaration(company):
    """申告情報ページ"""
    service = DeclarationService(company.id)
    form = DeclarationForm(request.form)

    if form.validate_on_submit():
        service.update_declaration_data(form)
        mark_step_as_completed('declaration')
        flash('申告情報を更新しました。', 'success')
        return redirect(url_for('company.office_list'))

    form, _ = service.populate_declaration_form()

    # 文字列→date変換の前に、共通プリミティブから安全に日付を取得（内部読み取りのみの変更）
    from datetime import datetime
    period = get_company_period(company)
    if period.start:
        form.accounting_period_start.data = period.start
    else:
        # 直 strptime を避け、共通の ensure_date を使用
        form.accounting_period_start.data = ensure_date(form.accounting_period_start.data)

    if period.end:
        form.accounting_period_end.data = period.end
    else:
        form.accounting_period_end.data = ensure_date(form.accounting_period_end.data)

    # Ensure closing_date (String in DB) is converted to date for WTForms DateField
    close_d = company_closing_date(company)
    if close_d:
        form.closing_date.data = close_d
    else:
        form.closing_date.data = ensure_date(form.closing_date.data)

    navigation_state = get_navigation_state('declaration')
    return render_template('company/declaration_form.html', form=form, navigation_state=navigation_state)
