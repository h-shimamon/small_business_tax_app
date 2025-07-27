# app/company/routes.py

import os
import pandas as pd
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, Blueprint, flash, current_app, session
from datetime import datetime
from app.company.models import Company, Employee, Office
from app.company.forms import EmployeeForm, DeclarationForm, OfficeForm, AccountingSelectionForm, DataMappingForm
from app import db
from wtforms import SelectField


company_bp = Blueprint(
    'company',
    __name__,
    template_folder='../templates',
    url_prefix='/company'
)

# --- (既存のルートは変更なしのため省略) ---
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
    if not Company.query.first():
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))

    employee = Employee.query.get_or_404(employee_id)
    form = EmployeeForm(obj=employee)

    if request.method == 'GET' and employee.joined_date:
        if isinstance(employee.joined_date, str):
            try:
                form.joined_date.data = datetime.strptime(employee.joined_date, '%Y-%m-%d').date()
            except ValueError:
                form.joined_date.data = None

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

    if request.method == 'GET':
        form = DeclarationForm(obj=company)
        if company.accounting_period_start and isinstance(company.accounting_period_start, str):
            try:
                form.accounting_period_start.data = datetime.strptime(company.accounting_period_start, '%Y-%m-%d').date()
            except ValueError:
                form.accounting_period_start.data = None
        
        if company.accounting_period_end and isinstance(company.accounting_period_end, str):
            try:
                form.accounting_period_end.data = datetime.strptime(company.accounting_period_end, '%Y-%m-%d').date()
            except ValueError:
                form.accounting_period_end.data = None
        
        if company.closing_date and isinstance(company.closing_date, str):
            try:
                form.closing_date.data = datetime.strptime(company.closing_date, '%Y-%m-%d').date()
            except ValueError:
                form.closing_date.data = None
    else:
        form = DeclarationForm(request.form)

    if form.validate_on_submit():
        form.populate_obj(company)
        db.session.commit()
        flash('申告情報を更新しました。', 'success')
        return redirect(url_for('company.declaration'))

    return render_template('company/declaration_form.html', form=form)


@company_bp.route('/select_accounting', methods=['GET', 'POST'])
def select_accounting():
    """会計データ選択画面。ファイルアップロードとヘッダー検証を行う。"""
    form = AccountingSelectionForm()

    if form.validate_on_submit():
        file = form.upload_file.data
        filename = secure_filename(file.filename)
        
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        try:
            expected_headers = ['日付', '勘定科目', '補助科目', '摘要', '借方金額', '貸方金額']
            
            try:
                df_header = pd.read_csv(filepath, nrows=0, encoding='utf-8-sig')
            except UnicodeDecodeError:
                df_header = pd.read_csv(filepath, nrows=0, encoding='shift_jis')
            
            actual_headers = df_header.columns.tolist()

            matching_headers = set(actual_headers) & set(expected_headers)
            mismatched_headers = [h for h in actual_headers if h not in matching_headers]
            missing_expected = [h for h in expected_headers if h not in actual_headers]

            if not mismatched_headers and not missing_expected:
                flash('ファイルは正常に検証されました。データ取り込み処理に進みます。', 'success')
                # TODO: 本来のデータ取り込み処理
                # os.remove(filepath)
                return redirect(url_for('company.select_accounting'))
            else:
                flash('ファイルヘッダーに不整合が見つかりました。項目を紐付けてください。', 'warning')
                session['mapping_filepath'] = filepath
                session['mismatched_headers'] = mismatched_headers
                session['expected_candidates'] = missing_expected
                return redirect(url_for('company.data_mapping'))

        except Exception as e:
            flash(f'ファイルの読み込み中にエラーが発生しました: {e}', 'danger')
            if os.path.exists(filepath):
                os.remove(filepath)
            return redirect(url_for('company.select_accounting'))

    return render_template('company/select_accounting.html', form=form)

# ▼▼▼▼▼ データマッピング画面のルートを完全に実装 ▼▼▼▼▼
@company_bp.route('/data_mapping', methods=['GET', 'POST'])
def data_mapping():
    """ヘッダーの不整合をユーザーに修正させる画面"""
    # セッションに必要な情報がなければ、開始ページにリダイレクト
    if 'mapping_filepath' not in session:
        flash('マッピング対象のファイルが見つかりません。もう一度アップロードしてください。', 'danger')
        return redirect(url_for('company.select_accounting'))

    mismatched = session.get('mismatched_headers', [])
    expected_candidates = session.get('expected_candidates', [])
    
    # 動的にフォームを構築
    class DynamicMappingForm(DataMappingForm):
        pass

    for header in mismatched:
        # フィールド名はPythonの変数として使えるようにサニタイズ
        field_name = f'map_{header.replace(" ", "_").replace("(", "").replace(")", "")}'
        choices = [('', '-----')] + [(h, h) for h in expected_candidates]
        field = SelectField(header, choices=choices)
        setattr(DynamicMappingForm, field_name, field)

    form = DynamicMappingForm(request.form)

    if form.validate_on_submit():
        filepath = session['mapping_filepath']
        try:
            # ユーザーが指定したマッピング情報を取得
            mapping = {}
            for field in form:
                if field.name.startswith('map_'):
                    original_header = field.label.text
                    mapped_header = field.data
                    if mapped_header: # 空欄は無視
                        mapping[original_header] = mapped_header
            
            # 文字コードを判定しながらCSVを読み込み、ヘッダー名を変更
            try:
                df = pd.read_csv(filepath, encoding='utf-8-sig')
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding='shift_jis')

            df.rename(columns=mapping, inplace=True)
            
            # TODO: ここでdfを使ったデータベースへの保存処理などを行う
            
            flash('データの紐付けが完了し、正常に処理されました。', 'success')

            # 処理が完了したのでセッションと一時ファイルをクリーンアップ
            os.remove(filepath)
            session.pop('mapping_filepath', None)
            session.pop('mismatched_headers', None)
            session.pop('expected_candidates', None)

            return redirect(url_for('company.select_accounting'))

        except Exception as e:
            flash(f'データ処理中にエラーが発生しました: {e}', 'danger')
            return redirect(url_for('company.select_accounting'))

    return render_template('company/data_mapping.html', form=form)
# ▲▲▲▲▲ ここまで実装 ▲▲▲▲▲


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
