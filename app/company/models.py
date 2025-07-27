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
    name = db.Column(db.String(100), nullable=False)
    group = db.Column(db.String(100))
    joined_date = db.Column(db.String(10))
    relationship = db.Column(db.String(50))
    address = db.Column(db.String(200))
    shares_held = db.Column(db.Integer)
    voting_rights = db.Column(db.Integer)
    position = db.Column(db.String(50))
    investment_amount = db.Column(db.Integer)
    
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('employees', lazy=True))

    def __repr__(self):
        return f'<Employee {self.name}>'

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

# ▼▼▼▼▼ ここから追加 ▼▼▼▼▼
class Deposit(db.Model):
    """預貯金等の内訳モデル"""
    id = db.Column(db.Integer, primary_key=True)
    financial_institution = db.Column(db.String(100), nullable=False) # 金融機関名
    branch_name = db.Column(db.String(100), nullable=False)          # 支店名
    account_type = db.Column(db.String(50), nullable=False)          # 預金種類
    account_number = db.Column(db.String(50), nullable=False)        # 口座番号
    balance = db.Column(db.Integer, nullable=False)                  # 期末現在高
    remarks = db.Column(db.String(200))                              # 摘要
    
    # Companyモデルとのリレーションシップ
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('deposits', lazy=True))

    def __repr__(self):
        return f'<Deposit {self.financial_institution}>'
# ▲▲▲▲▲ ここまで追加 ▲▲▲▲▲
