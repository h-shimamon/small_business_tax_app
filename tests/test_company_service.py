import datetime as dt

from app.company.forms.declaration import CompanyForm
from app.company.models import User
from app.company.services.company_service import CompanyService
from app.extensions import db


def _form_payload(**overrides):
    base = {
        'corporate_number': '1234567890123',
        'company_name': '株式会社テスト1',
        'company_name_kana': 'カブシキガイシャテストイチ',
        'zip_code': '1000001',
        'prefecture': '東京都',
        'city': '千代田区',
        'address': 'テスト1-1-1',
        'phone_number': '0312345678',
        'homepage': '',
        'establishment_date': dt.date(2023, 1, 1),
        'capital_limit': True,
        'is_supported_industry': True,
        'is_excluded_business': True,
        'industry_type': 'ソフトウェア',
        'industry_code': '39',
        'reference_number': 'REF-001',
    }
    base.update(overrides)
    return base


def test_company_service_updates_excluded_flag_for_existing_company(app, init_database):
    with app.app_context(), app.test_request_context():
        user = User.query.filter_by(username='testuser1').first()
        assert user is not None
        payload = _form_payload()
        form = CompanyForm(data=payload)
        company = CompanyService.create_or_update_company(form, user.id)

        assert company.is_excluded_business is True
        assert company.is_not_excluded_business is False


def test_company_service_creates_company_with_inverted_compatibility(app, init_database):
    with app.app_context(), app.test_request_context():
        new_user = User(username='newuser', email='new@example.com')
        new_user.set_password('password')
        db.session.add(new_user)
        db.session.commit()

        payload = _form_payload(
            corporate_number='5555555555555',
            company_name='株式会社ニュー',
            company_name_kana='カブシキガイシャニュー',
            is_excluded_business=False,
        )
        form = CompanyForm(data=payload)
        company = CompanyService.create_or_update_company(form, new_user.id)

        assert company.is_excluded_business is False
        assert company.is_not_excluded_business is True

        company.is_not_excluded_business = False
        assert company.is_excluded_business is True
