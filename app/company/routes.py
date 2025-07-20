# app/company/routes.py

from flask import render_template, request, redirect, url_for, Blueprint, flash
from datetime import datetime
from app.company.models import Company, Employee
# ▼▼▼ DeclarationForm をインポートします ▼▼▼
from app.company.forms import EmployeeForm, DeclarationForm
from app import db

# Blueprintを定義。このファイル内のルートは全て /company が先頭に付く
company_bp = Blueprint(
    'company',
    __name__,
    template_folder='../templates', # テンプレートフォルダの場所を正しく指定
    url_prefix='/company'
)


@company_bp.route('/')
def show():
    """
    基本情報ページのトップ。
    データベースから会社情報を取得し、フォームに表示する。
    GETリクエスト用。
    """
    company = Company.query.first()
    return render_template('register.html', company=company)


@company_bp.route('/save', methods=['POST'])
def save():
    """
    フォームから送信されたデータを保存（新規登録または更新）する。
    POSTリクエスト用。
    """
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
    # チェックボックスの処理を修正
    company.capital_limit = 'capital_limit' in request.form
    company.is_supported_industry = 'is_supported_industry' in request.form
    company.is_not_excluded_business = 'is_not_excluded_business' in request.form
    company.industry_type = request.form.get('industry_type')
    company.industry_code = request.form.get('industry_code')
    company.reference_number = request.form.get('reference_number')

    db.session.add(company)
    db.session.commit()

    return redirect(url_for('company.show'))


@company_bp.route('/employees')
def employees():
    """
    社員名簿ページ。
    データベースから社員の一覧を取得して表示する。
    """
    company = Company.query.first()
    employee_list = []
    if company:
        employee_list = company.employees

    return render_template(
        'company/employee_list.html',
        employees=employee_list
    )

# ▼▼▼▼▼ declaration ルートを以下のように全面的に更新します ▼▼▼▼▼
@company_bp.route('/declaration', methods=['GET', 'POST'])
def declaration():
    """
    GET: 申告情報ページを表示
    POST: 入力された申告情報を保存
    """
    company = Company.query.first()
    if not company:
        # 会社情報が未登録の場合は基本情報ページへリダイレクト
        flash('最初に会社の基本情報を登録してください。', 'info')
        return redirect(url_for('company.show'))

    # DeclarationForm をインスタンス化
    # POST時はフォームからのデータで、GET時はDBのデータ(obj=company)で初期化
    form = DeclarationForm(request.form, obj=company)

    if form.validate_on_submit():
        # フォームのデータをDBオブジェクトに一括でセット
        form.populate_obj(company)
        db.session.commit()
        flash('申告情報を更新しました。', 'success')
        return redirect(url_for('company.declaration'))

    # GETリクエスト時、またはPOSTでバリデーションエラーがあった場合
    return render_template('company/declaration_form.html', form=form)
# ▲▲▲▲▲ ここまで更新 ▲▲▲▲▲


@company_bp.route('/employee/register', methods=['GET', 'POST'])
def register_employee():
    """
    GET: 新規従業員登録ページを表示
    POST: 入力された従業員情報を保存
    """
    form = EmployeeForm(request.form)

    if form.validate_on_submit():
        company = Company.query.first()
        if not company:
            return redirect(url_for('company.show'))

        new_employee = Employee(
            name=form.name.data,
            group=form.group.data,
            joined_date=form.joined_date.data,
            relationship=form.relationship.data,
            address=form.address.data,
            shares_held=form.shares_held.data,
            voting_rights=form.voting_rights.data,
            position=form.position.data,
            investment_amount=form.investment_amount.data,
            company_id=company.id
        )

        db.session.add(new_employee)
        db.session.commit()

        return redirect(url_for('company.employees'))

    return render_template('company/register_employee.html', form=form)


@company_bp.route('/employee/edit/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    """
    GET: 既存の従業員情報を編集ページに表示
    POST: 更新された従業員情報を保存
    """
    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm(request.form, obj=employee)

    if form.validate_on_submit():
        form.populate_obj(employee)
        db.session.commit()
        return redirect(url_for('company.employees'))

    if isinstance(employee.joined_date, str):
        try:
            form.joined_date.data = datetime.strptime(employee.joined_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            form.joined_date.data = None

    return render_template('company/edit_employee.html', form=form)


@company_bp.route('/employee/delete/<int:employee_id>', methods=['POST'])
def delete_employee(employee_id):
    """
    指定された従業員を削除
    """
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    return redirect(url_for('company.employees'))
