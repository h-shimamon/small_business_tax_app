# app/company/import_data.py
import os
import pandas as pd
from flask import render_template, redirect, url_for, flash, session, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.company import company_bp as import_bp  # ブループリント名を統一
from app.company.forms import DataMappingForm, FileUploadForm, SoftwareSelectionForm
from app.company.models import AccountTitleMaster, UserAccountMapping

# ウィザードのステップ定義
WIZARD_STEPS = ['select_software', 'chart_of_accounts', 'journals', 'fixed_assets']
FILE_UPLOAD_STEPS = ['chart_of_accounts', 'journals', 'fixed_assets']

# データタイプごとの設定
DATA_TYPE_CONFIG = {
    'chart_of_accounts': {'step_name': '勘定科目データ選択'},
    'journals': {'step_name': '仕訳帳データ選択'},
    'fixed_assets': {'step_name': '固定資産データ選択'}
}

def _get_wizard_progress(current_step_key):
    """ウィザードの進捗状況を計算してリストで返す"""
    progress = []
    completed_steps = session.get('wizard_completed_steps', [])
    
    progress.append({
        'key': 'select_software',
        'name': '会計ソフト選択',
        'is_completed': 'select_software' in completed_steps,
        'is_current': current_step_key == 'select_software'
    })

    for step in FILE_UPLOAD_STEPS:
        progress.append({
            'key': step,
            'name': DATA_TYPE_CONFIG[step]['step_name'],
            'is_completed': step in completed_steps,
            'is_current': current_step_key == step
        })
    return progress

# 会計ソフトごとの設定
SOFTWARE_CONFIG = {
    'moneyforward': {
        'column_name': '勘定科目',
        'encoding': 'utf-8-sig',  # BOM付きUTF-8に対応
        'header_row': 0
    },
    'yayoi': {
        'column_name': '科目名', # 例: 弥生会計の場合
        'encoding': 'shift_jis',
        'header_row': 1 # 例: ヘッダーが2行目にある場合
    }
    # 他の会計ソフトもここに追加
}

@import_bp.route('/select_software', methods=['GET', 'POST'])
@login_required
def select_software():
    """会計ソフトを選択する画面"""
    form = SoftwareSelectionForm()
    if form.validate_on_submit():
        session['selected_software'] = form.accounting_software.data
        session['wizard_completed_steps'] = ['select_software'] # 進捗を記録
        flash(f'{form.accounting_software.data} が選択されました。勘定科目ファイルをアップロードしてください。', 'info')
        return redirect(url_for('company.upload_data'))
    
    # GETリクエスト時もウィザード進捗を渡す
    wizard_progress = _get_wizard_progress('select_software')
    return render_template('company/select_software.html', form=form, title="会計ソフト選択", wizard_progress=wizard_progress)

@import_bp.route('/upload_account_data', methods=['GET', 'POST'])
@login_required
def upload_data():
    """勘定科目ファイルをアップロードし、解析・照合する"""
    if 'selected_software' not in session:
        flash('最初に会計ソフトを選択してください。', 'warning')
        return redirect(url_for('company.select_software'))

    form = FileUploadForm()
    software = session.get('selected_software')
    config = SOFTWARE_CONFIG.get(software)

    if not config:
        flash('対応していない会計ソフトです。', 'danger')
        return redirect(url_for('company.select_software'))

    if form.validate_on_submit():
        file = form.upload_file.data
        if not file:
            flash('ファイルが選択されていません。', 'danger')
            return redirect(request.url)

        # ステップ1: ファイルの受信と解析
        try:
            df = pd.read_csv(
                file,
                encoding=config['encoding'],
                header=config['header_row']
            )
            user_accounts = df[config['column_name']].dropna().astype(str).str.strip().unique().tolist()

        except UnicodeDecodeError:
            flash(f"ファイルの文字コードが異なります。{config['encoding']} を選択してください。", 'danger')
            return redirect(url_for('company.upload_data'))
        except KeyError:
            flash(f"ファイルに必須の列 '{config['column_name']}' が見つかりません。", 'danger')
            return redirect(url_for('company.upload_data'))
        except Exception as e:
            flash(f'ファイルの読み込み中に予期せぬエラーが発生しました: {e}', 'danger')
            return redirect(url_for('company.upload_data'))

        # ステップ2: マスタデータとの照合
        unmatched_accounts = []
        # マスターの勘定科目名を重複なくセットとして保持（高速な検索のため）
        master_account_names = {master.name.strip() for master in AccountTitleMaster.query.all()}
        
        for account_name in user_accounts:
            if not account_name:  # 空文字やNoneを除外
                continue

            # 自動マッピング試行
            existing_mapping = UserAccountMapping.query.filter_by(
                user_id=current_user.id,
                original_account_name=account_name
            ).first()
            if existing_mapping:
                continue

            # マスタ直接照合
            if account_name in master_account_names:
                continue
            
            unmatched_accounts.append(account_name)

        # ステップ3: 画面遷移の分岐
        if not unmatched_accounts:
            flash('すべての勘定科目の取り込みが完了しました。', 'success')
            # ウィザードの進捗を更新
            completed_steps = session.get('wizard_completed_steps', [])
            if 'chart_of_accounts' not in completed_steps:
                completed_steps.append('chart_of_accounts')
            session['wizard_completed_steps'] = completed_steps
            # 次のステップへリダイレクト（仮に内訳書画面へ）
            return redirect(url_for('company.statement_of_accounts'))
        else:
            session['unmatched_accounts'] = unmatched_accounts
            session['selected_software'] = software
            return redirect(url_for('company.data_mapping'))

    wizard_progress = _get_wizard_progress('chart_of_accounts')
    return render_template('company/upload_data.html', form=form, title="勘定科目ファイルのアップロード", wizard_progress=wizard_progress, description="勘定科目の一覧をCSV形式でアップロードしてください。", selected_software=software)


@import_bp.route('/data_mapping', methods=['GET'])
@login_required
def data_mapping():
    """項目マッピング画面 (GET)"""
    unmatched_accounts = session.get('unmatched_accounts', [])
    if not unmatched_accounts:
        flash('マッピング対象の項目がありません。', 'info')
        return redirect(url_for('company.upload_data'))

    master_accounts = AccountTitleMaster.query.order_by(AccountTitleMaster.number).all()
    form = DataMappingForm()
    wizard_progress = _get_wizard_progress('chart_of_accounts') # 現在のステップとして渡す

    return render_template(
        'company/data_mapping.html',
        unmatched_accounts=unmatched_accounts,
        master_accounts=master_accounts,
        form=form,
        title="項目マッピング",
        wizard_progress=wizard_progress
    )

@import_bp.route('/data_mapping', methods=['POST'])
@login_required
def process_data_mapping():
    """項目マッピング画面 (POST)"""
    mappings = request.form
    software_name = session.get('selected_software')
    unmatched_accounts = session.get('unmatched_accounts', [])

    if not software_name or not unmatched_accounts:
        flash('セッション情報が失われました。もう一度アップロードからやり直してください。', 'warning')
        return redirect(url_for('company.upload_data'))

    try:
        for original_name in unmatched_accounts:
            master_id_str = mappings.get(f'map_{original_name}')
            if master_id_str and master_id_str.isdigit():
                # 既に存在しないか念のため確認
                existing_map = UserAccountMapping.query.filter_by(
                    user_id=current_user.id,
                    original_account_name=original_name
                ).first()

                if not existing_map:
                    new_mapping = UserAccountMapping(
                        user_id=current_user.id,
                        software_name=software_name,
                        original_account_name=original_name,
                        master_account_id=int(master_id_str)
                    )
                    db.session.add(new_mapping)
        
        db.session.commit()
        flash('マッピング情報を保存しました。', 'success')
        
        # ウィザードの進捗を更新
        completed_steps = session.get('wizard_completed_steps', [])
        if 'chart_of_accounts' not in completed_steps:
            completed_steps.append('chart_of_accounts')
        session['wizard_completed_steps'] = completed_steps

    except Exception as e:
        db.session.rollback()
        flash(f'データベースへの保存中にエラーが発生しました: {e}', 'danger')
    finally:
        # 成功・失敗にかかわらずセッションをクリア
        session.pop('unmatched_accounts', None)
        session.pop('selected_software', None)

    return redirect(url_for('company.statement_of_accounts'))
