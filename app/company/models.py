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
    capital_limit = db.Column(db.Boolean, default=True)               # ② 資本金の制限 (既存)
    is_supported_industry = db.Column(db.Boolean, default=True)      # ③ 対応業種の確認
    is_not_excluded_business = db.Column(db.Boolean, default=True)   # ④ 適用除外事業者の確
    capital_limit = db.Column(db.Boolean, default=True)
    industry_type = db.Column(db.String(50))
    industry_code = db.Column(db.String(10))
    reference_number = db.Column(db.String(20))

    # ▼▼▼▼▼ このブロックをここに追加 ▼▼▼▼▼
    # --- 申告情報 ---
    accounting_period_start = db.Column(db.String(10)) # 会計期間 開始
    accounting_period_end = db.Column(db.String(10))   # 会計期間 終了
    term_number = db.Column(db.Integer)                # 期数
    office_count = db.Column(db.String(10))            # 事業所の数 ('one' or 'multiple')
    declaration_type = db.Column(db.String(10))        # 申告区分 ('blue' or 'white')
    tax_system = db.Column(db.String(10))              # 消費税経理方式 ('tax_included' or 'tax_excluded')
    
    # 経理責任者
    accounting_manager_name = db.Column(db.String(100))
    accounting_manager_kana = db.Column(db.String(100))
    
    # 決算日・延長
    closing_date = db.Column(db.String(10))
    is_corp_tax_extended = db.Column(db.Boolean, default=False)
    is_biz_tax_extended = db.Column(db.Boolean, default=False)
    
    # 従業者数
    employee_count_at_eoy = db.Column(db.Integer) # 期末従業者数
    
    # 税理士情報
    tax_accountant_name = db.Column(db.String(100))
    tax_accountant_phone = db.Column(db.String(20))
    tax_accountant_zip = db.Column(db.String(7))
    tax_accountant_prefecture = db.Column(db.String(10))
    tax_accountant_city = db.Column(db.String(50))
    tax_accountant_address = db.Column(db.String(200))

    # 還付口座
    refund_bank_name = db.Column(db.String(100))
    refund_branch_name = db.Column(db.String(100))
    refund_account_type = db.Column(db.String(10))
    refund_account_number = db.Column(db.String(20))
    # ▲▲▲▲▲ ここまで追加 ▲▲▲▲▲


    def __repr__(self):
        return f'<Company {self.company_name}>'
# app/company/models.py (一番下に追記)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)        # 氏名
    group = db.Column(db.String(100))                       # グループ
    joined_date = db.Column(db.String(10))                  # 社員となった日
    relationship = db.Column(db.String(50))                 # 続柄
    address = db.Column(db.String(200))                     # 住所
    shares_held = db.Column(db.Integer)                     # 株式数
    voting_rights = db.Column(db.Integer)                   # 議決権
    position = db.Column(db.String(50))                     # 役職
    investment_amount = db.Column(db.Integer)               # 出資金額
    
    # 外部キー: この社員がどの会社に属しているかを示す
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    # リレーションシップ: Companyモデルからこの社員の情報を逆引きできるようにする
    company = db.relationship('Company', backref=db.backref('employees', lazy=True))

    def __repr__(self):
        return f'<Employee {self.name}>'        