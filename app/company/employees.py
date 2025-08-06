# app/company/employees.py
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required
from app.company import company_bp
from app.company.models import Company, Employee
from app.company.forms import EmployeeForm
from app import db
from app.utils import get_navigation_state
from datetime import date

def _get_or_create_dev_company():
    """
    DBから会社情報を取得する。
    会社情報が存在せず、かつ開発モード(app.debug is True)の場合、
    ダミーの会社情報を自動で作成して返す。
    本番モードで会社情報が存在しない場合はNoneを返す。
    """
    company = Company.query.first()
    if company:
        return company

    if not current_app.debug:
        return None

    # 開発モードで会社が存在しない場合、ダミーデータを作成
    flash('開発用のダミー会社情報を作成しました。', 'info')
    dummy_company = Company(
        corporate_number="1234567890123",
        company_name="ダミー株式会社",
        company_name_kana="ダミーカブシキガイシャ",
        zip_code="1000001",
        prefecture="東京都",
        city="千代田区",
        address="丸の内1-1",
        phone_number="03-1234-5678",
        establishment_date=date(2020, 1, 1)
    )
    db.session.add(dummy_company)
    db.session.commit()
    return dummy_company

@company_bp.route('/employees')
@login_required
def employees():
    company = _get_or_create_dev_company()
    employee_list = company.employees if company else []
    if not company:
        # 本番環境で会社情報がない場合
        flash('先に会社の基本情報を登録してください。', 'warning')
        return redirect(url_for('company.show'))
    
    navigation_state = get_navigation_state('employees')
    return render_template('company/employee_list.html', employees=employee_list, navigation_state=navigation_state)

@company_bp.route('/employee/register', methods=['GET', 'POST'])
@login_required
def register_employee():
    company = _get_or_create_dev_company()
    if not company:
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))
        
    form = EmployeeForm(request.form)
    if form.validate_on_submit():
        new_employee = Employee(company_id=company.id)
        # form.populate_obj(new_employee) # この行を削除
        # 手動で各フィールドをマッピング
        new_employee.last_name = form.last_name.data
        new_employee.first_name = form.first_name.data
        new_employee.is_officer = form.is_officer.data
        new_employee.joined_date = form.joined_date.data if form.joined_date.data else None
        new_employee.relationship = form.relationship.data
        new_employee.address = form.address.data
        new_employee.shares_held = form.shares_held.data
        new_employee.voting_rights = form.voting_rights.data
        new_employee.officer_position = form.officer_position.data
        db.session.add(new_employee)
        db.session.commit()
        flash('従業員を登録しました。', 'success')
        return redirect(url_for('company.employees'))
        
    navigation_state = get_navigation_state('employees')
    return render_template('company/register_employee.html', form=form, navigation_state=navigation_state)

@company_bp.route('/employee/edit/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    """従業員情報の編集"""
    company = _get_or_create_dev_company()
    if not company:
        flash('会社の基本情報が見つかりません。', 'error')
        return redirect(url_for('company.show'))

    employee = Employee.query.get_or_404(employee_id)
    # 念のため、他の会社の従業員を編集できないようにチェック
    if employee.company_id != company.id:
        flash('アクセス権限がありません。', 'error')
        return redirect(url_for('company.employees'))

    form = EmployeeForm(obj=employee)
    if form.validate_on_submit():
        # form.populate_obj(employee) # この行を削除
        # 手動で各フィールドをマッピング
        employee.last_name = form.last_name.data
        employee.first_name = form.first_name.data
        employee.last_name_kana = form.last_name_kana.data
        employee.first_name_kana = form.first_name_kana.data
        employee.is_officer = form.is_officer.data
        employee.joined_date = form.joined_date.data if form.joined_date.data else None
        employee.relationship = form.relationship.data
        employee.address = form.address.data
        employee.shares_held = form.shares_held.data
        employee.voting_rights = form.voting_rights.data
        employee.officer_position = form.officer_position.data
        db.session.commit()
        flash('従業員情報を更新しました。', 'success')
        return redirect(url_for('company.employees'))
        
    navigation_state = get_navigation_state('employees')
    return render_template('company/edit_employee.html', form=form, employee_id=employee.id, navigation_state=navigation_state)

@company_bp.route('/employee/delete/<int:employee_id>', methods=['POST'])
@login_required
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    flash('従業員を削除しました。', 'success')
    return redirect(url_for('company.employees'))