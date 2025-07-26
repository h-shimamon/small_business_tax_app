# app/company/routes.py

from flask import render_template, request, redirect, url_for, Blueprint, flash
from datetime import datetime
from app.company.models import Company, Employee, Office
from app.company.forms import EmployeeForm, DeclarationForm, OfficeForm
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
    """基本情報ページのトップ。"""
    company = Company.query.first()
    return render_template('register.html', company=company)


@company_bp.route('/save', methods=['POST'])
def save():
    """フォームから送信されたデータを保存（新規登録または更新）する。"""
    company = Company.query.first()
    if not company:
        company = Company()

    # request.formからデータを取得してcompanyオブジェクトに設定
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


# --- 社員名簿関連 ---

@company_bp.route('/employees')
def employees():
    """社員名簿ページ。"""
    company = Company.query.first()
    employee_list = []
    if company:
        employee_list = company.employees
    else:
        flash('会社情報が未登録のため、開発用の仮画面を表示しています。', 'warning')
    return render_template('company/employee_list.html', employees=employee_list)


@company_bp.route('/employee/register', methods=['GET', 'POST'])
def register_employee():
    """新規従業員登録"""
    company = Company.query.first()
    if not company:
        if request.method == 'POST':
            flash('先に会社の基本情報を登録してください。', 'error')
            return redirect(url_for('company.show'))
        
        form = EmployeeForm()
        flash('会社情報が未登録のため、開発用の仮画面を表示しています。入力内容は保存されません。', 'warning')
        return render_template('company/register_employee.html', form=form)
        
    form = EmployeeForm(request.form)
    if form.validate_on_submit():
        new_employee = Employee(company_id=company.id)
        form.populate_obj(new_employee)
        db.session.add(new_employee)
        db.session.commit()
        flash('従業員を登録しました。', 'success')
        return redirect(url_for('company.employees'))
    return render_template('company/register_employee.html', form=form)


@company_bp.route('/employee/edit/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    """従業員情報の編集"""
    # 既存のチェック処理はそのまま
    if not Company.query.first():
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))

    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm(obj=employee)

    # ▼▼▼▼▼ ここからが修正の核心部です ▼▼▼▼▼
    # 画面表示時(GETリクエスト)に、DBから読み込んだ日付データが
    # 文字列だった場合、日付オブジェクトに変換します。
    # これによりテンプレートでの 'strftime' エラーを防ぎます。
    if request.method == 'GET' and employee.joined_date:
        if isinstance(employee.joined_date, str):
            try:
                form.joined_date.data = datetime.strptime(employee.joined_date, '%Y-%m-%d').date()
            except ValueError:
                form.joined_date.data = None # 念のため変換失敗時も考慮
    # ▲▲▲▲▲ ここまでが修正の核心部です ▲▲▲▲▲

    if form.validate_on_submit():
        form.populate_obj(employee)
        db.session.commit()
        flash('従業員情報を更新しました。', 'success')
        return redirect(url_for('company.employees'))
        
    return render_template('company/edit_employee.html', form=form, employee_id=employee.id)
@company_bp.route('/employee/delete/<int:employee_id>', methods=['POST'])
def delete_employee(employee_id):
    """従業員の削除"""
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    flash('従業員を削除しました。', 'success')
    return redirect(url_for('company.employees'))


# --- 申告情報 ---

@company_bp.route('/declaration', methods=['GET', 'POST'])
def declaration():
    """申告情報ページ"""
    company = Company.query.first()
    if not company:
        if request.method == 'POST':
            flash('先に会社の基本情報を登録してください。', 'error')
            return redirect(url_for('company.show'))
        
        form = DeclarationForm()
        flash('会社情報が未登録のため、開発用の仮画面を表示しています。入力内容は保存されません。', 'warning')
        return render_template('company/declaration_form.html', form=form)

    # GETリクエストの場合、DBオブジェクトからフォームを生成
    if request.method == 'GET':
        form = DeclarationForm(obj=company)
        # DBから読み込んだ日付データが文字列の場合、日付オブジェクトに変換する
        if company.accounting_period_start and isinstance(company.accounting_period_start, str):
            try:
                form.accounting_period_start.data = datetime.strptime(company.accounting_period_start, '%Y-%m-%d').date()
            except ValueError:
                form.accounting_period_start.data = None # 変換失敗時はNone
        
        if company.accounting_period_end and isinstance(company.accounting_period_end, str):
            try:
                form.accounting_period_end.data = datetime.strptime(company.accounting_period_end, '%Y-%m-%d').date()
            except ValueError:
                form.accounting_period_end.data = None # 変換失敗時はNone
        
        # ▼▼▼▼▼ 新しく追加した修正箇所です ▼▼▼▼▼
        if company.closing_date and isinstance(company.closing_date, str):
            try:
                form.closing_date.data = datetime.strptime(company.closing_date, '%Y-%m-%d').date()
            except ValueError:
                form.closing_date.data = None # 変換失敗時はNone
        # ▲▲▲▲▲ 新しく追加した修正箇所です ▲▲▲▲▲

    # POSTリクエストの場合、フォームデータからフォームを生成
    else:
        form = DeclarationForm(request.form)

    if form.validate_on_submit():
        form.populate_obj(company)
        db.session.commit()
        flash('申告情報を更新しました。', 'success')
        return redirect(url_for('company.declaration'))

    # フォームを表示（GET時、またはPOSTでバリデーションエラー時）
    return render_template('company/declaration_form.html', form=form)

# --- 事業所 (Office) 関連 ---

@company_bp.route('/offices')
def office_list():
    """事業所の一覧ページ"""
    company = Company.query.first()
    office_list = []
    if company:
        office_list = company.offices
    else:
        flash('会社情報が未登録のため、開発用の仮画面を表示しています。', 'warning')
    return render_template('company/office_list.html', offices=office_list)


@company_bp.route('/office/register', methods=['GET', 'POST'])
def register_office():
    """新規事業所の登録"""
    company = Company.query.first()
    if not company:
        if request.method == 'POST':
            flash('先に会社の基本情報を登録してください。', 'error')
            return redirect(url_for('company.show'))
        
        form = OfficeForm()
        flash('会社情報が未登録のため、開発用の仮画面を表示しています。入力内容は保存されません。', 'warning')
        return render_template('company/office_form.html', form=form)

    form = OfficeForm(request.form)
    if form.validate_on_submit():
        new_office = Office(company_id=company.id)
        form.populate_obj(new_office)
        db.session.add(new_office)
        db.session.commit()
        flash('事業所を登録しました。', 'success')
        return redirect(url_for('company.office_list'))
    return render_template('company/office_form.html', form=form)


@company_bp.route('/office/edit/<int:office_id>', methods=['GET', 'POST'])
def edit_office(office_id):
    """事業所情報の編集"""
    if not Company.query.first():
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))

    office = Office.query.get_or_404(office_id)
    form = OfficeForm(request.form, obj=office)
    if form.validate_on_submit():
        form.populate_obj(office)
        db.session.commit()
        flash('事業所情報を更新しました。', 'success')
        return redirect(url_for('company.office_list'))
    return render_template('company/office_form.html', form=form, office=office)


@company_bp.route('/office/delete/<int:office_id>', methods=['POST'])
def delete_office(office_id):
    """事業所の削除"""
    office = Office.query.get_or_404(office_id)
    db.session.delete(office)
    db.session.commit()
    flash('事業所を削除しました。', 'success')
    return redirect(url_for('company.office_list'))
