# app/company/import_data.py
from flask import abort, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.company import company_bp as import_bp
from app.company.forms import DataMappingForm, FileUploadForm, SoftwareSelectionForm
from app.company.models import UserAccountMapping
from app.company.services.data_mapping_service import DataMappingService
from app.company.services.import_consistency_service import (
    on_mapping_deleted,
    on_mapping_saved,
    on_mappings_reset,
)
from app.company.services.import_wizard_service import UploadWizardService
from app.company.services.upload_flow_service import (
    UploadFlowError,
    UploadFlowService,
    UploadValidationError,
    build_upload_error_context,
)
from app.extensions import db
from app.navigation import (
    get_navigation_state,
    mark_step_as_completed,
)
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

FILE_UPLOAD_STEPS = ['journals']


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
    wizard = UploadWizardService(session, FILE_UPLOAD_STEPS)
    if not wizard.has_selected_software():
        flash('最初に会計ソフトを選択してください。', 'warning')
        return redirect(url_for('company.select_software'))

    next_step = wizard.next_pending_step()
    if next_step:
        return redirect(url_for('company.upload_data', datatype=next_step))

    flash('すべてのファイルのアップロードが完了しました。', 'success')
    wizard.reset()
    return redirect(url_for('company.statement_of_accounts'))



def _process_upload_submission(form, datatype, config):
    file_storage = form.upload_file.data
    service = UploadFlowService(datatype, current_user, config, session)
    try:
        result = service.handle(file_storage)
    except UploadValidationError as exc:
        session['upload_error_ctx'] = build_upload_error_context(getattr(exc, 'code', None), str(exc))
        flash(str(exc), 'danger')
        return redirect(request.url)
    except UploadFlowError as exc:
        session['upload_error_ctx'] = build_upload_error_context(getattr(exc, 'code', None), str(exc))
        flash(f"エラーが発生しました: {exc}", 'danger')
        return redirect(request.url)
    except Exception as exc:
        session['upload_error_ctx'] = build_upload_error_context('unknown_error', str(exc))
        flash(f"エラーが発生しました: {exc}", 'danger')
        return redirect(request.url)

    if result.flash_message:
        message, category = result.flash_message
        flash(message, category)
    return redirect(url_for(result.redirect_endpoint, **result.redirect_kwargs))

@import_bp.route('/upload/<datatype>', methods=['GET', 'POST'])
@login_required
def upload_data(datatype):
    """データタイプに応じたファイルアップロード処理"""
    config = DATA_TYPE_CONFIG.get(datatype)
    try:
        from_step = request.args.get('from_step')
        if from_step:
            mark_step_as_completed(from_step)
    except Exception:
        pass
    if not config:
        flash('無効なデータタイプです。', 'danger')
        return redirect(url_for('company.data_upload_wizard'))

    wizard = UploadWizardService(session, FILE_UPLOAD_STEPS)
    if not wizard.has_selected_software():
        return redirect(url_for('company.select_software'))

    missing_step = wizard.ensure_previous_steps_completed(datatype)
    if missing_step:
        flash('前のステップを先に完了してください。', 'warning')
        return redirect(url_for('company.data_upload_wizard'))

    form = FileUploadForm()
    if request.method == 'POST':
        return _process_upload_submission(form, datatype, config)

    navigation_state = get_navigation_state(datatype)
    show_reset_link = datatype == 'journals'
    template_config = {
        'title': config['title'],
        'description': config['description'],
        'step_name': config['step_name'],
    }
    error_context = session.pop('upload_error_ctx', None)
    return render_template(
        'company/upload_data.html',
        form=form,
        navigation_state=navigation_state,
        show_reset_link=show_reset_link,
        error_context=error_context,
        **template_config,
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



def _recompute_statements(mapping_service, software_name):
    j_path = session.get('uploaded_journals_path')
    if not j_path:
        return
    try:
        import io
        import os

        from werkzeug.datastructures import FileStorage

        with open(j_path, 'rb') as jf:
            content = jf.read()
        fs = FileStorage(
            stream=io.BytesIO(content),
            filename=session.get('uploaded_journals_name') or 'journals.csv',
        )
        parser = ParserFactory.create_parser(software_name, fs)
        parsed = parser.get_journals()

        from app.primitives.dates import get_company_period

        company = current_user.company
        period = get_company_period(company)
        start_date, end_date = period.start, period.end
        df_journals = mapping_service.apply_mappings_to_journals(parsed)

        from .services import FinancialStatementService

        fs_service = FinancialStatementService(df_journals, start_date, end_date)
        bs_data = fs_service.create_balance_sheet()
        pl_data = fs_service.create_profit_loss_statement()
        soa_breakdowns = fs_service.get_soa_breakdowns()

        from app.company.models import AccountingData
        from app.extensions import db as _db

        AccountingData.query.filter_by(company_id=company.id).delete()
        ad = AccountingData(
            company_id=company.id,
            period_start=start_date,
            period_end=end_date,
            data={
                'balance_sheet': bs_data,
                'profit_loss_statement': pl_data,
                'soa_breakdowns': soa_breakdowns,
            },
        )
        _db.session.add(ad)
        _db.session.commit()
        mark_step_as_completed('journals')
        try:
            if j_path and os.path.isfile(j_path):
                os.remove(j_path)
            session.pop('uploaded_journals_path', None)
            session.pop('uploaded_journals_name', None)
        except Exception:
            pass
    except Exception as exc:
        flash(f'再計算に失敗しました: {exc}', 'warning')


def _post_mapping_redirect():
    try:
        from app.company.models import AccountingData as __AD

        latest = (
            __AD.query.filter_by(company_id=current_user.company.id)
            .order_by(__AD.created_at.desc())
            .first()
        )
        if latest is not None:
            return redirect(url_for('company.confirm_trial_balance'))
    except Exception:
        pass
    return redirect(url_for('company.data_upload_wizard'))


def _handle_data_mapping_post(mapping_service):
    software_name = session.get('selected_software')
    try:
        mapping_service.save_mappings(request.form, software_name)
        flash('マッピング情報を保存しました。', 'success')
        on_mapping_saved(current_user.id)
        _recompute_statements(mapping_service, software_name)
    except Exception as exc:
        flash(str(exc), 'danger')
    finally:
        session.pop('unmatched_accounts', None)
    return _post_mapping_redirect()



def _group_master_accounts(master_accounts):
    grouped: dict[str, list] = {}
    for master in master_accounts:
        major = master.major_category or 'その他'
        grouped.setdefault(major, []).append(master)
    return grouped

@import_bp.route('/data_mapping', methods=['GET', 'POST'])
@login_required
def data_mapping():
    """項目マッピング画面"""
    mapping_service = DataMappingService(current_user.id)

    if request.method == 'POST':
        return _handle_data_mapping_post(mapping_service)

    unmatched_accounts = session.get('unmatched_accounts', [])
    if not unmatched_accounts:
        return redirect(url_for('company.manage_mappings'))

    mapping_items, master_accounts = mapping_service.get_mapping_suggestions(unmatched_accounts)
    grouped_masters = _group_master_accounts(master_accounts)

    form = DataMappingForm()
    navigation_state = get_navigation_state('data_mapping')
    return render_template(
        'company/data_mapping.html',
        mapping_items=mapping_items,
        grouped_masters=grouped_masters,
        master_accounts=master_accounts,
        form=form,
        title="項目マッピング",
        navigation_state=navigation_state,
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
        # マッピングのリセットに伴い、会計データも破棄してフローを初期化
        on_mappings_reset(current_user.id)
        session['wizard_completed_steps'] = ['select_software']
    except Exception as e:
        db.session.rollback()
        flash(f'リセット処理中にエラーが発生しました: {e}', 'danger')
    return redirect(url_for('company.data_upload_wizard'))

@import_bp.route('/manage_mappings', methods=['GET'])
@login_required
def manage_mappings():
    """登録済みのマッピングを一覧表示・管理する画面"""
    mappings = UserAccountMapping.query.filter_by(user_id=current_user.id).order_by(UserAccountMapping.original_account_name).all()
    # サイドバーは「勘定科目マッピング」をアクティブとして表示（data_mappingキー）
    navigation_state = get_navigation_state('data_mapping')
    return render_template('company/manage_mappings.html', mappings=mappings, navigation_state=navigation_state)

@import_bp.route('/delete_mapping/<int:mapping_id>', methods=['POST'])
@login_required
def delete_mapping(mapping_id):
    """特定のマッピングを削除する"""
    mapping_to_delete = db.session.get(UserAccountMapping, mapping_id)
    if mapping_to_delete is None:
        abort(404)
    
    if mapping_to_delete.user_id != current_user.id:
        flash('権限がありません。', 'danger')
        return redirect(url_for('company.manage_mappings'))
        
    try:
        db.session.delete(mapping_to_delete)
        db.session.commit()
        flash('マッピングを削除しました。', 'success')

        # マッピング削除後の整合性維持: 既存の会計データがあれば破棄し、勘定科目データ取込から再スタート
        if on_mapping_deleted(current_user.id):
            session['wizard_completed_steps'] = ['select_software']
            flash('既存の会計データを破棄しました。必要に応じて仕訳帳データを再取込してください。', 'info')
            return redirect(url_for('company.manage_mappings'))
    except Exception as e:
        db.session.rollback()
        flash(f'削除中にエラーが発生しました: {e}', 'danger')
        
    return redirect(url_for('company.manage_mappings'))
