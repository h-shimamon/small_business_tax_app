# app/company/shareholders.py
from flask import render_template, request, redirect, url_for, flash
from app.company import company_bp
from app.company.models import Shareholder, Company
from app.company.forms import ShareholderForm
from app import db
from app.navigation import get_navigation_state
from .auth import company_required

def get_page_title_and_check_redirect(company_name):
    """法人名に応じて動的なページタイトルを決定し、リダイレクトが必要か判定する"""
    if '株式会社' in company_name or '有限会社' in company_name:
        return '株主情報', None
    elif any(corp_type in company_name for corp_type in ['合同会社', '合名会社', '合資会社']):
        return '社員情報', None
    else:
        # 条件に合致しない場合はリダイレクト先を返す
        return None, redirect(url_for('company.declaration'))

@company_bp.route('/shareholders')
@company_required
def shareholders(company):
    """株主/社員情報の一覧ページ"""
    page_title, response = get_page_title_and_check_redirect(company.company_name)
    if response:
        return response

    shareholder_list = company.shareholders
    navigation_state = get_navigation_state('shareholders')
    return render_template(
        'company/shareholder_list.html', 
        shareholders=shareholder_list, 
        navigation_state=navigation_state,
        page_title=page_title
    )

@company_bp.route('/shareholder/register', methods=['GET', 'POST'])
@company_required
def register_shareholder(company):
    """株主/社員の新規登録"""
    page_title, response = get_page_title_and_check_redirect(company.company_name)
    if response:
        return response

    form = ShareholderForm(request.form)
    if form.validate_on_submit():
        new_shareholder = Shareholder(company_id=company.id)
        form.populate_obj(new_shareholder)
        db.session.add(new_shareholder)
        db.session.commit()
        flash(f'{page_title}を登録しました。', 'success')
        return redirect(url_for('company.shareholders'))
        
    navigation_state = get_navigation_state('shareholders')
    return render_template(
        'company/register_shareholder.html', 
        form=form, 
        navigation_state=navigation_state,
        page_title=page_title
    )

@company_bp.route('/shareholder/edit/<int:shareholder_id>', methods=['GET', 'POST'])
@company_required
def edit_shareholder(company, shareholder_id):
    """株主/社員情報の編集"""
    page_title, response = get_page_title_and_check_redirect(company.company_name)
    if response:
        return response

    shareholder = Shareholder.query.filter_by(id=shareholder_id, company_id=company.id).first_or_404()
    
    form = ShareholderForm(request.form, obj=shareholder)
    if form.validate_on_submit():
        form.populate_obj(shareholder)
        db.session.commit()
        flash(f'{page_title}を更新しました。', 'success')
        return redirect(url_for('company.shareholders'))
        
    if request.method == 'GET':
        form = ShareholderForm(obj=shareholder)

    navigation_state = get_navigation_state('shareholders')
    return render_template(
        'company/edit_shareholder.html', 
        form=form, 
        shareholder_id=shareholder.id, 
        navigation_state=navigation_state,
        page_title=page_title
    )

@company_bp.route('/shareholder/delete/<int:shareholder_id>', methods=['POST'])
@company_required
def delete_shareholder(company, shareholder_id):
    """株主/社員の削除"""
    page_title, response = get_page_title_and_check_redirect(company.company_name)
    if response:
        # 削除処理はGETリクエストを想定していないため、リダイレクトのみ
        return redirect(url_for('company.shareholders'))

    shareholder = Shareholder.query.filter_by(id=shareholder_id, company_id=company.id).first_or_404()
    db.session.delete(shareholder)
    db.session.commit()
    flash(f'{page_title}を削除しました。', 'success')
    return redirect(url_for('company.shareholders'))
