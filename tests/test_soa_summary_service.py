# tests/test_soa_summary_service.py
from datetime import date

from app.company.models import AccountingData, AccountTitleMaster, Borrowing, Company
from app.company.services.soa_summary_service import SoASummaryService
from app.extensions import db


def test_soa_borrowings_difference_and_skip(app, init_database):
    with app.app_context():
        # Arrange master: BS 借入金系と PL 支払利息のアカウントを用意
        borrowing_master = AccountTitleMaster(
            number=1000,
            name='借入金A',
            statement_name='借入金',
            major_category='負債',
            middle_category='流動負債',
            minor_category='',
            breakdown_document='借入金',
            master_type='BS',
        )
        interest_master = AccountTitleMaster(
            number=1500,
            name='支払利息',
            statement_name='営業外費用',
            major_category='費用',
            middle_category='営業外費用',
            minor_category='',
            breakdown_document=None,
            master_type='PL',
        )
        db.session.add_all([borrowing_master, interest_master])
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
        account_balances = {
            str(borrowing_master.id): -300,
            str(interest_master.id): 200,
        }
        db.session.add(AccountingData(
            company_id=company.id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            data={
                **data,
                'account_balances': account_balances,
            },
        ))
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
        deposit_master = AccountTitleMaster(
            number=10,
            name='普通預金',
            statement_name='資産',
            major_category='資産',
            middle_category='流動資産',
            minor_category='',
            breakdown_document='預貯金',
            master_type='BS',
        )
        db.session.add(deposit_master)
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
        db.session.add(AccountingData(
            company_id=company.id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            data={
                **data,
                'account_balances': {str(deposit_master.id): 1000},
            },
        ))
        db.session.commit()

        # Act
        diff = SoASummaryService.compute_difference(company.id, 'deposits', None, 'balance')
        skip_total = SoASummaryService.compute_skip_total(company.id, 'deposits')

        # Assert: breakdown_total は 0（レコード未登録）
        assert diff['bs_total'] == 1000
        assert diff['breakdown_total'] == 0
        assert diff['difference'] == 1000
        assert skip_total == 1000


def test_soa_pl_mappings_executive_and_rent_and_misc(app, init_database):
    with app.app_context():
        # Arrange PL master accounts used by mappings
        for i, name in enumerate(['役員報酬', '役員賞与', '地代家賃', '賃借料', '雑収入', '雑損失']):
            db.session.add(AccountTitleMaster(
                number=2000 + i,
                name=name,
                statement_name='PL',
                major_category='費用/収益',
                middle_category='',
                minor_category='',
                breakdown_document=None,
                master_type='PL',
            ))
        db.session.commit()

        masters = AccountTitleMaster.query.filter(AccountTitleMaster.name.in_(
            ['役員報酬', '役員賞与', '地代家賃', '賃借料', '雑収入', '雑損失']
        )).all()
        name_to_id = {m.name: m.id for m in masters}

        company = Company.query.first()
        data = {
            'balance_sheet': {},
            'profit_loss_statement': {
                'expenses': {'items': [
                    {'name': '役員報酬', 'amount': 300},
                    {'name': '役員賞与', 'amount': 200},
                    {'name': '地代家賃', 'amount': 150},
                    {'name': '賃借料', 'amount': 50},
                    {'name': '雑損失', 'amount': 25},
                ]},
                'revenues': {'items': [
                    {'name': '雑収入', 'amount': 75},
                ]},
            }
        }
        account_balances = {
            str(name_to_id['役員報酬']): 300,
            str(name_to_id['役員賞与']): 200,
            str(name_to_id['地代家賃']): 150,
            str(name_to_id['賃借料']): 50,
            str(name_to_id['雑収入']): 75,
            str(name_to_id['雑損失']): 25,
        }
        db.session.add(AccountingData(
            company_id=company.id,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            data={
                **data,
                'account_balances': account_balances,
            },
        ))
        db.session.commit()

        # Executive compensations mapping = 300 + 200 = 500
        d1 = SoASummaryService.compute_difference(company.id, 'executive_compensations', None, 'total_compensation')
        assert d1['bs_total'] == 500
        assert d1['breakdown_total'] == 0
        assert d1['difference'] == 500

        # Land rents mapping = 150 + 50 = 200
        d2 = SoASummaryService.compute_difference(company.id, 'land_rents', None, 'rent_paid')
        assert d2['bs_total'] == 200
        assert d2['breakdown_total'] == 0
        assert d2['difference'] == 200

        # Miscellaneous income mapping = 75
        d3_income = SoASummaryService.compute_difference(company.id, 'misc_income', None, 'amount')
        assert d3_income['bs_total'] == 75
        assert d3_income['breakdown_total'] == 0
        assert d3_income['difference'] == 75

        # Miscellaneous loss mapping = 25
        d3_loss = SoASummaryService.compute_difference(company.id, 'misc_losses', None, 'amount')
        assert d3_loss['bs_total'] == 25
        assert d3_loss['breakdown_total'] == 0
        assert d3_loss['difference'] == 25
