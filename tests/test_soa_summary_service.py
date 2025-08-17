# tests/test_soa_summary_service.py
from datetime import date

from app import db
from app.company.models import AccountingData, Company, AccountTitleMaster, Borrowing
from app.company.services.soa_summary_service import SoASummaryService


def test_soa_borrowings_difference_and_skip(app, init_database):
    with app.app_context():
        # Arrange master: BS 借入金系のアカウント名を1件
        db.session.add(AccountTitleMaster(
            number=1000, name='借入金A', statement_name='借入金', major_category='負債',
            middle_category='流動負債', minor_category='', breakdown_document='借入金', master_type='BS'
        ))
        db.session.commit()

        company = Company.query.first()
        # AccountingData: BS 借入金A=300, PL 支払利息=200
        data = {
            'balance_sheet': {
                'liabilities': {
                    'items': [
                        {'name': '借入金A', 'amount': 300},
                    ]
                }
            },
            'profit_loss_statement': {
                'expenses': {
                    'items': [
                        {'name': '支払利息', 'amount': 200},
                    ]
                }
            }
        }
        db.session.add(AccountingData(company_id=company.id, period_start=date(2024,1,1), period_end=date(2024,12,31), data=data))
        # Breakdown: 期末現在高合計=400, 支払利子合計=50 -> breakdown_total=450
        db.session.add(Borrowing(company_id=company.id, lender_name='X銀行', is_subsidiary=False, balance_at_eoy=400, interest_rate=1.0, paid_interest=50))
        db.session.commit()

        # Act
        diff = SoASummaryService.compute_difference(company.id, 'borrowings', Borrowing, 'balance_at_eoy')
        skip_total = SoASummaryService.compute_skip_total(company.id, 'borrowings')

        # Assert
        assert diff['bs_total'] == 300
        assert diff['pl_interest_total'] == 200
        assert diff['breakdown_total'] == 450
        assert diff['difference'] == 50  # (300+200) - 450
        assert skip_total == 500  # 300 + 200


def test_soa_deposits_basic_bs_flow(app, init_database):
    with app.app_context():
        # Arrange master: BS 預貯金のアカウント名を1件（普通預金）
        db.session.add(AccountTitleMaster(
            number=10, name='普通預金', statement_name='資産', major_category='資産',
            middle_category='流動資産', minor_category='', breakdown_document='預貯金', master_type='BS'
        ))
        db.session.commit()

        company = Company.query.first()
        # AccountingData: BS 普通預金=1000
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

        # Act
        diff = SoASummaryService.compute_difference(company.id, 'deposits', None, 'balance')
        skip_total = SoASummaryService.compute_skip_total(company.id, 'deposits')

        # Assert: breakdown_total は 0（レコード未登録）
        assert diff['bs_total'] == 1000
        assert diff['breakdown_total'] == 0
        assert diff['difference'] == 1000
        assert skip_total == 1000

