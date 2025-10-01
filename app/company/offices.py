# app/company/offices.py
from flask import flash, redirect, render_template, request, url_for

from app.company import company_bp
from app.company.forms import OfficeForm
from app.company.models import Office
from app.extensions import db
from app.navigation import get_navigation_state

from .auth import company_required


@company_bp.route('/offices')
@company_required
def office_list(company):
    """事業所の一覧ページ"""
    offices = company.offices
    navigation_state = get_navigation_state('office_list')
    return render_template('company/office_list.html', offices=offices, navigation_state=navigation_state)

@company_bp.route('/office/register', methods=['GET', 'POST'])
@company_required
def register_office(company):
    """事業所の新規登録"""
    form = OfficeForm(request.form)
    if form.validate_on_submit():
        new_office = Office(company_id=company.id)
        form.populate_obj(new_office)
        db.session.add(new_office)
        db.session.commit()
        flash('事業所を登録しました。', 'success')
        return redirect(url_for('company.office_list'))
        
    navigation_state = get_navigation_state('office_list')
    return render_template('company/office_form.html', form=form, navigation_state=navigation_state)

@company_bp.route('/office/edit/<int:office_id>', methods=['GET', 'POST'])
@company_required
def edit_office(company, office_id):
    """事業所情報の編集"""
    # ログインユーザーの会社に紐づく事業所のみを取得
    office = Office.query.filter_by(id=office_id, company_id=company.id).first_or_404()
    
    form = OfficeForm(request.form, obj=office)
    if form.validate_on_submit():
        form.populate_obj(office)
        db.session.commit()
        flash('事業所情報を更新しました。', 'success')
        return redirect(url_for('company.office_list'))
        
    if request.method == 'GET':
        form = OfficeForm(obj=office)

    navigation_state = get_navigation_state('office_list')
    return render_template('company/office_form.html', form=form, office=office, navigation_state=navigation_state)

@company_bp.route('/office/delete/<int:office_id>', methods=['POST'])
@company_required
def delete_office(company, office_id):
    """事業所の削除"""
    # ログインユーザーの会社に紐づく事業所のみを削除対象とする
    office = Office.query.filter_by(id=office_id, company_id=company.id).first_or_404()
    db.session.delete(office)
    db.session.commit()
    flash('事業所を削除しました。', 'success')
    return redirect(url_for('company.office_list'))
