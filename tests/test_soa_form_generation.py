import pytest

from app import create_app
from app.company.forms.soa.definitions import get_soa_form_classes


@pytest.fixture(scope='module')
def app_context():
    app = create_app({'TESTING': True, 'WTF_CSRF_ENABLED': False})
    with app.app_context():
        yield app


def test_deposit_form_generated(app_context):
    form_class = get_soa_form_classes()['DepositForm']
    form = form_class(meta={'csrf': False})
    assert 'financial_institution' in form._fields
    assert form.account_type.choices, "account_type should provide select choices"


def test_misc_income_hidden_account_name(app_context):
    form_class = get_soa_form_classes()['MiscellaneousIncomeForm']
    form = form_class(meta={'csrf': False})
    assert form.account_name.data == '雑収入'
    assert form.amount.label.text == '金額'