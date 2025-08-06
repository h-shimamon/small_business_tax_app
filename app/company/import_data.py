# app/company/import_data.py
import os
import pandas as pd
from flask import render_template, redirect, url_for, flash, session, request
from flask_login import login_required, current_user
from thefuzz import process
from werkzeug.utils import secure_filename

from app import db
from app.company import company_bp as import_bp
from app.company.forms import DataMappingForm, FileUploadForm, SoftwareSelectionForm
from app.company.models import AccountTitleMaster, UserAccountMapping
from app.utils import get_navigation_state, mark_step_as_completed

# --- ウィザードと設定の定義 ---

# データタイプごとの設定
DATA_TYPE_CONFIG = {
    'chart_of_accounts': {
        'title': '勘定科目データのインポート',
        'description': 'まず初めに、勘定科目の一覧をCSV形式でアップロードしてください。これは全ての会計処理の基礎となります。',
        'step_name': '勘定科目データ選択'
    },
    'journals': {
        'title': '仕訳帳のインポート',
        'description': '次に、会計期間中のすべての取引が記�����された仕訳帳のCSVファイルをアップロードしてください。',
        'step_name': '仕訳帳データ選択'
    },
    'fixed_assets': {
        'title': '固定資産台帳のインポート',
        'description': '最後に、固定資産台帳をCSV形式でアップロードしてください。',
        'step_name': '固定資産データ選択'
    }
}

# 会計ソフトごとの設定
SOFTWARE_CONFIG = {
    'moneyforward': {'column_name': '勘定科目', 'encoding': 'utf-8-sig', 'header_row': 0},
    'yayoi': {'column_name': '科目名', 'encoding': 'shift_jis', 'header_row': 1}
}

# ウィザードのステップ順序
FILE_UPLOAD_STEPS = ['chart_of_accounts', 'journals', 'fixed_assets']



# --- ルート関数の定義 ---

@import_bp.route('/select_software', methods=['GET', 'POST'])
@login_required
def select_software():
    """ウィザードの開始: 会計ソフトを選択"""
    form = SoftwareSelectionForm()
    if form.validate_on_submit():
        session['selected_software'] = form.accounting_software.data
        mark_step_as_completed('select_software')
        flash(f'{form.accounting_software.data} が選択されました。', 'info')
        return redirect(url_for('company.data_upload_wizard'))
    
    # 既存のマッピングデータがあるか確認
    has_mappings = UserAccountMapping.query.filter_by(user_id=current_user.id).first() is not None
    navigation_state = get_navigation_state('select_software')
    return render_template(
        'company/select_software.html', 
        form=form, 
        title="会計ソフト選択", 
        navigation_state=navigation_state,
        has_mappings=has_mappings
    )

@import_bp.route('/data_upload_wizard', methods=['GET'])
@login_required
def data_upload_wizard():
    """ウィザ-ドの進行を管理し、次のステップにリダイレクト"""
    if 'selected_software' not in session:
        flash('最初に会計ソフトを選択してください。', 'warning')
        return redirect(url_for('company.select_software'))

    completed_steps = session.get('wizard_completed_steps', [])
    next_step = next((step for step in FILE_UPLOAD_STEPS if step not in completed_steps), None)
            
    if next_step:
        return redirect(url_for('company.upload_data', datatype=next_step))
    else:
        flash('すべてのファイルのアップロードが完了しました。', 'success')
        session.pop('wizard_completed_steps', None)
        session.pop('selected_software', None)
        return redirect(url_for('company.statement_of_accounts')) # 最終的な完了画面へ

@import_bp.route('/upload/<datatype>', methods=['GET', 'POST'])
@login_required
def upload_data(datatype):
    """データタイプに応じたファイルアップロード処理"""
    config = DATA_TYPE_CONFIG.get(datatype)
    if not config:
        flash('無効なデータタイプです。', 'danger')
        return redirect(url_for('company.data_upload_wizard'))

    # ウィザードのステップ検証
    completed_steps = session.get('wizard_completed_steps', [])
    if 'select_software' not in completed_steps:
        return redirect(url_for('company.select_software'))
    
    current_step_index = FILE_UPLOAD_STEPS.index(datatype)
    for i in range(current_step_index):
        if FILE_UPLOAD_STEPS[i] not in completed_steps:
            flash('前のステップを先に完了してください。', 'warning')
            return redirect(url_for('company.data_upload_wizard'))

    form = FileUploadForm()
    if form.validate_on_submit():
        file = form.upload_file.data
        if not file:
            flash('ファイルが選択されていません。', 'danger')
            return redirect(request.url)

        # --- 勘定科目データ (chart_of_accounts) の特別処理 ---
        if datatype == 'chart_of_accounts':
            software = session.get('selected_software')
            software_config = SOFTWARE_CONFIG.get(software)
            try:
                df = pd.read_csv(file, encoding=software_config['encoding'], header=software_config['header_row'])
                user_accounts = df[software_config['column_name']].dropna().astype(str).str.strip().unique().tolist()
            except Exception as e:
                flash(f'ファイル読み込みエラー: {e}', 'danger')
                return redirect(request.url)

            master_account_names = {master.name.strip() for master in AccountTitleMaster.query.all()}
            unmatched_accounts = [acc for acc in user_accounts if acc and acc not in master_account_names and not UserAccountMapping.query.filter_by(user_id=current_user.id, original_account_name=acc).first()]

            if not unmatched_accounts:
                flash('すべての勘定科目の取り込みが完了しました。', 'success')
                mark_step_as_completed(datatype)
                return redirect(url_for('company.data_upload_wizard'))
            else:
                session['unmatched_accounts'] = unmatched_accounts
                return redirect(url_for('company.data_mapping'))
        
        # --- 他のデータタイプの仮処理 ---
        else:
            flash(f'{config["title"]} の取り込み機能は現在開発中です。', 'info')
            mark_step_as_completed(datatype)
            return redirect(url_for('company.data_upload_wizard'))

    navigation_state = get_navigation_state(datatype)
    # datatypeが'journals'の場合のみ、リセットリンク表示用のフラグを立てる
    show_reset_link = (datatype == 'journals')
    
    return render_template(
        'company/upload_data.html', 
        form=form, 
        navigation_state=navigation_state, 
        show_reset_link=show_reset_link,
        **config
    )

@import_bp.route('/data_mapping', methods=['GET', 'POST'])
@login_required
def data_mapping():
    """項目マッピング画面 (GET) - AI提案 & グループ化対応"""
    if request.method == 'POST':
        mappings = request.form
        software_name = session.get('selected_software')
        original_names = [key.replace('map_', '') for key in mappings.keys() if key.startswith('map_')]

        if not software_name or not original_names:
            flash('セッション情報が失われました。もう一度アップロードからやり直してください。', 'warning')
            return redirect(url_for('company.upload_data', datatype='chart_of_accounts'))

        try:
            for original_name in original_names:
                master_id_str = mappings.get(f'map_{original_name}')
                if master_id_str and master_id_str.isdigit():
                    if not UserAccountMapping.query.filter_by(user_id=current_user.id, original_account_name=original_name).first():
                        db.session.add(UserAccountMapping(user_id=current_user.id, software_name=software_name, original_account_name=original_name, master_account_id=int(master_id_str)))
            db.session.commit()
            flash('マッピング情報を保存しました。', 'success')
            
            mark_step_as_completed('chart_of_accounts')
        except Exception as e:
            db.session.rollback()
            flash(f'データベースへの保存中にエラーが発生しました: {e}', 'danger')
        finally:
            session.pop('unmatched_accounts', None)
        return redirect(url_for('company.data_upload_wizard'))

    # --- GETリクエストの処理 ---
    unmatched_accounts = session.get('unmatched_accounts', [])
    if not unmatched_accounts:
        return redirect(url_for('company.upload_data', datatype='chart_of_accounts'))

    master_accounts = AccountTitleMaster.query.order_by(AccountTitleMaster.major_category, AccountTitleMaster.middle_category, AccountTitleMaster.number).all()
    master_choices = {master.name: master.id for master in master_accounts}
    
    mapping_items = []
    for account in unmatched_accounts:
        suggested_master_id = None
        best_match = process.extractOne(account, master_choices.keys())
        if best_match and best_match[1] > 70:
            suggested_master_id = master_choices[best_match[0]]
        mapping_items.append({'original_name': account, 'suggested_master_id': suggested_master_id})

    grouped_masters = {}
    for master in master_accounts:
        major = master.major_category or 'その他'
        if major not in grouped_masters: grouped_masters[major] = []
        grouped_masters[major].append(master)

    form = DataMappingForm()
    navigation_state = get_navigation_state('data_mapping')
    return render_template('company/data_mapping.html', mapping_items=mapping_items, grouped_masters=grouped_masters, form=form, title="項目マッピング", navigation_state=navigation_state)

@import_bp.route('/reset_mappings/confirm', methods=['GET'])
@login_required
def reset_account_mappings_confirmation():
    """マッピング情報のリセット確認画面を表示する"""
    return render_template('company/reset_confirmation.html')


@import_bp.route('/reset_mappings/execute', methods=['POST'])
@login_required
def reset_account_mappings_execution():
    """マッピング情報を削除し、ウィザードをリセットする"""
    try:
        # ログインユーザーのマッピングデータのみを削除
        num_deleted = db.session.query(UserAccountMapping).filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash(f'{num_deleted}件の勘定科目マッピング情報をリセットしました。', 'success')

        # ウィザードの進捗をリセット（会計ソフト選択は完了済みのまま）
        session['wizard_completed_steps'] = ['select_software']

    except Exception as e:
        db.session.rollback()
        flash(f'リセット処理中にエラーが発生しました: {e}', 'danger')

    # 勘定科目アップロード画面へリダイレクト
    return redirect(url_for('company.upload_data', datatype='chart_of_accounts'))


@import_bp.route('/manage_mappings', methods=['GET'])
@login_required
def manage_mappings():
    """登録済みのマッピングを一覧表示・管理する画面"""
    mappings = UserAccountMapping.query.filter_by(user_id=current_user.id).order_by(UserAccountMapping.original_account_name).all()
    return render_template('company/manage_mappings.html', mappings=mappings)


@import_bp.route('/delete_mapping/<int:mapping_id>', methods=['POST'])
@login_required
def delete_mapping(mapping_id):
    """特定のマッピングを削除する"""
    mapping_to_delete = UserAccountMapping.query.get_or_404(mapping_id)
    
    # 他のユーザーのデータを削除できないように、所有者を確認
    if mapping_to_delete.user_id != current_user.id:
        flash('権限がありません。', 'danger')
        return redirect(url_for('company.manage_mappings'))
        
    try:
        db.session.delete(mapping_to_delete)
        db.session.commit()
        flash('マッピングを削除しました。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {e}', 'danger')
        
    return redirect(url_for('company.manage_mappings'))
