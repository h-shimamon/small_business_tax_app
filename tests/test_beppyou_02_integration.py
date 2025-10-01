from datetime import date

from app import create_app, db
from app.company.models import Company, Shareholder
from app.pdf.beppyou_02 import _collect_rows


def _setup_company(app):
    with app.app_context():
        db.create_all()
        company = Company(
            corporate_number="0000000000000",
            company_name="テスト株式会社",
            company_name_kana="テストカブシキガイシャ",
            zip_code="1000001",
            prefecture="東京都",
            city="千代田区",
            address="テスト1-1-1",
            phone_number="0312345678",
            establishment_date=date(2020, 1, 1),
            user_id=1,
        )
        db.session.add(company)
        db.session.commit()

        # main shareholder
        main = Shareholder(
            company_id=company.id,
            last_name="主株主",
            shares_held=100,
            voting_rights=100,
        )
        db.session.add(main)
        db.session.commit()

        # add multiple related shareholders
        for idx in range(5):
            db.session.add(
                Shareholder(
                    company_id=company.id,
                    parent_id=main.id,
                    last_name=f"関連{idx}",
                    shares_held=10 + idx,
                    voting_rights=10 + idx,
                )
            )
        db.session.commit()
        return company.id


def test_collect_rows_includes_all_related_shareholders():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test',
    })
    company_id = _setup_company(app)
    with app.app_context():
        rows = _collect_rows(company_id, limit=12)
        names = [row['person'].last_name for row in rows]
        # expected: main + 5 related
        assert len(names) == 6
        assert names[0] == '主株主'
        assert set(names[1:]) == {f'関連{i}' for i in range(5)}
