# tests/test_sidebar_skip_on_form_pages.py
from datetime import date
import re
# from flask_login import login_user

from app import db
from app.company.models import Company, AccountingData, AccountTitleMaster


from tests.helpers.auth import login_as


def setup_bs_master_for_two_pages(app):
    with app.app_context():
        # 受取手形（表示対象にする）と 買掛金（スキップ対象にする）
        db.session.add(AccountTitleMaster(
            number=101, name='受取手形', statement_name='流動資産',
            major_category='資産', middle_category='流動資産', minor_category='',
            breakdown_document='受取手形', master_type='BS'
        ))
        db.session.add(AccountTitleMaster(
            number=201, name='買掛金', statement_name='流動負債',
            major_category='負債', middle_category='流動負債', minor_category='',
            breakdown_document='買掛金', master_type='BS'
        ))
        db.session.commit()


def test_form_page_sidebar_marks_skipped_black_dot_by_class(client, init_database):
    """
    フォーム画面（買掛金の新規登録）で、参照合計=0のページに is-skipped クラス（黒丸相当）が付与されることを検証。
    赤丸指定のCSSは is-skipped を除外しているため、視覚的にも黒丸となる。
    """
    app = client.application
    login_as(client, 1)
    setup_bs_master_for_two_pages(app)

    with app.app_context():
        company = db.session.get(Company, 1)
        # AccountingData: 受取手形のみ金額>0、買掛金は0
        data = {
            'balance_sheet': {
                'assets': {'items': [ {'name': '受取手形', 'amount': 1000} ]},
                'liabilities': {'items': []}
            },
            'profit_loss_statement': {}
        }
        db.session.add(AccountingData(company_id=company.id, period_start=date(2024,1,1), period_end=date(2024,12,31), data=data))
        db.session.commit()

    # 買掛金の新規登録画面へ（参照合計=0のため本項目はスキップ状態）
    resp = client.get('/statement/accounts_payable/add', follow_redirects=True)
    body = resp.data.decode('utf-8')
    assert resp.status_code == 200

    # 「買掛金（未払金・未払費用）」のラベルを含む行のLIに is-skipped が含まれることを簡易的に検証
    # 近傍テキスト検索で該当LIのクラス属性を抽出
    m = re.search(r'<li class=\"([^\"]*progress-step[^\"]*)\">\s*<a[^>]*>\s*<span class=\"progress-marker\"></span>\s*<span class=\"progress-label\">買掛金（未払金・未払費用）</span>', body)
    assert m, '買掛金のナビ項目が見つかりません'
    classes = m.group(1)
    assert 'is-skipped' in classes, f'期待する is-skipped が付いていません。classes={classes}'

