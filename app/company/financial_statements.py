# app/company/financial_statements.py
from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.company import company_bp
from app.company.models import AccountingData
from app.navigation import get_navigation_state

@company_bp.route('/confirm_trial_balance', methods=['GET'])
@login_required
def confirm_trial_balance():
    """
    データベースに永続化された最新の財務諸表データを表示する。
    """
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