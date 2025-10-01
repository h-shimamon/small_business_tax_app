# app/company/financial_statements.py
from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.company import company_bp
from app.company.models import AccountingData, UserAccountMapping
from app.navigation import get_navigation_state


@company_bp.route('/confirm_trial_balance', methods=['GET'])
@login_required
def confirm_trial_balance():
    """
    データベースに永続化された最新の財務諸表データを表示する。
    """
    # 防御的ガード: マッピングが存在しない場合は残高確認を許可しない（整合性維持）
    has_mapping = UserAccountMapping.query.filter_by(user_id=current_user.id).first() is not None
    if not has_mapping:
        flash('勘定科目マッピングが未設定または削除されています。勘定科目データ取込から再スタートしてください。', 'warning')
        return redirect(url_for('company.upload_data', datatype='chart_of_accounts'))

    # 現在の会社に紐づく最新の会計データを取得
    accounting_data = AccountingData.query.filter_by(
        company_id=current_user.company.id
    ).order_by(AccountingData.created_at.desc()).first()

    if not accounting_data:
        flash('会計データがまだ取り込まれていません。先に仕訳帳データをアップロードしてください。', 'warning')
        return redirect(url_for('company.upload_data', datatype='journals'))

    # テンプレートに渡すためのデータを展開
    bs_data = accounting_data.data.get('balance_sheet', {})
    pl_data = accounting_data.data.get('profit_loss_statement', {})
    
    navigation_state = get_navigation_state('confirm_trial_balance')

    return render_template(
        'company/confirm_trial_balance.html',
        title="残高試算表の確認",
        bs_data=bs_data,
        pl_data=pl_data,
        navigation_state=navigation_state,
        company_name=current_user.company.company_name,
        term_number=current_user.company.term_number,
        accounting_period_start=accounting_data.period_start.strftime('%Y-%m-%d'),
        accounting_period_end=accounting_data.period_end.strftime('%Y-%m-%d')
    )
