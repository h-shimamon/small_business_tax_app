from datetime import date

from app.company.models import (
    AccountingData,
    AccountTitleMaster,
    Borrowing,
    Company,
    Miscellaneous,
)
from app.company.services.soa_summary_service import SoASummaryService
from app.extensions import db


def _create_accounting_data(company_id: int, payload: dict) -> None:
    db.session.add(
        AccountingData(
            company_id=company_id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            data=payload,
        )
    )
    db.session.commit()


def test_misc_income_difference_zero(app, init_database):
    with app.app_context():
        company = db.session.query(Company).first()
        payload = {
            'profit_loss_statement': {
                'others': {
                    'items': [
                        {'name': '雑収入', 'amount': 1200},
                    ]
                }
            },
            'soa_breakdowns': {
                '雑収入': 1200,
            },
        }
        _create_accounting_data(company.id, payload)
        db.session.add(
            Miscellaneous(
                company_id=company.id,
                account_name='雑収入',
                details='テスト',
                amount=1200,
            )
        )
        db.session.commit()

        diff = SoASummaryService.compute_difference(company.id, 'misc_income', Miscellaneous, 'amount')
        assert diff['difference'] == 0
        assert diff['breakdown_total'] == 1200


def test_borrowings_difference_zero(app, init_database):
    with app.app_context():
        company = db.session.query(Company).first()
        db.session.add(
            AccountTitleMaster(
                number=900,
                name='長期借入金',
                statement_name='負債',
                major_category='負債',
                middle_category='長期負債',
                minor_category='',
                breakdown_document='借入金',
                master_type='BS',
            )
        )
        db.session.commit()
        payload = {
            'balance_sheet': {
                'liabilities': {
                    'items': [
                        {'name': '長期借入金', 'amount': 500},
                    ]
                }
            },
            'profit_loss_statement': {
                'expenses': {
                    'items': [
                        {'name': '支払利息', 'amount': 100},
                    ]
                }
            },
            'soa_breakdowns': {
                '借入金': 500,
            },
        }
        _create_accounting_data(company.id, payload)
        db.session.add(
            Borrowing(
                company_id=company.id,
                lender_name='テスト銀行',
                is_subsidiary=False,
                balance_at_eoy=500,
                interest_rate=1.2,
                paid_interest=100,
            )
        )
        db.session.commit()

        diff = SoASummaryService.compute_difference(company.id, 'borrowings', Borrowing, 'balance_at_eoy')
        assert diff['difference'] == 0
        assert diff['bs_total'] == 500
        assert diff['pl_interest_total'] == 100
        assert diff['breakdown_total'] == 600
