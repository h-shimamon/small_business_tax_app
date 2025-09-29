from __future__ import annotations

from app import db

from .company_core import Company, User


class Beppyo15Breakdown(db.Model):
    """別表15の内訳（交際費等）を管理するモデル"""
    __tablename__ = 'beppyo15_breakdown'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    expense_amount = db.Column(db.Integer, nullable=False)
    deductible_amount = db.Column(db.Integer, nullable=False)
    net_amount = db.Column(db.Integer, nullable=False)
    hospitality_amount = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(200))

    company_id = db.Column(db.Integer, db.ForeignKey('company.id', name='fk_beppyo15_breakdown_company_id'), nullable=False, index=True)
    company = db.relationship('Company', backref=db.backref('beppyo15_breakdowns', lazy=True))

    def __repr__(self):
        return f'<Beppyo15Breakdown {self.subject}>'


class AccountTitleMaster(db.Model):
    """勘定科目マスターモデル"""
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, nullable=False)
    statement_name = db.Column(db.String)
    major_category = db.Column(db.String)
    middle_category = db.Column(db.String)
    minor_category = db.Column(db.String)
    breakdown_document = db.Column(db.String)
    master_type = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'<AccountTitleMaster {self.name}>'


class UserAccountMapping(db.Model):
    """ユーザー定義の勘定科目マッピングモデル"""
    __tablename__ = 'user_account_mapping'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    software_name = db.Column(db.String(50), nullable=False, comment="会計ソフト名 (例: moneyforward)")
    original_account_name = db.Column(db.String(255), nullable=False, comment="ユーザーファイル上の勘定科目名")
    master_account_id = db.Column(db.Integer, db.ForeignKey('account_title_master.id'), nullable=False, comment="紐付け先のマスター勘定科目ID")
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('account_mappings', lazy=True))
    master_account = db.relationship('AccountTitleMaster', backref=db.backref('user_mappings', lazy=True))

    __table_args__ = (db.UniqueConstraint('user_id', 'original_account_name', name='_user_original_account_uc'),)

    def __repr__(self):
        return f'<UserAccountMapping {self.original_account_name} -> {self.master_account.name}>'


class MasterVersion(db.Model):
    """マスターデータのバージョン管理モデル"""
    __tablename__ = 'master_version'
    id = db.Column(db.Integer, primary_key=True)
    version_hash = db.Column(db.String(64), nullable=False, unique=True)

    def __repr__(self):
        return f'<MasterVersion {self.version_hash}>'


class AccountingData(db.Model):
    """財務諸表データの永続化モデル"""

    __tablename__ = 'accounting_data'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False, index=True)
    company = db.relationship('Company', backref=db.backref('accounting_data', lazy='dynamic'))
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


class CorporateTaxMaster(db.Model):
    __tablename__ = 'corporate_tax_master'

    id = db.Column(db.Integer, primary_key=True)
    fiscal_start_date = db.Column(db.Date, nullable=False)
    fiscal_end_date = db.Column(db.Date, nullable=False)
    months_standard = db.Column(db.Integer, nullable=False)
    months_truncated = db.Column(db.Integer, nullable=False)

    corporate_tax_rate_u8m = db.Column(db.Numeric(5, 2), nullable=False)
    corporate_tax_rate_o8m = db.Column(db.Numeric(5, 2), nullable=False)
    local_corporate_tax_rate = db.Column(db.Numeric(5, 2), nullable=False)

    enterprise_tax_rate_u4m = db.Column(db.Numeric(5, 2), nullable=False)
    enterprise_tax_rate_4m_8m = db.Column(db.Numeric(5, 2), nullable=False)
    enterprise_tax_rate_o8m = db.Column(db.Numeric(5, 2), nullable=False)

    local_special_tax_rate = db.Column(db.Numeric(5, 2), nullable=False)
    prefectural_corporate_tax_rate = db.Column(db.Numeric(5, 2), nullable=False)
    prefectural_equalization_amount = db.Column(db.Integer, nullable=False)
    municipal_corporate_tax_rate = db.Column(db.Numeric(5, 2), nullable=False)
    municipal_equalization_amount = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    __table_args__ = (
        db.UniqueConstraint('fiscal_start_date', name='ux_corporate_tax_master_fiscal_start'),
    )
