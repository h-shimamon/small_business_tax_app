from werkzeug.datastructures import MultiDict

from app.company.models import Company
from app.company.services.statement_of_accounts_service import StatementOfAccountsService
from app.extensions import db
from app.services.soa_registry import STATEMENT_PAGES_CONFIG


def _make_accounts_payable_form(data):
    form_class = STATEMENT_PAGES_CONFIG['accounts_payable']['form']
    return form_class(formdata=MultiDict(data))


def test_accounts_payable_sets_default_account_name(app, init_database):
    with app.app_context():
        company = db.session.query(Company).first()
        service = StatementOfAccountsService(company.id)

        form = _make_accounts_payable_form({
            'partner_name': 'テスト取引先',
            'balance_at_eoy': '1000',
        })
        assert form.validate()

        ok, item, error = service.create_item('accounts_payable', form)

        assert ok is True
        assert error is None
        assert item.account_name == '買掛金'


def test_accounts_payable_update_backfills_missing_account_name(app, init_database):
    with app.app_context():
        company = db.session.query(Company).first()
        service = StatementOfAccountsService(company.id)

        form = _make_accounts_payable_form({
            'partner_name': '更新前',
            'balance_at_eoy': '2000',
        })
        assert form.validate()
        ok, item, _ = service.create_item('accounts_payable', form)
        assert ok is True

        # 手動で欠損させた場合も更新時に既定値が補完されること
        item.account_name = ''
        db.session.commit()

        update_form = _make_accounts_payable_form({
            'partner_name': '更新後',
            'balance_at_eoy': '3000',
        })
        assert update_form.validate()
        ok, updated, error = service.update_item('accounts_payable', item, update_form)

        assert ok is True
        assert error is None
        assert updated.account_name == '買掛金'
