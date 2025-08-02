# app/company/core.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.company import company_bp
from app.company.models import Company
from app.company.forms import CompanyForm, DeclarationForm
from app import db

@company_bp.route('/', methods=['GET', 'POST'])
@login_required
def show():
    """基本情報ページの表示と更新"""
    company = Company.query.first()

    if request.method == 'POST':
        form = CompanyForm()
        if form.validate_on_submit():
            if not company:
                company = Company()
                db.session.add(company)
            form.populate_obj(company)
            db.session.commit()
            flash('基本情報を更新しました。', 'success')
            return redirect(url_for('company.show'))
    else: # GET request
        if company:
            form = CompanyForm(obj=company)
        else:
            form = CompanyForm()

    return render_template('register.html', form=form)

@company_bp.route('/declaration', methods=['GET', 'POST'])
@login_required
def declaration():
    """申告情報ページ"""
    company = Company.query.first()
    if not company:
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))
    
    form = DeclarationForm(obj=company)
    if form.validate_on_submit():
        form.populate_obj(company)
        db.session.commit()
        flash('申告情報を更新しました。', 'success')
        return redirect(url_for('company.declaration'))
    
    return render_template('declaration_form.html', form=form)