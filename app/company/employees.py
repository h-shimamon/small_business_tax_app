# app/company/employees.py
from flask import render_template, request, redirect, url_for, flash
from app.company import company_bp
from app.company.models import Employee
from app.company.forms import EmployeeForm
from app import db
from app.navigation import get_navigation_state
from .auth import company_required

@company_bp.route('/employees')
@company_required
def employees(company):
    """社員名簿の一覧ページ"""
    employee_list = company.employees
    navigation_state = get_navigation_state('employees')
    return render_template('company/employee_list.html', employees=employee_list, navigation_state=navigation_state)

@company_bp.route('/employee/register', methods=['GET', 'POST'])
@company_required
def register_employee(company):
    """社員の新規登録"""
    form = EmployeeForm(request.form)
    if form.validate_on_submit():
        new_employee = Employee(company_id=company.id)
        form.populate_obj(new_employee)
        db.session.add(new_employee)
        db.session.commit()
        flash('従業員を登録しました。', 'success')
        return redirect(url_for('company.employees'))
        
    navigation_state = get_navigation_state('employees')
    return render_template('company/register_employee.html', form=form, navigation_state=navigation_state)

@company_bp.route('/employee/edit/<int:employee_id>', methods=['GET', 'POST'])
@company_required
def edit_employee(company, employee_id):
    """従業員情報の編集"""
    # ログインユーザーの会社に紐づく従業員のみを取得
    employee = Employee.query.filter_by(id=employee_id, company_id=company.id).first_or_404()
    
    form = EmployeeForm(request.form, obj=employee)
    if form.validate_on_submit():
        form.populate_obj(employee)
        db.session.commit()
        flash('従業員情報を更新しました。', 'success')
        return redirect(url_for('company.employees'))
        
    # GETリクエストの場合は、DBから取得した情報をフォームに設定
    if request.method == 'GET':
        form = EmployeeForm(obj=employee)

    navigation_state = get_navigation_state('employees')
    return render_template('company/edit_employee.html', form=form, employee_id=employee.id, navigation_state=navigation_state)

@company_bp.route('/employee/delete/<int:employee_id>', methods=['POST'])
@company_required
def delete_employee(company, employee_id):
    """従業員の削除"""
    # ログインユーザーの会社に紐づく従業員のみを削除対象とする
    employee = Employee.query.filter_by(id=employee_id, company_id=company.id).first_or_404()
    db.session.delete(employee)
    db.session.commit()
    flash('従業員を削除しました。', 'success')
    return redirect(url_for('company.employees'))
