# app/company/import_data.py
from flask import render_template, redirect, url_for, flash, session, request
from flask_login import login_required, current_user

from app import db
from app.company import company_bp as import_bp
from app.company.forms import DataMappingForm, FileUploadForm, SoftwareSelectionForm
from app.company.models import AccountingData, UserAccountMapping
from app.navigation import get_navigation_state, mark_step_as_completed
from .services import DataMappingService, FinancialStatementService
from .parser_factory import ParserFactory

# --- ウィザードと設定の定義 ---

DATA_TYPE_CONFIG = {
    'chart_of_accounts': {
        'title': '勘定科目データのインポート',
        'description': 'まず初めに、勘定科目の一覧をCSVまたはTXT形式でアップロードしてください。これは全ての会計処理の基礎となります。',
        'step_name': '勘定科目データ選択',
        'parser_method': 'get_chart_of_accounts'
    },
    'journals': {
        'title': '仕訳帳のインポート',
        'description': '次に、会計期間中のすべての取引が記録された仕訳帳のCSVまたはTXTファイルをアップロードしてください。',
        'step_name': '仕訳帳データ選択',
        'parser_method': 'get_journals'
    },
    'fixed_assets': {
        'title': '固定資産データのインポート',
        'description': '最後に、固定資産台帳のデータをCSVまたはTXT形式でアップロードしてください。（この機能は現在開発中です）',
        'step_name': '固定資産データ選択',
        'parser_method': 'get_fixed_assets'
    }
}

FILE_UPLOAD_STEPS = ['chart_of_accounts', 'journals', 'fixed_assets']


# --- ルート関数の定義 ---

@import_bp.route('/select_software', methods=['GET', 'POST'])
@login_required
def select_software():
    """ウィザードの開始: 会計ソフトを選択"""
    form = SoftwareSelectionForm()
    if form.validate_on_submit():
        # ウィザードの進行状況をリセットし、新しいフローを開始する
        session['selected_software'] = form.accounting_software.data
        session['wizard_completed_steps'] = ['select_software']
        flash(f'{form.accounting_software.data} が選択されました。新しいデータ取込を開始します。', 'info')
        return redirect(url_for('company.data_upload_wizard'))
    
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
    """ウィザードの進行を管理し、次のステップにリダイレクト"""
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
        return redirect(url_for('company.statement_of_accounts'))

@import_bp.route('/upload/<datatype>', methods=['GET', 'POST'])
@login_required
def upload_data(datatype):
    """データタイプに応じたファイルアップロード処理"""
    config = DATA_TYPE_CONFIG.get(datatype)
    if not config:
        flash('無効なデータタイプです。', 'danger')
        return redirect(url_for('company.data_upload_wizard'))

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
        if not file or not file.filename:
            flash('ファイルが選択されていません。', 'danger')
            return redirect(request.url)

        software = session.get('selected_software')
        try:
            parser = ParserFactory.create_parser(software, file)
            parser_method = getattr(parser, config['parser_method'])
            parsed_data = parser_method()

            if datatype == 'chart_of_accounts':
                mapping_service = DataMappingService(current_user.id)
                unmatched_accounts = mapping_service.get_unmatched_accounts(parsed_data)
                if not unmatched_accounts:
                    flash('すべての勘定科目の取り込みが完了しました。', 'success')
                    mark_step_as_completed(datatype)
                    return redirect(url_for('company.data_upload_wizard'))
                else:
                    session['unmatched_accounts'] = unmatched_accounts
                    return redirect(url_for('company.data_mapping'))
            
            elif datatype == 'journals':
                company = current_user.company
                if not company or not company.accounting_period_start or not company.accounting_period_end:
                    flash('申告情報で会計期間が設定されていません。先に基本情報を登録してください。', 'warning')
                    return redirect(url_for('company.declaration'))

                # Companyモデルから会計期間を取得し、dateオブジェクトに変換
                from datetime import datetime
                start_date = datetime.strptime(company.accounting_period_start, '%Y-%m-%d').date()
                end_date = datetime.strptime(company.accounting_period_end, '%Y-%m-%d').date()

                # マッピングサービスを利用してデータを変換
                mapping_service = DataMappingService(current_user.id)
                df_journals = mapping_service.apply_mappings_to_journals(parsed_data)

                # 財務諸表サービスを呼び出し
                fs_service = FinancialStatementService(df_journals, start_date, end_date)
                bs_data = fs_service.create_balance_sheet()
                pl_data = fs_service.create_profit_loss_statement()

                # 既存の会計データを削除
                AccountingData.query.filter_by(company_id=company.id).delete()

                # 新しい会計データをDBに保存
                accounting_data = AccountingData(
                    company_id=company.id,
                    period_start=start_date,
                    period_end=end_date,
                    data={
                        'balance_sheet': bs_data,
                        'profit_loss_statement': pl_data
                    }
                )
                db.session.add(accounting_data)
                db.session.commit()

                mark_step_as_completed(datatype)
                flash('仕訳帳データが正常に取り込まれ、財務諸表が生成されました。', 'success')
                return redirect(url_for('company.confirm_trial_balance'))

        except Exception as e:
            flash(f"エラーが発生しました: {e}", 'danger')
            return redirect(request.url)

    navigation_state = get_navigation_state(datatype)
    show_reset_link = (datatype == 'journals')
    
    template_config = {
        'title': config['title'],
        'description': config['description'],
        'step_name': config['step_name']
    }

    return render_template(
        'company/upload_data.html', 
        form=form, 
        navigation_state=navigation_state, 
        show_reset_link=show_reset_link,
        **template_config
    )

@import_bp.route('/financial_statements', methods=['GET'])
@login_required
def show_financial_statements():
    """生成された財務諸表を表示する"""
    statements = session.get('financial_statements')
    if not statements:
        flash('表示する財務諸表データがありません。再度アップロードしてください。', 'warning')
        return redirect(url_for('company.upload_data', datatype='journals'))

    navigation_state = get_navigation_state('journals')

    return render_template(
        'company/financial_statements.html',
        title="財務諸表",
        bs_data=statements['balance_sheet'],
        pl_data=statements['profit_and_loss'],
        navigation_state=navigation_state
    )

@import_bp.route('/data_mapping', methods=['GET', 'POST'])
@login_required
def data_mapping():
    """項目マッピング画面"""
    mapping_service = DataMappingService(current_user.id)
    
    if request.method == 'POST':
        software_name = session.get('selected_software')
        try:
            mapping_service.save_mappings(request.form, software_name)
            flash('マッピング情報を保存しました。', 'success')
            mark_step_as_completed('chart_of_accounts')
        except Exception as e:
            flash(str(e), 'danger')
        finally:
            session.pop('unmatched_accounts', None)
        return redirect(url_for('company.data_upload_wizard'))

    unmatched_accounts = session.get('unmatched_accounts', [])
    if not unmatched_accounts:
        return redirect(url_for('company.upload_data', datatype='chart_of_accounts'))

    mapping_items, master_accounts = mapping_service.get_mapping_suggestions(unmatched_accounts)
    
    grouped_masters = {}
    for master in master_accounts:
        major = master.major_category or 'その他'
        if major not in grouped_masters:
            grouped_masters[major] = []
        grouped_masters[major].append(master)

    form = DataMappingForm()
    navigation_state = get_navigation_state('data_mapping')
    return render_template(
        'company/data_mapping.html', 
        mapping_items=mapping_items, 
        grouped_masters=grouped_masters, 
        master_accounts=master_accounts,
        form=form, 
        title="項目マッピング", 
        navigation_state=navigation_state
    )

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
        num_deleted = db.session.query(UserAccountMapping).filter_by(user_id=current_user.id).delete()
        db.session.commit()
        flash(f'{num_deleted}件の勘定科目マッピング情報をリセットしました。', 'success')
        session['wizard_completed_steps'] = ['select_software']
    except Exception as e:
        db.session.rollback()
        flash(f'リセット処理中にエラーが発生しました: {e}', 'danger')
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