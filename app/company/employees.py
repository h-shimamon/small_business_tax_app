# app/company/employees.py

from flask import render_template, request, redirect, url_for, flash
from app.company import company_bp
from app.company.models import Company, Employee
from app.company.forms import EmployeeForm
from app import db

@company_bp.route('/employees')
def employees():
    company = Company.query.first()
    employee_list = company.employees if company else []
    if not company:
        flash('会社情報が未登録のため、開発用の仮画面を表示しています。', 'warning')
    return render_template('employee_list.html', employees=employee_list)

@company_bp.route('/employee/register', methods=['GET', 'POST'])
def register_employee():
    company = Company.query.first()
    if not company:
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))
        
    form = EmployeeForm(request.form)
    if form.validate_on_submit():
        new_employee = Employee(company_id=company.id)
        form.populate_obj(new_employee)
        db.session.add(new_employee)
        db.session.commit()
        flash('従業員を登録しました。', 'success')
        return redirect(url_for('company.employees'))
        
    return render_template('register_employee.html', form=form)

@company_bp.route('/employee/edit/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    """従業員情報の編集"""
    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm(obj=employee)
    if form.validate_on_submit():
        form.populate_obj(employee)
        db.session.commit()
        flash('従業員情報を更新しました。', 'success')
        return redirect(url_for('company.employees'))
        
    return render_template('edit_employee.html', form=form, employee_id=employee.id)

@company_bp.route('/employee/delete/<int:employee_id>', methods=['POST'])
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    flash('従業員を削除しました。', 'success')
    return redirect(url_for('company.employees'))