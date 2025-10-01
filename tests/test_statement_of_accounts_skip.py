# tests/test_statement_of_accounts_skip.py
from datetime import date

from app.company.models import AccountingData, AccountTitleMaster, Company

# from flask_login import login_user
from app.extensions import db
from tests.helpers.auth import login_as


def setup_bs_master_for_notes_receivable(app):
    with app.app_context():
        db.session.add(AccountTitleMaster(
            number=5000, name='受取手形', statement_name='流動資産',
            major_category='資産', middle_category='流動資産', minor_category='',
            breakdown_document='受取手形', master_type='BS'
        ))
        db.session.commit()


def test_soa_redirects_when_current_page_skipped(client, init_database):
    """
    deposits が参照合計=0でスキップ対象、次の notes_receivable が参照合計>0 のとき、
    deposits へアクセスすると302で notes_receivable に前方リダイレクトされ、
    フラッシュに skip カテゴリの文言が含まれる。
    """
    app = client.application
    login_as(client, 1)
    setup_bs_master_for_notes_receivable(app)

    with app.app_context():
        company = db.session.get(Company, 1)
        data = {
            'balance_sheet': {
                'assets': {
                    'items': [
                        {'name': '受取手形', 'amount': 1234},
                    ]
                }
            },
            'profit_loss_statement': {}
        }
        db.session.add(AccountingData(company_id=company.id, period_start=date(2024,1,1), period_end=date(2024,12,31), data=data))
        db.session.commit()

    # まずはリダイレクト先を確認
    resp = client.get('/statement_of_accounts?page=deposits', follow_redirects=False)
    assert resp.status_code == 302
    assert 'page=notes_receivable' in resp.headers.get('Location', '')

    # リダイレクトを辿ってフラッシュ文言を確認
    resp2 = client.get('/statement_of_accounts?page=deposits', follow_redirects=True)
    body = resp2.data.decode('utf-8')
    assert '財務諸表に計上されていない勘定科目は自動でスキップされます。' in body


def test_navigation_state_marks_skipped(client, init_database):
    """
    notes_receivable のみ参照合計>0とし、get_navigation_state に渡した skipped_steps に
    deposits が含まれることを検証する（is_skipped=True）。
    """
    from app.company.services.soa_summary_service import SoASummaryService
    from app.navigation import get_navigation_state
    from app.navigation_builder import navigation_tree

    app = client.application
    login_as(client, 1)
    setup_bs_master_for_notes_receivable(app)

    with app.app_context():
        company = db.session.get(Company, 1)
        data = {
            'balance_sheet': {
                'assets': {
                    'items': [
                        {'name': '受取手形', 'amount': 1000},
                    ]
                }
            },
            'profit_loss_statement': {}
        }
        db.session.add(AccountingData(company_id=company.id, period_start=date(2024,1,1), period_end=date(2024,12,31), data=data))
        db.session.commit()

        # skipped set を組み上げ
        skipped_steps = set()
        soa_children = []
        for node in navigation_tree:
            if node.key == 'statement_of_accounts_group':
                soa_children = node.children
                break
        for child in soa_children:
            child_page = (child.params or {}).get('page')
            if child_page:
                if SoASummaryService.compute_skip_total(company.id, child_page) == 0:
                    skipped_steps.add(child.key)

        nav = get_navigation_state('notes_receivable', skipped_steps=skipped_steps)
        # SoAグループを見つけ、depositsの is_skipped=True を確認
        soa_group = next(g for g in nav if g['key'] == 'statement_of_accounts_group')
        child_map = {c['key']: c for c in soa_group['children']}
        assert child_map['deposits']['is_skipped'] is True
