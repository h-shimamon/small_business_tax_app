# app/company/offices.py

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.company import company_bp
from app.company.models import Company, Office
from app.company.forms import OfficeForm
from app import db

@company_bp.route('/offices')
@login_required
def office_list():
    company = Company.query.first()
    offices = company.offices if company else []
    if not company:
        flash('会社情報が未登録のため、開発用の仮画面を表示しています。', 'warning')
    return render_template('office_list.html', offices=offices)

@company_bp.route('/office/register', methods=['GET', 'POST'])
@login_required
def register_office():
    company = Company.query.first()
    # if not company:
    #     flash('先に会社の基本情報を登録してください。', 'error')
    #     return redirect(url_for('company.show'))
        
    form = OfficeForm(request.form)
    if form.validate_on_submit():
        new_office = Office(company_id=company.id)
        form.populate_obj(new_office)
        db.session.add(new_office)
        db.session.commit()
        flash('事業所を登録しました。', 'success')
        return redirect(url_for('company.office_list'))
        
    return render_template('office_form.html', form=form)

@company_bp.route('/office/edit/<int:office_id>', methods=['GET', 'POST'])
@login_required
def edit_office(office_id):
    """事業所情報の編集"""
    office = Office.query.get_or_404(office_id)
    form = OfficeForm(obj=office)
    if form.validate_on_submit():
        form.populate_obj(office)
        db.session.commit()
        flash('事業所情報を更新しました。', 'success')
        return redirect(url_for('company.office_list'))
        
    return render_template('office_form.html', form=form, office=office)

@company_bp.route('/office/delete/<int:office_id>', methods=['POST'])
@login_required
def delete_office(office_id):
    office = Office.query.get_or_404(office_id)
    db.session.delete(office)
    db.session.commit()
    flash('事業所を削除しました。', 'success')
    return redirect(url_for('company.office_list'))
