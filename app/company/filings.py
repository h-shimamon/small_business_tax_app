# app/company/filings.py
from __future__ import annotations

from flask import render_template, request, abort

from app.company import company_bp
from .auth import company_required
from app.navigation import get_navigation_state

# 申告書ページのタイトル定義（仮置き）。
TITLE_MAP = {
    'beppyo_2': '別表2',
    'beppyo_16_2': '別表16(2)',
    'beppyo_15': '別表15',
    'tax_payment_status_beppyo_5_2': '法人税等の納付状況（別表５(2))',
    'beppyo_7': '別表７',
    'beppyo_4': '別表４',
    'beppyo_5_1': '別表５(1)',
    'appropriation_calc_beppyo_5_2': '納税充当金の計算（別表５(2))',
    'local_tax_rates': '地方税税率登録',
    'business_overview_1': '事業概況説明書１',
    'business_overview_2': '事業概況説明書２',
    'business_overview_3': '事業概況説明書３',
    'journal_entries_cit': '法人税等に関する仕訳の表示',
    'financial_statements': '決算書',
}

@company_bp.route('/filings')
@company_required
def filings(company):
    """申告書グループの各ページ（仮置き）。
    内訳書ビューのレイアウトを流用し、空リストを表示するだけのプレースホルダ。
    """
    page = request.args.get('page', 'beppyo_2')
    title = TITLE_MAP.get(page)
    if not title:
        abort(404)

    context = {
        'page': page,
        'page_title': title,
        'items': [],
        'navigation_state': get_navigation_state(page),
        'generic_summary': {'bs_total': 0, 'breakdown_total': 0, 'difference': 0},
        'soa_next_url': None,
        'soa_next_name': None,
        'pdf_year': '2025',
    }
    # statement_of_accounts.html を流用（ボタン/サマリは差分0・items空の状態で安全に表示）
    # 特例: 事業概況説明書１は専用テンプレートを表示（保存なしの入力UI）
    if page == 'business_overview_1':
        return render_template('company/filings/business_overview_1.html', **context)
    return render_template('company/statement_of_accounts.html', **context)


@company_bp.get('/filings/preview')
@company_required
def filings_preview(company):
    """事業概況説明書などのPDFプレビューを返す（読み取り専用）。
    現状は business_overview_1 のみ固定パスを返却。
    """
    from flask import send_file
    page = request.args.get('page', '')
    if page == 'business_overview_1':
        pdf_path = '/Users/shimamorihayato/Projects/small_business_tax_app/resources/pdf_forms/jigyogaikyo/2025/source.pdf'
    else:
        abort(404)
    try:
        return send_file(pdf_path, mimetype='application/pdf', as_attachment=False, download_name='business_overview_1_preview.pdf')
    except Exception:
        abort(404)
