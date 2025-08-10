# app/company/core.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.company import company_bp
from app.company.models import Company
from app.company.forms import CompanyForm, DeclarationForm
from app import db
from app.navigation import get_navigation_state, mark_step_as_completed
from .services import DeclarationService
from .auth import company_required

@company_bp.route('/', methods=['GET', 'POST'])
@login_required
def show():
    """基本情報ページの表示と更新"""
    company = Company.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        form = CompanyForm(request.form)
        if form.validate_on_submit():
            if company: # 更新
                form.populate_obj(company)
            else: # 新規作成
                company = Company(user_id=current_user.id)
                form.populate_obj(company)
                db.session.add(company)
            
            db.session.commit()
            mark_step_as_completed('company_info')
            flash('基本情報を更新しました。', 'success')
            return redirect(url_for('company.show'))
    else: # GET
        form = CompanyForm(obj=company)

    wizard_progress = get_navigation_state('company_info')
    return render_template('register.html', form=form, navigation_state=wizard_progress)

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
        return redirect(url_for('company.declaration'))

    # GETリクエストの場合、フォームにデータを設定
    form, _ = service.populate_declaration_form()

    wizard_progress = get_navigation_state('declaration')
    return render_template('declaration_form.html', form=form, navigation_state=wizard_progress)