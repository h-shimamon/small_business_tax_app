# app/company/models.py

from app import db

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
    establishment_date = db.Column(db.String(10), nullable=False)
    capital_limit = db.Column(db.Boolean, default=True)
    is_supported_industry = db.Column(db.Boolean, default=True)
    is_not_excluded_business = db.Column(db.Boolean, default=True)
    industry_type = db.Column(db.String(50))
    industry_code = db.Column(db.String(10))
    reference_number = db.Column(db.String(20))

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

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(50), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    is_officer = db.Column(db.Boolean, default=False) # Boolean型（真偽値）に修正
    joined_date = db.Column(db.String(10))
    relationship = db.Column(db.String(50))
    address = db.Column(db.String(200))
    shares_held = db.Column(db.Integer)
    voting_rights = db.Column(db.Integer)
    officer_position = db.Column(db.String(100), nullable=True) # 役職名に修正
    # investment_amount = db.Column(db.Integer) の行を完全に削除
    
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('employees', lazy=True))

    def __repr__(self):
        return f'<Employee {self.last_name} {self.first_name}>'

class Office(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    zip_code = db.Column(db.String(7))
    prefecture = db.Column(db.String(50))
    municipality = db.Column(db.String(100))
    address = db.Column(db.String(200))
    phone_number = db.Column(db.String(20))
    opening_date = db.Column(db.String(10))
    closing_date = db.Column(db.String(10))
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

# ▼▼▼▼▼ ここから追加 ▼▼▼▼▼
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
# ▲▲▲▲▲ ここまで追加 ▲▲▲▲▲
