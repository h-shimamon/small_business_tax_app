# app/company/models.py

from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Company(db.Model):
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
    is_not_excluded_business = db.Column(db.Boolean, default=True)
    is_excluded_business = db.Column(db.Boolean, default=False)
    industry_type = db.Column(db.String(50))
    industry_code = db.Column(db.String(10))
    reference_number = db.Column(db.String(20))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    user = db.relationship('User', backref=db.backref('company', uselist=False))

    # --- 申告情報 ---
    accounting_period_start = db.Column(db.String(10))
    accounting_period_end = db.Column(db.String(10))
    term_number = db.Column(db.Integer)
    office_count = db.Column(db.String(10))
    declaration_type = db.Column(db.String(10))
    tax_system = db.Column(db.String(10))
    
    # --- 代表者情報 ---
    representative_name = db.Column(db.String(100))
    representative_kana = db.Column(db.String(100))
    representative_position = db.Column(db.String(100))
    representative_status = db.Column(db.String(20))
    representative_zip_code = db.Column(db.String(7))
    representative_prefecture = db.Column(db.String(10))
    representative_city = db.Column(db.String(50))
    representative_address = db.Column(db.String(200))
    
    # --- 経理責任者 ---
    accounting_manager_name = db.Column(db.String(100))
    accounting_manager_kana = db.Column(db.String(100))
    
    # --- 決算日・延長 ---
    closing_date = db.Column(db.String(10))
    is_corp_tax_extended = db.Column(db.Boolean, default=False)
    is_biz_tax_extended = db.Column(db.Boolean, default=False)
    
    # --- 従業者数 ---
    employee_count_at_eoy = db.Column(db.Integer)
    
    # --- 税理士情報 ---
    tax_accountant_name = db.Column(db.String(100))
    tax_accountant_phone = db.Column(db.String(20))
    tax_accountant_zip = db.Column(db.String(7))
    tax_accountant_prefecture = db.Column(db.String(10))
    tax_accountant_city = db.Column(db.String(50))
    tax_accountant_address = db.Column(db.String(200))

    # --- 還付口座 ---
    refund_bank_name = db.Column(db.String(100))
    refund_branch_name = db.Column(db.String(100))
    refund_account_type = db.Column(db.String(10))
    refund_account_number = db.Column(db.String(20))


    def __repr__(self):
        return f'<Company {self.company_name}>'

class Shareholder(db.Model):
    __tablename__ = 'shareholder'
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

    def __repr__(self):
        return f'<Office {self.name}>'

class Deposit(db.Model):
    """預貯金等の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    financial_institution = db.Column(db.String(100), nullable=False) # 金融機関名
    branch_name = db.Column(db.String(100), nullable=False)          # 支店名
    account_type = db.Column(db.String(50), nullable=False)          # 預金種類
    account_number = db.Column(db.String(50), nullable=False)        # 口座番号
    balance = db.Column(db.Integer, nullable=False)                  # 期末現在高
    remarks = db.Column(db.String(200))                              # 摘要
    
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('deposits', lazy=True))

    def __repr__(self):
        return f'<Deposit {self.financial_institution}>'

class NotesReceivable(db.Model):
    """受取手形の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    drawer = db.Column(db.String(100), nullable=False)              # 振出人
    registration_number = db.Column(db.String(20))                  # 登録番号（法人番号）
    issue_date = db.Column(db.String(10), nullable=False)           # 振出年月日
    due_date = db.Column(db.String(10), nullable=False)             # 支払期日
    payer_bank = db.Column(db.String(100), nullable=False)          # 支払銀行名
    payer_branch = db.Column(db.String(100))                        # 支払支店名
    amount = db.Column(db.Integer, nullable=False)                  # 金額
    discount_bank = db.Column(db.String(100))                       # 割引銀行名
    discount_branch = db.Column(db.String(100))                     # 割引支店名
    remarks = db.Column(db.String(200))                             # 摘要

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('notes_receivable', lazy=True))

    def __repr__(self):
        return f'<NotesReceivable {self.drawer}>'

class AccountsReceivable(db.Model):
    """売掛金（未収入金）の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)         # 科目
    partner_name = db.Column(db.String(100), nullable=False)        # 取引先名
    registration_number = db.Column(db.String(20))                  # 登録番号（法人番号）
    is_subsidiary = db.Column(db.Boolean, default=False)            # 関係会社
    partner_address = db.Column(db.String(200), nullable=False)     # 取引先住所
    balance_at_eoy = db.Column(db.Integer, nullable=False)          # 期末現在高
    remarks = db.Column(db.String(200))                             # 摘要

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('accounts_receivable', lazy=True))

    def __repr__(self):
        return f'<AccountsReceivable {self.partner_name}>'

class TemporaryPayment(db.Model):
    """仮払金（前渡金）の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)         # 科目
    partner_name = db.Column(db.String(100), nullable=False)        # 取引先名
    registration_number = db.Column(db.String(20))                  # 登録番号（法人番号）
    is_subsidiary = db.Column(db.Boolean, default=False)            # 関係会社
    partner_address = db.Column(db.String(200))                     # 取引先住所
    relationship = db.Column(db.String(100))                        # 法人・代表者との関係
    balance_at_eoy = db.Column(db.Integer, nullable=False)          # 期末現在高
    transaction_details = db.Column(db.String(200))                 # 取引の内容

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('temporary_payments', lazy=True))

    def __repr__(self):
        return f'<TemporaryPayment {self.partner_name}>'

# ▼▼▼▼▼ ここから新規追加 ▼▼▼▼▼

class LoansReceivable(db.Model):
    """貸付金及び受取利息の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    borrower_name = db.Column(db.String(100), nullable=False)       # 貸付先
    is_subsidiary = db.Column(db.Boolean, default=False)            # 関係会社
    borrower_address = db.Column(db.String(200))                    # 貸付先住所
    balance_at_eoy = db.Column(db.Integer, nullable=False)          # 期末現在高
    interest_rate = db.Column(db.Float, nullable=False)             # 利率
    received_interest = db.Column(db.Integer)                       # 受取利息
    remarks = db.Column(db.String(200))                             # 摘要
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('loans_receivable', lazy=True))

class Inventory(db.Model):
    """棚卸資産の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)           # 商品・製品等の名称
    location = db.Column(db.String(200))                            # 保管場所
    quantity = db.Column(db.Float, nullable=False)                  # 数量
    unit = db.Column(db.String(20))                                 # 単位
    unit_price = db.Column(db.Integer, nullable=False)              # 単価
    balance_at_eoy = db.Column(db.Integer, nullable=False)          # 期末現在高
    remarks = db.Column(db.String(200))                             # 摘要
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('inventories', lazy=True))

class Security(db.Model):
    """有価証券の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    security_type = db.Column(db.String(50), nullable=False)        # 種類（株式、債券など）
    issuer = db.Column(db.String(100), nullable=False)              # 銘柄・発行者
    quantity = db.Column(db.Integer)                                # 数量
    balance_at_eoy = db.Column(db.Integer, nullable=False)          # 期末現在高
    remarks = db.Column(db.String(200))                             # 摘要
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('securities', lazy=True))

class FixedAsset(db.Model):
    """固定資産（土地、建物等）の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    asset_type = db.Column(db.String(50), nullable=False)           # 種類
    location = db.Column(db.String(200), nullable=False)            # 所在地
    area = db.Column(db.Float)                                      # 面積（㎡）
    balance_at_eoy = db.Column(db.Integer, nullable=False)          # 期末現在高
    remarks = db.Column(db.String(200))                             # 摘要
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('fixed_assets', lazy=True))

class NotesPayable(db.Model):
    """支払手形の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    payee = db.Column(db.String(100), nullable=False)               # 支払先
    issue_date = db.Column(db.Date, nullable=False)                 # 振出年月日
    due_date = db.Column(db.Date, nullable=False)                   # 支払期日
    amount = db.Column(db.Integer, nullable=False)                  # 金額
    remarks = db.Column(db.String(200))                             # 摘要
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('notes_payable', lazy=True))

class AccountsPayable(db.Model):
    """買掛金（未払金・未払費用）の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)         # 科目
    partner_name = db.Column(db.String(100), nullable=False)        # 取引先名
    is_subsidiary = db.Column(db.Boolean, default=False)            # 関係会社
    partner_address = db.Column(db.String(200))                     # 取引先住所
    balance_at_eoy = db.Column(db.Integer, nullable=False)          # 期末現在高
    remarks = db.Column(db.String(200))                             # 摘要
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('accounts_payable', lazy=True))

class TemporaryReceipt(db.Model):
    """仮受金（前受金・預り金）の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)         # 科目
    partner_name = db.Column(db.String(100), nullable=False)        # 相手先
    balance_at_eoy = db.Column(db.Integer, nullable=False)          # 期末現在高
    transaction_details = db.Column(db.String(200))                 # 取引の内容
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('temporary_receipts', lazy=True))

class Borrowing(db.Model):
    """借入金及び支払利子の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    lender_name = db.Column(db.String(100), nullable=False)         # 借入先
    is_subsidiary = db.Column(db.Boolean, default=False)            # 関係会社
    balance_at_eoy = db.Column(db.Integer, nullable=False)          # 期末現在高
    interest_rate = db.Column(db.Float, nullable=False)             # 利率
    paid_interest = db.Column(db.Integer)                           # 支払利子
    remarks = db.Column(db.String(200))                             # 摘要
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('borrowings', lazy=True))

class ExecutiveCompensation(db.Model):
    """役員報酬手当等及び人件費の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    shareholder_name = db.Column(db.String(100), nullable=False)       # 氏名
    relationship = db.Column(db.String(100))                        # 関係
    position = db.Column(db.String(100))                            # 役職
    base_salary = db.Column(db.Integer)                             # 基本給
    other_allowances = db.Column(db.Integer)                        # その他手当
    total_compensation = db.Column(db.Integer, nullable=False)      # 総額
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('executive_compensations', lazy=True))

class LandRent(db.Model):
    """地代家賃等の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)         # 科目
    lessor_name = db.Column(db.String(100), nullable=False)         # 支払先
    property_details = db.Column(db.String(200))                    # 物件の詳細
    rent_paid = db.Column(db.Integer, nullable=False)               # 支払賃借料
    remarks = db.Column(db.String(200))                             # 摘要
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('land_rents', lazy=True))

class Miscellaneous(db.Model):
    """雑益、雑損失等の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)         # 科目
    details = db.Column(db.String(200), nullable=False)             # 内容
    amount = db.Column(db.Integer, nullable=False)                  # 金額
    remarks = db.Column(db.String(200))                             # 摘要
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('miscellaneous_items', lazy=True))

# ▲▲▲▲▲ ここまで新規追加 ▲▲▲▲▲

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
    master_type = db.Column(db.String, nullable=False) # BS or PL

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

    # userとmaster_accountへのリレーションシップを定義
    user = db.relationship('User', backref=db.backref('account_mappings', lazy=True))
    master_account = db.relationship('AccountTitleMaster', backref=db.backref('user_mappings', lazy=True))

    # user_id と original_account_name の組み合わせでユニーク制約を設ける
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
    """
    生成された財務諸表データ（貸借対照表、損益計算書）を永続化するためのモデル。
    会計年度ごとにレコードが作成されることを想定。
    """
    __tablename__ = 'accounting_data'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False, index=True)
    company = db.relationship('Company', backref=db.backref('accounting_data', lazy='dynamic'))
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    data = db.Column(db.JSON, nullable=False) # 財務諸表本体
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
