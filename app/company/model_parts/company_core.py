from __future__ import annotations

import datetime as _dt

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_email_verified = db.Column(db.Boolean, nullable=False, server_default=db.text('0'))
    is_admin = db.Column(db.Boolean, nullable=False, server_default=db.text('0'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)




def _coerce_iso_date(value) -> _dt.date | None:
    if value is None or value == "":
        return None
    if isinstance(value, _dt.date):
        return value
    if isinstance(value, _dt.datetime):
        return value.date()
    try:
        return _dt.date.fromisoformat(str(value))
    except Exception:
        return None


def _iso_or_none(value: _dt.date | None) -> str | None:
    return value.isoformat() if isinstance(value, _dt.date) else None

class Company(db.Model):
    __table_args__ = (
        db.CheckConstraint('employee_count_at_eoy >= 0', name='ck_company_employee_count_non_negative'),
    )
    _OFFICE_COUNT_MAP = {'one': 1, 'multiple': 2}
    _OFFICE_COUNT_REVERSE = {1: 'one', 2: 'multiple'}

    id = db.Column(db.Integer, primary_key=True)
    corporate_number = db.Column(db.String(13), unique=True, nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    company_name_kana = db.Column(db.String(100), nullable=False)
    zip_code = db.Column(db.String(7), nullable=False)
    prefecture = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    homepage = db.Column(db.String(200))
    establishment_date = db.Column(db.Date, nullable=False)
    capital_limit = db.Column(db.Boolean, default=True)
    is_supported_industry = db.Column(db.Boolean, default=True)
    is_excluded_business = db.Column(db.Boolean, default=False)

    @property
    def is_not_excluded_business(self) -> bool | None:
        value = getattr(self, 'is_excluded_business', None)
        if value is None:
            return None
        return not bool(value)

    @is_not_excluded_business.setter
    def is_not_excluded_business(self, value: bool | None) -> None:
        if value is None:
            return
        self.is_excluded_business = not bool(value)

    industry_type = db.Column(db.String(50))
    industry_code = db.Column(db.String(10))
    reference_number = db.Column(db.String(20))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    user = db.relationship('User', backref=db.backref('company', uselist=False))

    accounting_period_start_date = db.Column(db.Date)
    accounting_period_end_date = db.Column(db.Date)

    @property
    def accounting_period_start(self) -> str | None:
        return _iso_or_none(self.accounting_period_start_date)

    @accounting_period_start.setter
    def accounting_period_start(self, value) -> None:
        self.accounting_period_start_date = _coerce_iso_date(value)

    @property
    def accounting_period_end(self) -> str | None:
        return _iso_or_none(self.accounting_period_end_date)

    @accounting_period_end.setter
    def accounting_period_end(self, value) -> None:
        self.accounting_period_end_date = _coerce_iso_date(value)

    term_number = db.Column(db.Integer)
    office_count = db.Column(db.String(10))
    @classmethod
    def _normalize_office_count_value(cls, value: str | int | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, int):
            return cls._OFFICE_COUNT_REVERSE.get(value, 'multiple' if value >= 2 else 'one')
        text = str(value).strip()
        if not text:
            return None
        lowered = text.lower()
        if lowered in cls._OFFICE_COUNT_MAP:
            return lowered
        if lowered.isdigit():
            try:
                numeric = int(lowered)
            except ValueError:
                return lowered
            return cls._OFFICE_COUNT_REVERSE.get(numeric, 'multiple' if numeric >= 2 else 'one')
        return lowered

    @property
    def office_count_numeric(self) -> int | None:
        raw_value = getattr(self, 'office_count', None)
        if raw_value is None:
            return None
        if isinstance(raw_value, int):
            return raw_value
        text = str(raw_value).strip()
        if not text:
            return None
        lowered = text.lower()
        if lowered.isdigit():
            try:
                return int(lowered)
            except ValueError:
                return None
        return self._OFFICE_COUNT_MAP.get(lowered)

    @office_count_numeric.setter
    def office_count_numeric(self, value: str | int | None) -> None:
        self.office_count = self._normalize_office_count_value(value)

    def apply_office_count_input(self, raw_value: str | int | None) -> None:
        self.office_count = self._normalize_office_count_value(raw_value)
    declaration_type = db.Column(db.String(10))
    tax_system = db.Column(db.String(10))

    representative_name = db.Column(db.String(100))
    representative_kana = db.Column(db.String(100))
    representative_position = db.Column(db.String(100))
    representative_status = db.Column(db.String(20))
    representative_zip_code = db.Column(db.String(7))
    representative_prefecture = db.Column(db.String(10))
    representative_city = db.Column(db.String(50))
    representative_address = db.Column(db.String(200))

    accounting_manager_name = db.Column(db.String(100))
    accounting_manager_kana = db.Column(db.String(100))

    closing_date_date = db.Column(db.Date)

    @property
    def closing_date(self) -> str | None:
        return _iso_or_none(self.closing_date_date)

    @closing_date.setter
    def closing_date(self, value) -> None:
        self.closing_date_date = _coerce_iso_date(value)

    is_corp_tax_extended = db.Column(db.Boolean, default=False)
    is_biz_tax_extended = db.Column(db.Boolean, default=False)

    employee_count_at_eoy = db.Column(db.Integer)

    tax_accountant_name = db.Column(db.String(100))
    tax_accountant_phone = db.Column(db.String(20))
    tax_accountant_zip = db.Column(db.String(7))
    tax_accountant_prefecture = db.Column(db.String(10))
    tax_accountant_city = db.Column(db.String(50))
    tax_accountant_address = db.Column(db.String(200))

    refund_bank_name = db.Column(db.String(100))
    refund_bank_type = db.Column(db.String(20))
    refund_branch_name = db.Column(db.String(100))
    refund_branch_type = db.Column(db.String(20))
    refund_account_type = db.Column(db.String(10))
    refund_account_number = db.Column(db.String(20))

    def __repr__(self):
        return f'<Company {self.company_name}>'


class Shareholder(db.Model):
    __tablename__ = 'shareholder'
    __table_args__ = (
        db.CheckConstraint('shares_held >= 0', name='ck_shareholder_shares_non_negative'),
        db.CheckConstraint('voting_rights >= 0', name='ck_shareholder_votes_non_negative'),
    )
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(20), nullable=False, default='individual')
    is_controlled_company = db.Column(db.Boolean, default=False)
    joined_date = db.Column(db.Date)
    relationship = db.Column(db.String(50))
    address = db.Column(db.String(200))
    zip_code = db.Column(db.String(7), nullable=True)
    prefecture_city = db.Column(db.String(100), nullable=True)
    shares_held = db.Column(db.Integer)
    voting_rights = db.Column(db.Integer)
    officer_position = db.Column(db.String(100), nullable=True)
    investment_amount = db.Column(db.Integer, nullable=True)

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('shareholders', lazy=True))

    parent_id = db.Column(db.Integer, db.ForeignKey('shareholder.id', name='fk_shareholder_parent_id'), nullable=True)
    children = db.relationship('Shareholder', backref=db.backref('parent', remote_side=[id]), cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Shareholder {self.last_name}>'


class Office(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    zip_code = db.Column(db.String(7))
    prefecture = db.Column(db.String(50))
    municipality = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone_number = db.Column(db.String(20))
    opening_date = db.Column(db.Date)
    closing_date = db.Column(db.Date)
    employee_count = db.Column(db.Integer)
    office_count = db.Column(db.Integer)

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('offices', lazy=True))

    @property
    def office_name(self):
        return self.name

    @office_name.setter
    def office_name(self, value):
        self.name = value

    @property
    def city(self):
        return self.municipality

    @city.setter
    def city(self, value):
        self.municipality = value

    def __repr__(self):
        return f'<Office {self.name}>'

