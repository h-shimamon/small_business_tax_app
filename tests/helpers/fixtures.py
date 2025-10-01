from datetime import date
from typing import Optional

from app.company.models import Company, User
from app.extensions import db


def ensure_user(username: str = "testuser1", email: str = "test1@example.com") -> User:
    user = User.query.filter_by(username=username).first()
    if user:
        return user
    user = User(username=username, email=email)
    user.set_password("password")
    db.session.add(user)
    db.session.commit()
    return user


def ensure_company(user: Optional[User] = None, *, name: str = "株式会社テスト1") -> Company:
    if user is None:
        user = ensure_user()
    company = Company.query.filter_by(user_id=user.id).first()
    if company:
        return company
    company = Company(
        user_id=user.id,
        corporate_number='1234567890123',
        company_name=name,
        company_name_kana='カブシキガイシャテストイチ',
        zip_code='1000001',
        prefecture='東京都',
        city='千代田区',
        address='テスト1-1-1',
        phone_number='0312345678',
        establishment_date=date(2023, 1, 1)
    )
    db.session.add(company)
    db.session.commit()
    return company
