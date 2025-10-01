from __future__ import annotations

from app.extensions import db
from app.models_utils.date_sync import attach_date_string_sync


class Deposit(db.Model):
    """預貯金等の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    financial_institution = db.Column(db.String(100), nullable=False)
    branch_name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.String(50), nullable=False)
    balance = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('deposits', lazy=True))

    def __repr__(self):
        return f'<Deposit {self.financial_institution}>'


class NotesReceivable(db.Model):
    """受取手形の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    drawer = db.Column(db.String(100), nullable=False)
    registration_number = db.Column(db.String(20))
    issue_date = db.Column(db.String(10), nullable=False)
    issue_date_date = db.Column(db.Date)
    due_date = db.Column(db.String(10), nullable=False)
    due_date_date = db.Column(db.Date)
    payer_bank = db.Column(db.String(100), nullable=False)
    payer_branch = db.Column(db.String(100))
    amount = db.Column(db.Integer, nullable=False)
    discount_bank = db.Column(db.String(100))
    discount_branch = db.Column(db.String(100))
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('notes_receivable', lazy=True))

    def __repr__(self):
        return f'<NotesReceivable {self.drawer}>'


class AccountsReceivable(db.Model):
    """売掛金（未収入金）の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)
    partner_name = db.Column(db.String(100), nullable=False)
    registration_number = db.Column(db.String(20))
    is_subsidiary = db.Column(db.Boolean, default=False)
    partner_address = db.Column(db.String(200), nullable=False)
    balance_at_eoy = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('accounts_receivable', lazy=True))

    def __repr__(self):
        return f'<AccountsReceivable {self.partner_name}>'


class TemporaryPayment(db.Model):
    """仮払金（前渡金）の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)
    partner_name = db.Column(db.String(100), nullable=False)
    registration_number = db.Column(db.String(20))
    is_subsidiary = db.Column(db.Boolean, default=False)
    partner_address = db.Column(db.String(200))
    relationship = db.Column(db.String(100))
    balance_at_eoy = db.Column(db.Integer, nullable=False)
    transaction_details = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('temporary_payments', lazy=True))

    def __repr__(self):
        return f'<TemporaryPayment {self.partner_name}>'


class LoansReceivable(db.Model):
    """貸付金及び受取利息の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(20))
    borrower_name = db.Column(db.String(100), nullable=False)
    borrower_address = db.Column(db.String(200))
    relationship = db.Column(db.String(100))
    balance_at_eoy = db.Column(db.Integer, nullable=False)
    received_interest = db.Column(db.Integer)
    interest_rate = db.Column(db.Float, nullable=False)
    collateral_details = db.Column(db.String(200))
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('loans_receivable', lazy=True))


class Inventory(db.Model):
    """棚卸資産の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    unit_price = db.Column(db.Integer, nullable=False)
    balance_at_eoy = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('inventories', lazy=True))


class Security(db.Model):
    """有価証券の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    security_type = db.Column(db.String(50), nullable=False)
    issuer = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer)
    balance_at_eoy = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('securities', lazy=True))


class FixedAsset(db.Model):
    """固定資産（土地、建物等）の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    asset_type = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    area = db.Column(db.Float)
    balance_at_eoy = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('fixed_assets', lazy=True))


class NotesPayable(db.Model):
    """支払手形の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(20))
    payee = db.Column(db.String(100), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    payer_bank = db.Column(db.String(100))
    payer_branch = db.Column(db.String(100))
    amount = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('notes_payable', lazy=True))


class AccountsPayable(db.Model):
    """買掛金（未払金・未払費用）の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)
    partner_name = db.Column(db.String(100), nullable=False)
    registration_number = db.Column(db.String(20))
    is_subsidiary = db.Column(db.Boolean, default=False)
    partner_address = db.Column(db.String(200))
    balance_at_eoy = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('accounts_payable', lazy=True))


class TemporaryReceipt(db.Model):
    """仮受金（前受金・預り金）の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)
    partner_name = db.Column(db.String(100), nullable=False)
    balance_at_eoy = db.Column(db.Integer, nullable=False)
    transaction_details = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('temporary_receipts', lazy=True))


class Borrowing(db.Model):
    """借入金及び支払利子の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    lender_name = db.Column(db.String(100), nullable=False)
    is_subsidiary = db.Column(db.Boolean, default=False)
    balance_at_eoy = db.Column(db.Integer, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    paid_interest = db.Column(db.Integer)
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('borrowings', lazy=True))


class ExecutiveCompensation(db.Model):
    """役員報酬手当等及び人件費の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    shareholder_name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(100))
    position = db.Column(db.String(100))
    base_salary = db.Column(db.Integer)
    other_allowances = db.Column(db.Integer)
    total_compensation = db.Column(db.Integer, nullable=False)

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('executive_compensations', lazy=True))


class LandRent(db.Model):
    """地代家賃等の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)
    lessor_name = db.Column(db.String(100), nullable=False)
    property_details = db.Column(db.String(200))
    rent_paid = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('land_rents', lazy=True))


class Miscellaneous(db.Model):
    """雑益、雑損失等の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('miscellaneous_items', lazy=True))


attach_date_string_sync(NotesReceivable, 'issue_date', 'issue_date_date')
attach_date_string_sync(NotesReceivable, 'due_date', 'due_date_date')
