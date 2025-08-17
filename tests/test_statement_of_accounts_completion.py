# tests/test_statement_of_accounts_completion.py
from datetime import date
from flask_login import login_user

from app import db
from app.company.models import User, Company, AccountingData, AccountTitleMaster, Deposit


def login_as_first_user(client):
    app = client.application
    with app.app_context():
        user = db.session.get(User, 1)
        with client.session_transaction():
            login_user(user)


def setup_bs_master_for_deposits(app):
    with app.app_context():
        # 預貯金のBSマスタ（普通預金など）
        db.session.add(AccountTitleMaster(
            number=10, name='普通預金', statement_name='資産',
            major_category='資産', middle_category='流動資産', minor_category='',
            breakdown_document='預貯金', master_type='BS'
        ))
        db.session.commit()


def test_mark_and_unmark_completion_based_on_difference(client, init_database):
    """
    差額=0 の時に完了マークされ、差額≠0 で未完了に戻ることを検証（セッションの wizard_completed_steps）。
    """
    app = client.application
    login_as_first_user(client)
    setup_bs_master_for_deposits(app)

    with app.app_context():
        company = db.session.get(Company, 1)
        # 1) source_total=1000 に設定
        data = {
            'balance_sheet': {
                'assets': {
                    'items': [
                        {'name': '普通預金', 'amount': 1000},
                    ]
                }
            },
            'profit_loss_statement': {}
        }
        db.session.add(AccountingData(company_id=company.id, period_start=date(2024,1,1), period_end=date(2024,12,31), data=data))
        db.session.commit()

    # 2) breakdown_total=1000 を作成 → 差額0 で完了マーク
    with app.app_context():
        db.session.add(Deposit(company_id=1, financial_institution='X銀行', branch_name='本店', account_type='普通', account_number='000', balance=1000))
        db.session.commit()

    resp = client.get('/statement_of_accounts?page=deposits', follow_redirects=True)
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        assert 'deposits' in sess.get('wizard_completed_steps', [])

    # 3) breakdown_total を 700 に変更 → 差額300 で未完了へ
    with app.app_context():
        dep = Deposit.query.filter_by(company_id=1).first()
        dep.balance = 700
        db.session.commit()

    resp2 = client.get('/statement_of_accounts?page=deposits', follow_redirects=True)
    assert resp2.status_code == 200
    with client.session_transaction() as sess:
        assert 'deposits' not in sess.get('wizard_completed_steps', [])

