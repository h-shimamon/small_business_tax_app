from __future__ import annotations

from datetime import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import (
    StringField, PasswordField, SubmitField, SelectField, FileField,
    RadioField, BooleanField, IntegerField
)
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, Optional

from .base_fields import CorporateNumberField


class SoftwareSelectionForm(FlaskForm):
    accounting_software = RadioField(
        '会計ソフト',
        choices=[('yayoi', '弥生会計'), ('freee', 'freee'), ('moneyforward', 'マネーフォワード'), ('other', 'その他')],
        validators=[DataRequired(message='会計ソフトを選択してください。')]
    )
    submit = SubmitField('次へ進む')


class CompanyForm(FlaskForm):
    corporate_number = CorporateNumberField(required=True)
    company_name = StringField('法人名', validators=[DataRequired(), Length(max=100)])
    company_name_kana = StringField('フリガナ', validators=[DataRequired(), Length(max=100)])
    # 住所（テンプレート互換のためフィールド名を維持）
    zip_code = StringField('郵便番号', validators=[Optional(), Length(min=7, max=7, message="郵便番号は7桁で入力してください。")])
    prefecture = StringField('都道府県', validators=[Optional(), Length(max=10)])  # TODO: 既存上限に合わせて10を維持
    city = StringField('市区町村', validators=[Optional(), Length(max=50)])
    address = StringField('番地以降の住所', validators=[Optional(), Length(max=200)])
    phone_number = StringField('電話番号', validators=[DataRequired(), Length(max=20)])
    homepage = StringField('ホームページアドレス', validators=[Optional(), Length(max=200)])
    establishment_date = DateField('設立年月日', format='%Y-%m-%d', validators=[DataRequired()], render_kw={'class': 'js-date'})
    capital_limit = BooleanField('定款上の会計期間が１年間ですか？', default=False)
    is_supported_industry = BooleanField('電気・ガス供給業及び保険業に該当していませんか？', default=False)
    is_not_excluded_business = BooleanField('資本金または出資金の額が1億円以下の中小法人ですか？', default=False)
    is_excluded_business = BooleanField('適用除外事業者に該当していませんか？', default=False)
    industry_type = StringField('業種', validators=[Optional(), Length(max=50)])
    industry_code = StringField('業種番号', validators=[Optional(), Length(max=10)])
    reference_number = StringField('整理番号', validators=[Optional(), Length(max=20)])
    submit = SubmitField('保存する')


class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    remember_me = BooleanField('ログイン状態を保持する')
    submit = SubmitField('ログイン')


class DeclarationForm(FlaskForm):
    accounting_period_start = DateField('会計期間 開始', format='%Y-%m-%d', validators=[Optional()], render_kw={'class': 'js-date'})
    accounting_period_end = DateField('会計期間 終了', format='%Y-%m-%d', validators=[Optional()], render_kw={'class': 'js-date'})
    office_count = RadioField('事業所の数', choices=[('one', '１箇所'), ('multiple', '２箇所以上')], validators=[Optional()])
    declaration_type = RadioField('申告区分', choices=[('blue', '青色申告'), ('white', '白色申告')], validators=[Optional()])
    tax_system = RadioField('消費税経理方式', choices=[('included', '税込経理方式'), ('excluded', '税抜経理方式')], validators=[Optional()])
    representative_name = StringField('氏名', validators=[Optional()])
    representative_kana = StringField('ふりがな', validators=[Optional()])
    representative_position = StringField('役職', validators=[Optional()])
    representative_status = SelectField('常勤・非常勤の別', choices=[('full_time', '常勤'), ('part_time', '非常勤')], validators=[Optional()])
    representative_zip_code = StringField('郵便番号', validators=[Optional()])
    representative_prefecture = StringField('都道府県', validators=[Optional()])
    representative_city = StringField('市区町村', validators=[Optional()])
    representative_address = StringField('住所', validators=[Optional()])
    accounting_manager_name = StringField('氏名', validators=[Optional()])
    accounting_manager_kana = StringField('ふりがな', validators=[Optional()])
    closing_date = DateField('決算確定年月日', format='%Y-%m-%d', validators=[Optional()], render_kw={'class': 'js-date'})
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
    refund_bank_type = SelectField('金融機関種別', choices=[('', '選択してください'), ('bank', '銀行'), ('shinkin', '金庫'), ('kumiai', '組合'), ('nokyo', '農協'), ('gyokyo', '漁協')], validators=[Optional()])
    refund_branch_name = StringField('支店名', validators=[Optional()])
    refund_branch_type = SelectField('支店種別', choices=[('', '選択してください'), ('honten', '本店'), ('shiten', '支店'), ('shucchojo', '出張所'), ('honjo', '本所'), ('shisho', '支所')], validators=[Optional()])
    refund_account_type = SelectField('預金種類', choices=[('ordinary', '普通'), ('checking', '当座'), ('savings', '貯蓄')], validators=[Optional()])
    refund_account_number = StringField('口座番号', validators=[Optional()])
    submit = SubmitField('保存する')


class OfficeForm(FlaskForm):
    office_name = StringField('事業所名', validators=[DataRequired(message="事業所名は必須です。"), Length(max=100)])
    zip_code = StringField('郵便番号', validators=[Optional(), Length(min=7, max=7, message="郵便番号は7桁で入力してください。")])
    prefecture = StringField('都道府県', validators=[Optional(), Length(max=20)])
    city = StringField('市区町村', validators=[Optional(), Length(max=50)])
    address = StringField('番地以降', validators=[Optional(), Length(max=200)])
    phone_number = StringField('電話番号', validators=[Optional(), Length(max=20)])
    opening_date = DateField('開設年月日', format='%Y-%m-%d', validators=[Optional()], render_kw={'class': 'js-date'})
    closing_date = DateField('廃止年月日', format='%Y-%m-%d', validators=[Optional()], render_kw={'class': 'js-date'})
    employee_count = IntegerField('従業者数', validators=[Optional()])
    submit = SubmitField('登録する')


class AccountingSelectionForm(FlaskForm):
    current_year = datetime.now().year
    years = [(str(y), f'{y}年') for y in range(current_year, current_year - 10, -1)]
    target_year = SelectField('対象年度', choices=years, validators=[DataRequired(message="対象年度を選択してください。")])
    target_period = RadioField('対象期間', choices=[('first_half', '上期'), ('second_half', '下期'), ('full_year', '通期')], default='full_year', validators=[DataRequired(message="対象期間を選択してください。")])
    upload_file = FileField('会計データファイル', validators=[FileRequired(message="ファイルを選択してください。"), FileAllowed(['csv'], message='CSVファイルのみアップロードできます。')])
    submit = SubmitField('データ取込開始')


class DataMappingForm(FlaskForm):
    submit = SubmitField('マッピングを確定して次へ')


class FileUploadForm(FlaskForm):
    upload_file = FileField('データファイル', validators=[FileRequired(message="ファイルを選択してください。"), FileAllowed(['csv', 'txt'], message='CSVまたはTXTファイルのみアップロードできます。')])
    submit = SubmitField('データ取込開始')
