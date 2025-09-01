# app/company/fixed_assets_pages.py
from flask import render_template, session, redirect, url_for, flash
from flask_login import login_required
from . import company_bp
from app.navigation import get_navigation_state


@company_bp.route('/fixed-assets/ledger')
@login_required
def fixed_assets_ledger():
    """固定資産台帳（プレビュー表示）。
    事前に upload(fixed_assets) で取り込んだ内容をセッションから表示する。
    """
    records = session.get('fixed_assets_preview', []) or []
    nav = get_navigation_state('fixed_assets_ledger')
    if not records:
        flash('固定資産データがありません。まずは固定資産データの取込を実行してください。', 'info')
        return render_template('company/fixed_assets_ledger.html', records=[], navigation_state=nav)
    return render_template('company/fixed_assets_ledger.html', records=records, navigation_state=nav)


@company_bp.route('/fixed-assets/small-assets')
@login_required
def small_assets_list():
    """少額資産明細（スケルトン）。
    仕様確定前のため空状態を表示する。後続で条件や閾値を反映。
    """
    nav = get_navigation_state('small_assets')
    return render_template('company/small_assets_list.html', navigation_state=nav)


@company_bp.post('/fixed-assets/preview/delete/<int:idx>')
@login_required
def delete_fixed_asset_preview(idx: int):
    """プレビュー中の固定資産レコードを削除（セッション更新）。"""
    records = session.get('fixed_assets_preview', []) or []
    if 0 <= idx < len(records):
        try:
            del records[idx]
            session['fixed_assets_preview'] = records
            flash('1件削除しました。', 'success')
        except Exception:
            flash('削除に失敗しました。', 'danger')
    else:
        flash('対象レコードが見つかりません。', 'warning')
    return redirect(url_for('company.fixed_assets_ledger'))


@company_bp.post('/fixed-assets/preview/edit/<int:idx>')
@login_required
def edit_fixed_asset_preview(idx: int):
    """プレビュー中の固定資産レコードを編集（セッション更新）。"""
    records = session.get('fixed_assets_preview', []) or []
    if not (0 <= idx < len(records)):
        flash('対象レコードが見つかりません。', 'warning')
        return redirect(url_for('company.fixed_assets_ledger'))
    import math
    from flask import request

    def _to_int(name):
        try:
            v = request.form.get(name, '').replace(',', '').strip()
            return int(v) if v != '' else 0
        except Exception:
            return 0

    def _to_float(name):
        try:
            v = request.form.get(name, '').replace(',', '').strip()
            return float(v) if v != '' else None
        except Exception:
            return None

    def _to_str(name):
        v = request.form.get(name, '').strip()
        return v or None

    row = records[idx] or {}
    row.update({
        'asset_type': _to_str('asset_type'),
        'name': _to_str('name'),
        'quantity_or_area': _to_float('quantity_or_area'),
        'acquisition_date': _to_str('acquisition_date'),
        'acquisition_cost': _to_int('acquisition_cost'),
        'depreciation_method': _to_str('depreciation_method'),
        'useful_life': _to_float('useful_life'),
        'period_this_year': _to_str('period_this_year'),
        'opening_balance': _to_int('opening_balance'),
        'planned_depreciation': _to_int('planned_depreciation'),
        'special_depreciation': _to_int('special_depreciation'),
        'expense_amount': _to_int('expense_amount'),
        'closing_balance': _to_int('closing_balance'),
    })
    records[idx] = row
    session['fixed_assets_preview'] = records
    flash('1件更新しました。', 'success')
    return redirect(url_for('company.fixed_assets_ledger'))
