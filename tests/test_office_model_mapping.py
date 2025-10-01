from app.company.forms import OfficeForm
from app.company.models import Company, Office
from app.extensions import db


def test_office_form_aliases(app, init_database):
    with app.app_context():
        company = db.session.query(Company).first()
        office = Office(company_id=company.id, name='本店', municipality='千代田区')
        db.session.add(office)
        db.session.commit()

        # GET 時の初期値がエイリアス経由で取得できること
        form = OfficeForm(obj=office)
        assert form.office_name.data == '本店'
        assert form.city.data == '千代田区'

        # populate_obj でモデル実カラムに正しく反映されること
        edit_form = OfficeForm(data={
            'office_name': '新宿支店',
            'city': '新宿区'
        })
        edit_form.populate_obj(office)
        assert office.name == '新宿支店'
        assert office.municipality == '新宿区'


def test_company_office_count_numeric_helpers(app, init_database):
    with app.app_context():
        company = db.session.query(Company).first()
        company.office_count = 'one'
        assert company.office_count_numeric == 1

        company.office_count_numeric = 2
        assert company.office_count == 'multiple'
        assert company.office_count_numeric == 2

        company.apply_office_count_input('3')
        assert company.office_count == 'multiple'
        assert company.office_count_numeric == 2

        company.apply_office_count_input(None)
        assert company.office_count is None
        assert company.office_count_numeric is None
