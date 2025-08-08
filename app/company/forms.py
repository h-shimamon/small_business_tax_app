# app/company/forms.py

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, SelectField, FileField, RadioField, BooleanField, IntegerField, TextAreaField, FloatField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class SoftwareSelectionForm(FlaskForm):
    """会計ソフト選択用フォーム"""
    accounting_software = RadioField(
        '会計ソフト',
        choices=[
            ('yayoi', '弥生会計'),
            ('freee', 'freee'),
            ('moneyforward', 'マネーフォワード'),
            ('other', 'その他')
        ],
        validators=[DataRequired(message='会計ソフトを選択してください。')]
    )
    submit = SubmitField('次へ進む')
from datetime import datetime

class CompanyForm(FlaskForm):
    """会社の基本情報を登録・編集するためのフォーム"""
    corporate_number = StringField('法人番号', validators=[DataRequired(), Length(min=13, max=13)])
    company_name = StringField('法人名', validators=[DataRequired(), Length(max=100)])
    company_name_kana = StringField('フリガナ', validators=[DataRequired(), Length(max=100)])
    zip_code = StringField('郵便番号', validators=[DataRequired(), Length(min=7, max=7)])
    prefecture = StringField('都道府県', validators=[DataRequired(), Length(max=10)])
    city = StringField('市区町村', validators=[DataRequired(), Length(max=50)])
    address = StringField('番地以降の住所', validators=[DataRequired(), Length(max=200)])
    phone_number = StringField('電話番号', validators=[DataRequired(), Length(max=20)])
    homepage = StringField('ホームページアドレス', validators=[Optional(), Length(max=200)])
    establishment_date = DateField('設立年月日', format='%Y-%m-%d', validators=[DataRequired()])
    capital_limit = BooleanField('定款上の会計期間が１年間ですか？', default=False)
    is_supported_industry = BooleanField('電気・ガス供給業及び保険業に該当していませんか？', default=False)
    is_not_excluded_business = BooleanField('資本金または出資金の額が1億円以下の中小法人ですか？', default=False)
    is_excluded_business = BooleanField('適用除外事業者に該当していませんか？', default=False)
    industry_type = StringField('業種', validators=[Optional(), Length(max=50)])
    industry_code = StringField('業種番号', validators=[Optional(), Length(max=10)])
    reference_number = StringField('整理番号', validators=[Optional(), Length(max=20)])
    submit = SubmitField('保存する')

class LoginForm(FlaskForm):
    """ログインフォーム"""
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    remember_me = BooleanField('ログイン状態を保持する')
    submit = SubmitField('ログイン')

class EmployeeForm(FlaskForm):
    """従業員登録・編集フォーム"""
    employee_number = StringField('社員番号', validators=[Optional(), Length(max=20)])
    last_name = StringField('姓', validators=[DataRequired(message="姓は必須です。"), Length(max=50)])
    first_name = StringField('名', validators=[DataRequired(message="名は必須です。"), Length(max=50)])
    last_name_kana = StringField('セイ', validators=[DataRequired(message="セイは必須です。"), Length(max=50)])
    first_name_kana = StringField('メイ', validators=[DataRequired(message="メイは必須です。"), Length(max=50)])
    joined_date = DateField('入社年月日', format='%Y-%m-%d', validators=[Optional()])
    address = StringField('住所', validators=[Optional(), Length(max=200)])
    is_officer = RadioField('役員区分', choices=[(True, '役員である'), (False, '役員ではない')], default=False, coerce=lambda x: x is True or x == 'True')
    officer_position = StringField('役職名', validators=[Optional(), Length(max=100)])
    relationship = StringField('法人・代表者との関係', validators=[Optional(), Length(max=100)])
    shares_held = IntegerField('保有株式数', validators=[Optional()])
    voting_rights = IntegerField('議決権の数', validators=[Optional()])
    submit = SubmitField('登録する')

class DeclarationForm(FlaskForm):
    """申告情報を登録・編集するためのフォーム"""
    
    # --- 基本項目 ---
    accounting_period_start = DateField('会計期間 開始', validators=[Optional()])
    accounting_period_end = DateField('会計期間 終了', validators=[Optional()])
    office_count = RadioField(
        '事業所の数',
        choices=[('one', '１箇所'), ('multiple', '２箇所以上')],
        validators=[Optional()]
    )
    declaration_type = RadioField(
        '申告区分',
        choices=[('blue', '青色申告'), ('white', '白色申告')],
        validators=[Optional()]
    )
    tax_system = RadioField(
        '消費税経理方式',
        choices=[('included', '税込経理方式'), ('excluded', '税抜経理方式')],
        validators=[Optional()]
    )

    # --- (その他の項目は省略) ---
    representative_name = StringField('氏名', validators=[Optional()])
    representative_kana = StringField('ふりがな', validators=[Optional()])
    representative_position = StringField('役職', validators=[Optional()])
    representative_status = SelectField(
        '常勤・非常勤の別',
        choices=[('full_time', '常勤'), ('part_time', '非常勤')],
        validators=[Optional()]
    )
    representative_zip_code = StringField('郵便番号', validators=[Optional()])
    representative_prefecture = StringField('都道府県', validators=[Optional()])
    representative_city = StringField('市区町村', validators=[Optional()])
    representative_address = StringField('住所', validators=[Optional()])
    accounting_manager_name = StringField('氏名', validators=[Optional()])
    accounting_manager_kana = StringField('ふりがな', validators=[Optional()])
    closing_date = DateField('決算確定年月日', validators=[Optional()])
    is_corp_tax_extended = BooleanField('法人税の申告期限を延長している', default=False)
    is_biz_tax_extended = BooleanField('事業税の申告期限を延長している', default=False)
    employee_count_at_eoy = IntegerField('期末従業者数', validators=[Optional()])
    tax_accountant_name = StringField('氏名', validators=[Optional()])
    tax_accountant_phone = StringField('電話番号', validators=[Optional()])
    tax_accountant_zip = StringField('郵便番号', validators=[Optional()])
    tax_accountant_prefecture = StringField('都道府県', validators=[Optional()])
    tax_accountant_city = StringField('市区町村', validators=[Optional()])
    tax_accountant_address = StringField('住所', validators=[Optional()])
    refund_bank_name = StringField('銀行名', validators=[Optional()])
    refund_bank_type = SelectField(
        '金融機関種別',
        choices=[
            ('', '選択してください'),
            ('bank', '銀行'),
            ('shinkin', '金庫'),
            ('kumiai', '組合'),
            ('nokyo', '農協'),
            ('gyokyo', '漁協')
        ],
        validators=[Optional()]
    )
    refund_branch_name = StringField('支店名', validators=[Optional()])
    refund_branch_type = SelectField(
        '支店種別',
        choices=[
            ('', '選択してください'),
            ('honten', '本店'),
            ('shiten', '支店'),
            ('shucchojo', '出張所'),
            ('honjo', '本所'),
            ('shisho', '支所')
        ],
        validators=[Optional()]
    )
    refund_account_type = SelectField(
        '預金種類',
        choices=[('ordinary', '普通'), ('checking', '当座'), ('savings', '貯蓄')],
        validators=[Optional()]
    )
    refund_account_number = StringField('口座番号', validators=[Optional()])

    submit = SubmitField('保存する')

class OfficeForm(FlaskForm):
    """事業所登録・編集フォーム"""
    office_name = StringField('事業所名', validators=[DataRequired(message="事業所名は必須です。"), Length(max=100)])
    zip_code = StringField('郵便番号', validators=[Optional(), Length(max=8)])
    prefecture = StringField('都道府県', validators=[Optional(), Length(max=20)])
    city = StringField('市区町村', validators=[Optional(), Length(max=50)])
    address = StringField('番地以降', validators=[Optional(), Length(max=200)])
    phone_number = StringField('電話番号', validators=[Optional(), Length(max=20)])
    opening_date = DateField('開設年月日', format='%Y-%m-%d', validators=[Optional()])
    closing_date = DateField('廃止年月日', format='%Y-%m-%d', validators=[Optional()])
    employee_count = IntegerField('従業者数', validators=[Optional()])
    submit = SubmitField('登録する')

class AccountingSelectionForm(FlaskForm):
    """会計データ選択画面のフォーム"""
    current_year = datetime.now().year
    years = [(str(y), f'{y}年') for y in range(current_year, current_year - 10, -1)]

    target_year = SelectField(
        '対象年度', 
        choices=years, 
        validators=[DataRequired(message="対象年度を選択してください。")]
    )
    target_period = RadioField(
        '対象期間',
        choices=[('first_half', '上期'), ('second_half', '下期'), ('full_year', '通期')],
        default='full_year',
        validators=[DataRequired(message="対象期間を選択してください。")]
    )
    upload_file = FileField(
        '会計データファイル',
        validators=[
            FileRequired(message="ファイルを選択してください。"),
            FileAllowed(['csv'], message='CSVファイルのみアップロードできます。')
        ]
    )
    submit = SubmitField('データ取込開始')

class DataMappingForm(FlaskForm):
    """データマッピング画面の動的ベースフォーム"""
    submit = SubmitField('マッピングを確定して次へ')

class FileUploadForm(FlaskForm):
    """共通のファイルアップロードフォーム"""
    upload_file = FileField(
        'データファイル',
        validators=[
            FileRequired(message="ファイルを選択してください。"),
            FileAllowed(['csv', 'txt'], message='CSVまたはTXTファイルのみアップロードできます。')
        ]
    )
    submit = SubmitField('データ取込開始')

class DepositForm(FlaskForm):
    """預貯金等の登録・編集フォーム"""
    financial_institution = StringField(
        '金融機関名', 
        validators=[DataRequired(message="金融機関名は必須です。"), Length(max=100)]
    )
    branch_name = StringField(
        '支店名', 
        validators=[DataRequired(message="支店名は必須です。"), Length(max=100)]
    )
    account_type = SelectField(
        '預金種類',
        choices=[
            ('普通預金', '普通預金'),
            ('当座預金', '当座預金'),
            ('通知預金', '通知預金'),
            ('定期預金', '定期預金'),
            ('定期積金', '定期積金'),
            ('別段預金', '別段預金'),
            ('納税準備預金', '納税準備預金'),
            ('その他', 'その他')
        ],
        validators=[DataRequired(message="預金種類は必須です。")]
    )
    account_number = StringField(
        '口座番号', 
        validators=[DataRequired(message="口座番号は必須です。"), Length(max=50)]
    )
    balance = IntegerField(
        '期末現在高', 
        validators=[DataRequired(message="期末現在高は必須です。")]
    )
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class NotesReceivableForm(FlaskForm):
    """受取手形の登録・編集フォーム"""
    drawer = StringField(
        '振出人',
        validators=[DataRequired(message="振出人は必須です。"), Length(max=100)]
    )
    registration_number = StringField(
        '登録番号（法人番号）',
        validators=[Optional(), Length(max=20)]
    )
    issue_date = DateField(
        '振出年月日',
        format='%Y-%m-%d',
        validators=[DataRequired(message="振出年月日は必須です。")]
    )
    due_date = DateField(
        '支払期日',
        format='%Y-%m-%d',
        validators=[DataRequired(message="支払期日は必須です。")]
    )
    payer_bank = StringField(
        '支払銀行名',
        validators=[DataRequired(message="支払銀行名は必須です。"), Length(max=100)]
    )
    payer_branch = StringField(
        '支払支店名',
        validators=[Optional(), Length(max=100)]
    )
    amount = IntegerField(
        '金額',
        validators=[DataRequired(message="金額は必須です。")]
    )
    discount_bank = StringField(
        '割引銀行名',
        validators=[Optional(), Length(max=100)]
    )
    discount_branch = StringField(
        '割引支店名',
        validators=[Optional(), Length(max=100)]
    )
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class AccountsReceivableForm(FlaskForm):
    """売掛金（未収入金）の登録・編集フォーム"""
    account_name = SelectField(
        '科目',
        choices=[
            ('売掛金', '売掛金'),
            ('未収入金', '未収入金')
        ],
        validators=[DataRequired(message="科目は��須です。")]
    )
    partner_name = StringField(
        '取引先名',
        validators=[DataRequired(message="取引先名は必須です。"), Length(max=100)]
    )
    registration_number = StringField(
        '登録番号（法人番号）',
        validators=[Optional(), Length(max=20)]
    )
    is_subsidiary = BooleanField('関係会社')
    partner_address = StringField(
        '取引先住所',
        validators=[DataRequired(message="取引先住所は必須です。"), Length(max=200)]
    )
    balance_at_eoy = IntegerField(
        '期末現在高',
        validators=[DataRequired(message="期末現在高は必須です。")]
    )
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class TemporaryPaymentForm(FlaskForm):
    """仮払金（前渡金）の登録・編集フォーム"""
    account_name = SelectField(
        '科目',
        choices=[
            ('仮払金', '仮払金'),
            ('前渡金', '前渡金')
        ],
        validators=[DataRequired(message="科目は必須です。")]
    )
    partner_name = StringField(
        '取引先名',
        validators=[DataRequired(message="取引先名は必須です。"), Length(max=100)]
    )
    registration_number = StringField(
        '登録番号（法人番号）',
        validators=[Optional(), Length(max=20)]
    )
    is_subsidiary = BooleanField('関係会社')
    partner_address = StringField(
        '取引先住所',
        validators=[Optional(), Length(max=200)]
    )
    relationship = StringField(
        '法人・代表者との関係',
        validators=[Optional(), Length(max=100)]
    )
    balance_at_eoy = IntegerField(
        '期末現在高',
        validators=[DataRequired(message="期末現在高は必須です。")]
    )
    transaction_details = TextAreaField(
        '取引の内容', 
        validators=[Optional(), Length(max=200)]
    )
    submit = SubmitField('保存する')

# ▼▼▼▼▼ ここから新規追加 ▼▼▼▼▼

class LoansReceivableForm(FlaskForm):
    """貸付金及び受取利息の登録・編集フォーム"""
    borrower_name = StringField('貸付先', validators=[DataRequired(), Length(max=100)])
    is_subsidiary = BooleanField('関係会社')
    borrower_address = StringField('貸付先住所', validators=[Optional(), Length(max=200)])
    balance_at_eoy = IntegerField('期末現在高', validators=[DataRequired()])
    interest_rate = FloatField('利率（%）', validators=[DataRequired()])
    received_interest = IntegerField('期間中の受取利息', validators=[Optional()])
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class InventoryForm(FlaskForm):
    """棚卸資産の登録・編集フォーム"""
    item_name = StringField('商品・製品等の名称', validators=[DataRequired(), Length(max=100)])
    location = StringField('保管場所', validators=[Optional(), Length(max=200)])
    quantity = FloatField('数量', validators=[DataRequired()])
    unit = StringField('単位', validators=[Optional(), Length(max=20)])
    unit_price = IntegerField('単価', validators=[DataRequired()])
    balance_at_eoy = IntegerField('期末現在高', validators=[DataRequired()])
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class SecurityForm(FlaskForm):
    """有価証券の登録・編集フォーム"""
    security_type = StringField('種類', validators=[DataRequired(), Length(max=50)])
    issuer = StringField('銘柄・発行者', validators=[DataRequired(), Length(max=100)])
    quantity = IntegerField('数量（株・口）', validators=[Optional()])
    balance_at_eoy = IntegerField('期末現在高', validators=[DataRequired()])
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class FixedAssetForm(FlaskForm):
    """固定資産（土地、建物等）の登録・編集フォーム"""
    asset_type = StringField('種類', validators=[DataRequired(), Length(max=50)])
    location = StringField('所在地', validators=[DataRequired(), Length(max=200)])
    area = FloatField('面積（㎡）', validators=[Optional()])
    balance_at_eoy = IntegerField('期末現在高', validators=[DataRequired()])
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class NotesPayableForm(FlaskForm):
    """支払手形の登録・編集フォーム"""
    payee = StringField('支払先', validators=[DataRequired(), Length(max=100)])
    issue_date = DateField('振出年月日', format='%Y-%m-%d', validators=[DataRequired()])
    due_date = DateField('支払期日', format='%Y-%m-%d', validators=[DataRequired()])
    amount = IntegerField('金額', validators=[DataRequired()])
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class AccountsPayableForm(FlaskForm):
    """買掛金（未払金・未払費用）の登録・編集フォーム"""
    account_name = SelectField('科目', choices=[('買掛金', '買掛金'), ('未払金', '未払金'), ('未払費用', '未払費用')], validators=[DataRequired()])
    partner_name = StringField('取引先名', validators=[DataRequired(), Length(max=100)])
    is_subsidiary = BooleanField('関係会社')
    partner_address = StringField('取引先住所', validators=[Optional(), Length(max=200)])
    balance_at_eoy = IntegerField('期末現在高', validators=[DataRequired()])
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class TemporaryReceiptForm(FlaskForm):
    """仮受金（前受金・預り金）の登録・編集フォーム"""
    account_name = SelectField('科目', choices=[('仮受金', '仮受金'), ('前受金', '前受金'), ('預り金', '預り金')], validators=[DataRequired()])
    partner_name = StringField('相手先名', validators=[DataRequired(), Length(max=100)])
    balance_at_eoy = IntegerField('期末現在高', validators=[DataRequired()])
    transaction_details = TextAreaField('取引の内容', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class BorrowingForm(FlaskForm):
    """借入金及び支払利子の登録・編集フォーム"""
    lender_name = StringField('借入先', validators=[DataRequired(), Length(max=100)])
    is_subsidiary = BooleanField('関係会社')
    balance_at_eoy = IntegerField('期末現在高', validators=[DataRequired()])
    interest_rate = FloatField('利率（%）', validators=[DataRequired()])
    paid_interest = IntegerField('期間中の支払利子', validators=[Optional()])
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class ExecutiveCompensationForm(FlaskForm):
    """役員報酬手当等及び人件費の内訳モデル"""
    employee_name = StringField('氏名', validators=[DataRequired(), Length(max=100)])
    relationship = StringField('関係', validators=[Optional(), Length(max=100)])
    position = StringField('役職', validators=[Optional(), Length(max=100)])
    base_salary = IntegerField('基本給', validators=[Optional()])
    other_allowances = IntegerField('その他手当', validators=[Optional()])
    total_compensation = IntegerField('総額', validators=[DataRequired()])
    submit = SubmitField('保存する')

class LandRentForm(FlaskForm):
    """地代家賃等の内訳モデル"""
    account_name = SelectField('科目', choices=[('地代', '地代'), ('家賃', '家賃')], validators=[DataRequired()])
    lessor_name = StringField('支払先', validators=[DataRequired(), Length(max=100)])
    property_details = StringField('物件の詳細', validators=[Optional(), Length(max=200)])
    rent_paid = IntegerField('支払賃借料', validators=[DataRequired()])
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class MiscellaneousForm(FlaskForm):
    """雑益、雑損失等の内訳モデル"""
    account_name = SelectField('科目', choices=[('雑益', '雑益'), ('雑損失', '雑損失')], validators=[DataRequired()])
    details = StringField('内容', validators=[DataRequired(), Length(max=200)])
    amount = IntegerField('金額', validators=[DataRequired()])
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

# ▲▲▲▲▲ ここまで新規追加 ▲▲▲▲▲
