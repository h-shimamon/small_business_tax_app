# app/company/routes.py

import os
import pandas as pd
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, Blueprint, flash, current_app, session
from datetime import datetime
# ▼▼▼▼▼ TemporaryPaymentモデルをインポート ▼▼▼▼▼
from app.company.models import Company, Employee, Office, Deposit, NotesReceivable, AccountsReceivable, TemporaryPayment
# ▼▼▼▼▼ TemporaryPaymentFormをインポート ▼▼▼▼▼
from app.company.forms import (
    EmployeeForm, DeclarationForm, OfficeForm, 
    AccountingSelectionForm, DataMappingForm, FileUploadForm, 
    DepositForm, NotesReceivableForm, AccountsReceivableForm, TemporaryPaymentForm
)
from app import db
from wtforms import SelectField


company_bp = Blueprint(
    'company',
    __name__,
    template_folder='../templates',
    url_prefix='/company'
)

# --- (既存のルートは変更なし) ---
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
    # ... (フォームデータの処理) ...
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

@company_bp.route('/employees')
def employees():
    company = Company.query.first()
    employee_list = company.employees if company else []
    if not company:
        flash('会社情報が未登録のため、開発用の仮画面を表示しています。', 'warning')
    return render_template('company/employee_list.html', employees=employee_list)

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
    return render_template('company/register_employee.html', form=form)

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
    return render_template('company/edit_employee.html', form=form, employee_id=employee.id)

@company_bp.route('/employee/delete/<int:employee_id>', methods=['POST'])
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    flash('従業員を削除しました。', 'success')
    return redirect(url_for('company.employees'))

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
    return render_template('company/declaration_form.html', form=form)

@company_bp.route('/offices')
def office_list():
    company = Company.query.first()
    offices = company.offices if company else []
    if not company:
        flash('会社情報が未登録のため、開発用の仮画面を表示しています。', 'warning')
    return render_template('company/office_list.html', offices=offices)

@company_bp.route('/office/register', methods=['GET', 'POST'])
def register_office():
    company = Company.query.first()
    if not company:
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))
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
    office = Office.query.get_or_404(office_id)
    form = OfficeForm(obj=office)
    if form.validate_on_submit():
        form.populate_obj(office)
        db.session.commit()
        flash('事業所情報を更新しました。', 'success')
        return redirect(url_for('company.office_list'))
    return render_template('company/office_form.html', form=form, office=office)

@company_bp.route('/office/delete/<int:office_id>', methods=['POST'])
def delete_office(office_id):
    office = Office.query.get_or_404(office_id)
    db.session.delete(office)
    db.session.commit()
    flash('事業所を削除しました。', 'success')
    return redirect(url_for('company.office_list'))

def _process_file_upload(form, expected_headers, origin_url):
    """ファイルアップロードとヘッダー検証の共通処理"""
    file = form.upload_file.data
    filename = secure_filename(file.filename)
    
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'instance/uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    try:
        try:
            df_header = pd.read_csv(filepath, nrows=0, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df_header = pd.read_csv(filepath, nrows=0, encoding='shift_jis')
        
        actual_headers = df_header.columns.tolist()

        if set(actual_headers) == set(expected_headers):
            flash('ヘッダーは正常に検証されました。データ取り込み機能は現在開発中です (TODO)。', 'success')
            return True
        else:
            flash('ファイルヘッダーに不整合が見つかりました。項目を紐付けてください。', 'warning')
            session['mapping_filepath'] = filepath
            session['mismatched_headers'] = [h for h in actual_headers if h not in expected_headers]
            session['expected_candidates'] = [h for h in expected_headers if h not in actual_headers]
            session['mapping_origin_url'] = origin_url
            return True

    except Exception as e:
        flash(f'ファイルの読み込み中にエラーが発生しました: {e}', 'danger')
        if os.path.exists(filepath):
            os.remove(filepath)
        return False

@company_bp.route('/import_accounts', methods=['GET', 'POST'])
def import_accounts():
    """会計データ選択画面"""
    form = AccountingSelectionForm()
    if form.validate_on_submit():
        expected_headers = ['日付', '勘定科目', '補助科目', '摘要', '借方金額', '貸方金額']
        if _process_file_upload(form, expected_headers, url_for('company.import_accounts')):
            if 'mapping_filepath' in session:
                return redirect(url_for('company.data_mapping'))
            return redirect(url_for('company.import_accounts'))
    return render_template('company/import_accounts.html', form=form)

# --- (他のimportルートは変更なし) ---

@company_bp.route('/import_chart_of_accounts', methods=['GET', 'POST'])
def import_chart_of_accounts():
    """勘定科目取込ページ"""
    form = FileUploadForm()
    if form.validate_on_submit():
        expected_headers = ['科目コード', '科目名', '税区分']
        if _process_file_upload(form, expected_headers, url_for('company.import_chart_of_accounts')):
            if 'mapping_filepath' in session:
                return redirect(url_for('company.data_mapping'))
            return redirect(url_for('company.import_chart_of_accounts'))
    return render_template('company/import_chart_of_accounts.html', form=form)

@company_bp.route('/import_journals', methods=['GET', 'POST'])
def import_journals():
    """仕訳取込ページ"""
    form = FileUploadForm()
    if form.validate_on_submit():
        expected_headers = ['日付', '借方勘定科目', '貸方勘定科目', '金額', '摘要']
        if _process_file_upload(form, expected_headers, url_for('company.import_journals')):
            if 'mapping_filepath' in session:
                return redirect(url_for('company.data_mapping'))
            return redirect(url_for('company.import_journals'))
    return render_template('company/import_journals.html', form=form)

@company_bp.route('/import_fixed_assets', methods=['GET', 'POST'])
def import_fixed_assets():
    """固定資産取込ページ"""
    form = FileUploadForm()
    if form.validate_on_submit():
        expected_headers = ['資産名', '取得日', '取得価額', '耐用年数']
        if _process_file_upload(form, expected_headers, url_for('company.import_fixed_assets')):
            if 'mapping_filepath' in session:
                return redirect(url_for('company.data_mapping'))
            return redirect(url_for('company.import_fixed_assets'))
    return render_template('company/import_fixed_assets.html', form=form)


@company_bp.route('/data_mapping', methods=['GET', 'POST'])
def data_mapping():
    """ヘッダーの不整合をユーザーに修正させる画面"""
    origin_url = session.get('mapping_origin_url', url_for('company.import_accounts'))

    if 'mapping_filepath' not in session:
        flash('マッピング対象のファイルが見つかりません。もう一度アップロードしてください。', 'danger')
        return redirect(origin_url)

    mismatched = session.get('mismatched_headers', [])
    expected_candidates = session.get('expected_candidates', [])
    
    class DynamicMappingForm(DataMappingForm):
        pass

    for header in mismatched:
        field_name = f'map_{header.replace(" ", "_").replace("(", "").replace(")", "")}'
        choices = [('', '-----')] + [(h, h) for h in expected_candidates]
        field = SelectField(header, choices=choices)
        setattr(DynamicMappingForm, field_name, field)

    form = DynamicMappingForm(request.form)

    if form.validate_on_submit():
        filepath = session['mapping_filepath']
        try:
            mapping = {
                field.label.text: field.data
                for field in form if field.name.startswith('map_') and field.data
            }
            
            try:
                df = pd.read_csv(filepath, encoding='utf-8-sig')
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding='shift_jis')

            df.rename(columns=mapping, inplace=True)
            
            flash('データの紐付けが完了し、正常に処理されました。', 'success')
            # TODO: ここでdfを使ったデータベースへの保存処理などを行う

            os.remove(filepath)
            session.pop('mapping_filepath', None)
            session.pop('mismatched_headers', None)
            session.pop('expected_candidates', None)
            session.pop('mapping_origin_url', None)

            return redirect(origin_url)

        except Exception as e:
            flash(f'データ処理中にエラーが発生しました: {e}', 'danger')
            return redirect(origin_url)

    return render_template('company/data_mapping.html', form=form)

@company_bp.route('/statement_of_accounts')
def statement_of_accounts():
    """勘定科目内訳書ページ"""
    page = request.args.get('page', 'deposits')
    company = Company.query.first()
    
    context = {'page': page}

    if not company:
        flash('会社情報が未登録のため、機能を利用できません。', 'warning')
    else:
        if page == 'deposits':
            deposits = Deposit.query.filter_by(company_id=company.id).all()
            context['deposits'] = deposits
        elif page == 'notes_receivable':
            notes = NotesReceivable.query.filter_by(company_id=company.id).all()
            context['notes'] = notes
        elif page == 'accounts_receivable':
            receivables = AccountsReceivable.query.filter_by(company_id=company.id).all()
            context['receivables'] = receivables
        # ▼▼▼▼▼ ここから追加 ▼▼▼▼▼
        elif page == 'temporary_payments':
            payments = TemporaryPayment.query.filter_by(company_id=company.id).all()
            context['payments'] = payments
        # ▲▲▲▲▲ ここまで追加 ▲▲▲▲▲

    return render_template('company/statement_of_accounts.html', **context)


@company_bp.route('/deposit/add', methods=['GET', 'POST'])
def add_deposit():
    """預貯金の新規登録"""
    form = DepositForm()
    company = Company.query.first()
    if not company:
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))
    
    if form.validate_on_submit():
        new_deposit = Deposit(company_id=company.id)
        form.populate_obj(new_deposit)
        db.session.add(new_deposit)
        db.session.commit()
        flash('預貯金情報を登録しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='deposits'))
    
    return render_template('company/deposit_form.html', form=form, form_title="預貯金の新規登録")

@company_bp.route('/deposit/edit/<int:deposit_id>', methods=['GET', 'POST'])
def edit_deposit(deposit_id):
    """預貯金の編集"""
    deposit = Deposit.query.get_or_404(deposit_id)
    form = DepositForm(obj=deposit)
    
    if form.validate_on_submit():
        form.populate_obj(deposit)
        db.session.commit()
        flash('預貯金情報を更新しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='deposits'))
        
    return render_template('company/deposit_form.html', form=form, form_title="預貯金の編集")

@company_bp.route('/deposit/delete/<int:deposit_id>', methods=['POST'])
def delete_deposit(deposit_id):
    """預貯金の削除"""
    deposit = Deposit.query.get_or_404(deposit_id)
    db.session.delete(deposit)
    db.session.commit()
    flash('預貯金情報を削除しました。', 'success')
    return redirect(url_for('company.statement_of_accounts', page='deposits'))

# --- 受取手形のCRUD ---
@company_bp.route('/notes_receivable/add', methods=['GET', 'POST'])
def add_notes_receivable():
    """受取手形の新規登録"""
    form = NotesReceivableForm()
    company = Company.query.first()
    if not company:
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))
    
    if form.validate_on_submit():
        new_note = NotesReceivable(company_id=company.id)
        form.populate_obj(new_note)
        db.session.add(new_note)
        db.session.commit()
        flash('受取手形情報を登録しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='notes_receivable'))
    
    return render_template('company/notes_receivable_form.html', form=form, form_title="受取手形の新規登録")

@company_bp.route('/notes_receivable/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_notes_receivable(note_id):
    """受取手形の編集"""
    note = NotesReceivable.query.get_or_404(note_id)
    form = NotesReceivableForm(obj=note)
    
    if form.validate_on_submit():
        form.populate_obj(note)
        db.session.commit()
        flash('受取手形情報を更新しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='notes_receivable'))
        
    return render_template('company/notes_receivable_form.html', form=form, form_title="受取手形の編集")

@company_bp.route('/notes_receivable/delete/<int:note_id>', methods=['POST'])
def delete_notes_receivable(note_id):
    """受取手形の削除"""
    note = NotesReceivable.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    flash('受取手形情報を削除しました。', 'success')
    return redirect(url_for('company.statement_of_accounts', page='notes_receivable'))

# --- 売掛金（未収入金）のCRUD ---
@company_bp.route('/accounts_receivable/add', methods=['GET', 'POST'])
def add_accounts_receivable():
    """売掛金（未収入金）の新規登録"""
    form = AccountsReceivableForm()
    company = Company.query.first()
    if not company:
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))
    
    if form.validate_on_submit():
        new_receivable = AccountsReceivable(company_id=company.id)
        form.populate_obj(new_receivable)
        db.session.add(new_receivable)
        db.session.commit()
        flash('売掛金（未収入金）情報を登録しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='accounts_receivable'))
    
    return render_template('company/accounts_receivable_form.html', form=form, form_title="売掛金（未収入金）の新規登録")

@company_bp.route('/accounts_receivable/edit/<int:receivable_id>', methods=['GET', 'POST'])
def edit_accounts_receivable(receivable_id):
    """売掛金（未収入金）の編集"""
    receivable = AccountsReceivable.query.get_or_404(receivable_id)
    form = AccountsReceivableForm(obj=receivable)
    
    if form.validate_on_submit():
        form.populate_obj(receivable)
        db.session.commit()
        flash('売掛金（未収入金）情報を更新しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='accounts_receivable'))
        
    return render_template('company/accounts_receivable_form.html', form=form, form_title="売掛金（未収入金）の編集")

@company_bp.route('/accounts_receivable/delete/<int:receivable_id>', methods=['POST'])
def delete_accounts_receivable(receivable_id):
    """売掛金（未収入金）の削除"""
    receivable = AccountsReceivable.query.get_or_404(receivable_id)
    db.session.delete(receivable)
    db.session.commit()
    flash('売掛金（未収入金）情報を削除しました。', 'success')
    return redirect(url_for('company.statement_of_accounts', page='accounts_receivable'))

# ▼▼▼▼▼ ここから追加 ▼▼▼▼▼
# --- 仮払金（前渡金）のCRUD ---
@company_bp.route('/temporary_payment/add', methods=['GET', 'POST'])
def add_temporary_payment():
    """仮払金（前渡金）の新規登録"""
    form = TemporaryPaymentForm()
    company = Company.query.first()
    if not company:
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))
    
    if form.validate_on_submit():
        new_payment = TemporaryPayment(company_id=company.id)
        form.populate_obj(new_payment)
        db.session.add(new_payment)
        db.session.commit()
        flash('仮払金（前渡金）情報を登録しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='temporary_payments'))
    
    return render_template('company/temporary_payment_form.html', form=form, form_title="仮払金（前渡金）の新規登録")

@company_bp.route('/temporary_payment/edit/<int:payment_id>', methods=['GET', 'POST'])
def edit_temporary_payment(payment_id):
    """仮払金（前渡金）の編集"""
    payment = TemporaryPayment.query.get_or_404(payment_id)
    form = TemporaryPaymentForm(obj=payment)
    
    if form.validate_on_submit():
        form.populate_obj(payment)
        db.session.commit()
        flash('仮払金（前渡金）情報を更新しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='temporary_payments'))
        
    return render_template('company/temporary_payment_form.html', form=form, form_title="仮払金（前渡金）の編集")

@company_bp.route('/temporary_payment/delete/<int:payment_id>', methods=['POST'])
def delete_temporary_payment(payment_id):
    """仮払金（前渡金）の削除"""
    payment = TemporaryPayment.query.get_or_404(payment_id)
    db.session.delete(payment)
    db.session.commit()
    flash('仮払金（前渡金）情報を削除しました。', 'success')
    return redirect(url_for('company.statement_of_accounts', page='temporary_payments'))
# ▲▲▲▲▲ ここまで追加 ▲▲▲▲▲
