# app/company/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, SubmitField, RadioField, SelectField, BooleanField
from wtforms.validators import DataRequired, Optional, Length
from wtforms.widgets import TextInput

class EmployeeForm(FlaskForm):
    """従業員情報を登録・編集するためのフォーム"""
    name = StringField('氏名', validators=[DataRequired(message='氏名は必須です。')])
    group = StringField('グループ', validators=[Optional()])
    joined_date = DateField('社員となった日', validators=[Optional()])
    relationship = StringField('続柄', validators=[Optional()])
    address = StringField('住所', validators=[Optional()])
    shares_held = IntegerField('株式数', validators=[Optional()], widget=TextInput())
    voting_rights = IntegerField('議決権', validators=[Optional()], widget=TextInput())
    position = StringField('役職', validators=[Optional()])
    investment_amount = IntegerField('出資金額', validators=[Optional()], widget=TextInput())
    submit = SubmitField('登録する')

class OfficeForm(FlaskForm):
    """事業所の登録・編集フォーム"""
    prefecture = StringField('所属都道府県', validators=[Optional(), Length(max=50)])
    municipality = StringField('所属市区町村', validators=[Optional(), Length(max=100)])
    name = StringField('事業所名', validators=[DataRequired(message="事業所名は必須です。"), Length(max=100)])
    zip_code = StringField('郵便番号', validators=[Optional(), Length(max=7)])
    address = StringField('住所', validators=[Optional(), Length(max=200)])
    phone_number = StringField('電話番号', validators=[Optional(), Length(max=20)])
    opening_date = DateField('開設年月日', format='%Y-%m-%d', validators=[Optional()])
    closing_date = DateField('閉鎖年月日', format='%Y-%m-%d', validators=[Optional()])
    employee_count = IntegerField('従業者数', validators=[Optional()])
    office_count = IntegerField('事業所数', validators=[Optional()])
    submit = SubmitField('保存する')

class AccountingSelectionForm(FlaskForm):
    """会計データ選択用のフォーム"""
    accounting_year = SelectField(
        '対象年度',
        choices=[('2025', '2025年'), ('2024', '2024年'), ('2023', '2023年')],
        validators=[DataRequired(message="年度を選択してください。")]
    )
    accounting_period = RadioField(
        '対象期間',
        choices=[
            ('first_half', '上期'),
            ('second_half', '下期'),
            ('full_year', '通期')
        ],
        default='first_half',
        validators=[DataRequired(message="期間を選択してください。")]
    )

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

    # --- 代表者カテゴリ ---
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

    # --- 経理責任者カテゴリ ---
    accounting_manager_name = StringField('氏名', validators=[Optional()])
    accounting_manager_kana = StringField('ふりがな', validators=[Optional()])

    # --- 決算・申告期限 ---
    closing_date = DateField('決算確定年月日', validators=[Optional()])
    is_corp_tax_extended = BooleanField('法人税の申告期限を延長している', default=False)
    is_biz_tax_extended = BooleanField('事業税の申告期限を延長している', default=False)
    
    # --- その他 ---
    employee_count_at_eoy = IntegerField('期末従業者数', validators=[Optional()])

    # --- 税理士カテゴリ ---
    tax_accountant_name = StringField('氏名', validators=[Optional()])
    tax_accountant_phone = StringField('電話番号', validators=[Optional()])
    tax_accountant_zip = StringField('郵便番号', validators=[Optional()])
    tax_accountant_prefecture = StringField('都道府県', validators=[Optional()])
    tax_accountant_city = StringField('市区町村', validators=[Optional()])
    tax_accountant_address = StringField('住所', validators=[Optional()])

    # --- 還付金受取口座 ---
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
