# app/company/import_data.py

import os
import pandas as pd
from werkzeug.utils import secure_filename
from flask import render_template, redirect, url_for, flash, current_app, session, request
from wtforms import SelectField
from app.company import company_bp
from app.company.forms import AccountingSelectionForm, DataMappingForm, FileUploadForm
from app import db

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
    return render_template('import_accounts.html', form=form)

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
    return render_template('import_chart_of_accounts.html', form=form)

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
    return render_template('import_journals.html', form=form)

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
    return render_template('import_fixed_assets.html', form=form)

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

    return render_template('data_mapping.html', form=form)