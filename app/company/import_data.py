# app/company/import_data.py

import os
import pandas as pd
from werkzeug.utils import secure_filename
from flask import render_template, redirect, url_for, flash, current_app, session, request
from wtforms import SelectField
from app.company import company_bp
from app.company.forms import DataMappingForm, FileUploadForm, SoftwareSelectionForm
from app import db

# データタイプごとの設定を定義
DATA_TYPE_CONFIG = {
    'chart_of_accounts': {
        'title': '勘定科目設定のインポート',
        'description': 'まず初めに、勘定科目の一覧をCSV形式でアップロードしてください。これは全ての会計処理の基礎となります。',
        'expected_headers': ['科目コード', '科目名', '税区分'],
        'guide_text_data_type': '勘定科目一覧',
        'step_name': '勘定科目'
    },
    'journals': {
        'title': '仕訳帳のインポート',
        'description': '次に、会計期間中のすべての取引が記録された仕訳帳のCSVファイルをアップロードしてください。',
        'expected_headers': ['日付', '借方勘定科目', '貸方勘定科目', '金額', '摘要'],
        'guide_text_data_type': '仕訳帳',
        'step_name': '仕訳帳'
    },
    'fixed_assets': {
        'title': '固定資産台帳のインポート',
        'description': '最後に、固定資産台帳をCSV形式でアップロードしてください。',
        'expected_headers': ['資産名', '取得日', '取得価額', '耐用年数'],
        'guide_text_data_type': '固定資産台帳',
        'step_name': '固定資産'
    }
}

# ウィザードのステップを定義
FILE_UPLOAD_STEPS = ['chart_of_accounts', 'journals', 'fixed_assets']

@company_bp.route('/select_software', methods=['GET', 'POST'])
def select_software():
    """会計ソフトを選択し、ウィザードを開始するページ"""
    form = SoftwareSelectionForm()

    # ウィザードのステップ情報をテンプレートに渡す
    wizard_steps_info = [
        {'key': 'select_software', 'name': '会計ソフト選択', 'is_current': True, 'is_completed': False},
        {'key': 'chart_of_accounts', 'name': DATA_TYPE_CONFIG['chart_of_accounts']['step_name'], 'is_current': False, 'is_completed': False},
        {'key': 'journals', 'name': DATA_TYPE_CONFIG['journals']['step_name'], 'is_current': False, 'is_completed': False},
        {'key': 'fixed_assets', 'name': DATA_TYPE_CONFIG['fixed_assets']['step_name'], 'is_current': False, 'is_completed': False},
    ]

    if form.validate_on_submit():
        session['selected_software'] = form.accounting_software.data
        session['wizard_completed_steps'] = [] # 新しいウィザードを開始
        flash(f'{form.accounting_software.label.text}が選択されました。', 'info')
        return redirect(url_for('company.data_upload_wizard'))
    return render_template('company/select_software.html', form=form, wizard_progress=wizard_steps_info)

@company_bp.route('/data_upload_wizard', methods=['GET'])
def data_upload_wizard():
    """
    ファイルアップロードウィザードの進行を管理する。
    """
    if 'selected_software' not in session:
        flash('最初に会計ソフトを選択してください。', 'warning')
        return redirect(url_for('company.select_software'))

    completed_steps = session.get('wizard_completed_steps', [])
    
    next_step = None
    for step in FILE_UPLOAD_STEPS:
        if step not in completed_steps:
            next_step = step
            break
            
    if next_step:
        return redirect(url_for('company.upload_data', datatype=next_step))
    else:
        flash('すべてのファイルのアップロードが完了しました。', 'success')
        session.pop('wizard_completed_steps', None)
        session.pop('selected_software', None)
        return redirect(url_for('company.statement_of_accounts'))

def _handle_successful_upload(origin_url, datatype):
    """アップロード成功時の共通処理"""
    completed_steps = session.get('wizard_completed_steps', [])
    if datatype not in completed_steps:
        completed_steps.append(datatype)
    session['wizard_completed_steps'] = completed_steps
    return redirect(url_for('company.data_upload_wizard'))

def _process_file_upload(form, expected_headers, origin_url, datatype): # datatype引数を追加
    """ファイルアップロードとヘッダー検証の共通処理"""
    file = form.upload_file.data
    if not file:
        flash('ファイルが選択されていません。', 'danger')
        return False

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
            flash('ヘッダーは正常に検証されました。データ取り込み機能は現在開発中です (TODO)。', 'info')
            # TODO: データベースへの保存処理
            if os.path.exists(filepath):
                os.remove(filepath)
            
            _handle_successful_upload(origin_url, datatype)
            return True # リダイレクトは_handle_successful_upload内で行われる

        else:
            flash('ファイルヘッダーに不整合が見つかりました。項目を紐付けてください。', 'warning')
            session['mapping_filepath'] = filepath
            session['mismatched_headers'] = [h for h in actual_headers if h not in expected_headers]
            session['expected_candidates'] = [h for h in expected_headers if h not in actual_headers]
            session['mapping_origin_url'] = origin_url
            session['mapping_datatype'] = datatype # マッピング後どのステップか判断するためにdatatypeを保存
            return True

    except Exception as e:
        flash(f'ファイルの読み込み中にエラーが発生しました: {e}', 'danger')
        if os.path.exists(filepath):
            os.remove(filepath)
        return False

@company_bp.route('/upload/<datatype>', methods=['GET', 'POST'])
def upload_data(datatype):
    """
    データアップロードの共通ルート。
    datatypeに応じて、タイトル、説明、期待されるヘッダーを動的に設定する。
    """
    config = DATA_TYPE_CONFIG.get(datatype)
    if not config:
        flash('無効なデータタイプです。', 'danger')
        return redirect(url_for('company.data_upload_wizard'))

    # URL直接アクセスによるステップのスキップを防止
    completed_steps = session.get('wizard_completed_steps', [])
    current_step_index = FILE_UPLOAD_STEPS.index(datatype)
    
    # 現在のステップより前のステップが完了しているかチェック
    for i in range(current_step_index):
        if FILE_UPLOAD_STEPS[i] not in completed_steps:
            flash('前のステップを先に完了してください。', 'warning')
            return redirect(url_for('company.data_upload_wizard'))

    form = FileUploadForm()
    if form.validate_on_submit():
        origin_url = url_for('company.upload_data', datatype=datatype)
        if _process_file_upload(form, config['expected_headers'], origin_url, datatype):
            if 'mapping_filepath' in session:
                return redirect(url_for('company.data_mapping'))
            return redirect(url_for('company.data_upload_wizard'))

    # Alpine.jsのガイドで使うテキストを生成
    config['guide_text_required_columns'] = ', '.join(config['expected_headers'])
    
    # ウィザードの進捗情報をテンプレートに渡す
    wizard_progress = [
        {'key': 'select_software', 'name': '会計ソフト選択', 'is_current': False, 'is_completed': True}
    ]
    completed_steps = session.get('wizard_completed_steps', [])
    for step in FILE_UPLOAD_STEPS:
        wizard_progress.append({
            'key': step,
            'name': DATA_TYPE_CONFIG[step]['step_name'],
            'is_completed': step in completed_steps,
            'is_current': step == datatype
        })

    selected_software = session.get('selected_software', 'other')

    return render_template(
        'company/upload_data.html', 
        form=form,
        datatype=datatype,
        wizard_progress=wizard_progress,
        selected_software=selected_software,
        **config
    )

@company_bp.route('/data_mapping', methods=['GET', 'POST'])
def data_mapping():
    """ヘッダーの不整合をユーザーに修正させる画面"""
    datatype = session.get('mapping_datatype', 'chart_of_accounts')
    origin_url = session.get('mapping_origin_url', url_for('company.upload_data', datatype=datatype))

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
            session.pop('mapping_datatype', None)

            # アップロード成功処理を呼び出し、ウィザードを次に進める
            return _handle_successful_upload(origin_url, datatype)

        except Exception as e:
            flash(f'データ処理中にエラーが発生しました: {e}', 'danger')
            return redirect(origin_url)

    return render_template('data_mapping.html', form=form)