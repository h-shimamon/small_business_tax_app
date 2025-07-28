# app/company/core.py

from flask import render_template, request, redirect, url_for, flash
from app.company import company_bp
from app.company.models import Company
from app.company.forms import DeclarationForm
from app import db

@company_bp.route('/')
def show():
    """基本情報ページのトップ。"""
    company = Company.query.first()
    # register.htmlはcompanyディレクトリの外にあるため、テンプレートパスを調整
    return render_template('register.html', company=company)

@company_bp.route('/save', methods=['POST'])
def save():
    """フォームから送信されたデータを保存（新規登録または更新）する。"""
    company = Company.query.first()
    if not company:
        company = Company()
    
    company.corporate_number = request.form.get('corporate_number')
    company.company_name = request.form.get('company_name')
    company.company_name_kana = request.form.get('company_name_kana')
    company.zip_code = request.form.get('zip_code')
    company.prefecture = request.form.get('prefecture')
    company.city = request.form.get('city')
    company.address = request.form.get('address')
    company.phone_number = request.form.get('phone_number')
    company.homepage = request.form.get('homepage')
    company.establishment_date = request.form.get('establishment_date')
    company.capital_limit = 'capital_limit' in request.form
    company.is_supported_industry = 'is_supported_industry' in request.form
    company.is_not_excluded_business = 'is_not_excluded_business' in request.form
    company.industry_type = request.form.get('industry_type')
    company.industry_code = request.form.get('industry_code')
    company.reference_number = request.form.get('reference_number')

    db.session.add(company)
    db.session.commit()
    return redirect(url_for('company.show'))

@company_bp.route('/declaration', methods=['GET', 'POST'])
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