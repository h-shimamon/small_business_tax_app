from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField, FloatField, TextAreaField, HiddenField, BooleanField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, Optional

from .base_fields import CorporateNumberField, MoneyField, MemoField


class AccountsReceivableForm(FlaskForm):
    account_name = SelectField('科目', choices=[('売掛金', '売掛金'), ('未収入金', '未収入金')], validators=[DataRequired(message="科目は必須です。")])
    partner_name = StringField('取引先名', validators=[DataRequired(message="取引先名は必須です。"), Length(max=100)])
    registration_number = CorporateNumberField('登録番号（法人番号）', required=False)
    is_subsidiary = BooleanField('関係会社')
    partner_address = StringField('取引先住所', validators=[DataRequired(message="取引先住所は必須です。"), Length(max=200)])  # TODO: 旧仕様準拠（必須）
    balance_at_eoy = MoneyField('期末現在高', required=True)
    remarks = MemoField()
    submit = SubmitField('保存する')


class AccountsPayableForm(FlaskForm):
    # 2025-08-27 仕様: 登録番号/名称/所在地/期末現在高/摘要
    registration_number = CorporateNumberField('登録番号（法人番号）', required=False)
    partner_name = StringField('名称（氏名）', validators=[DataRequired(), Length(max=100)])
    partner_address = StringField('所在地（住所）', validators=[Optional(), Length(max=200)])
    balance_at_eoy = MoneyField('期末現在高', required=True)
    remarks = MemoField()
    submit = SubmitField('保存する')


class TemporaryPaymentForm(FlaskForm):
    account_name = SelectField('科目', choices=[('仮払金', '仮払金'), ('前渡金', '前渡金')], validators=[DataRequired(message="科目は必須です。")])
    partner_name = StringField('取引先名', validators=[DataRequired(message="取引先名は必須です。"), Length(max=100)])
    registration_number = CorporateNumberField('登録番号（法人番号）', required=False)
    is_subsidiary = BooleanField('関係会社')
    partner_address = StringField('取引先住所', validators=[Optional(), Length(max=200)])
    relationship = StringField('法人・代表者との関係', validators=[Optional(), Length(max=100)])
    balance_at_eoy = MoneyField('期末現在高', required=True)
    transaction_details = StringField('摘要', validators=[Optional(), Length(max=200)])  # TODO: memoフィールドへの統一候補
    submit = SubmitField('保存する')


class TemporaryReceiptForm(FlaskForm):
    account_name = SelectField('科目', choices=[('仮受金', '仮受金'), ('前受金', '前受金'), ('預り金', '預り金')], validators=[DataRequired()])
    partner_name = StringField('相手先名', validators=[DataRequired(), Length(max=100)])
    balance_at_eoy = MoneyField('期末現在高', required=True)
    transaction_details = TextAreaField('取引の内容', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')


class LoansReceivableForm(FlaskForm):
    registration_number = CorporateNumberField('登録番号（法人番号）', required=False)
    borrower_name = StringField('貸付先（氏名）', validators=[DataRequired(), Length(max=100)])
    borrower_address = StringField('貸付先（住所）', validators=[Optional(), Length(max=200)])
    relationship = StringField('法人・代表者との関係', validators=[Optional(), Length(max=100)])
    balance_at_eoy = MoneyField('期末現在高', required=True)
    received_interest = IntegerField('期中の受取利息額', validators=[Optional()])
    interest_rate = FloatField('利率', validators=[DataRequired()])
    collateral_details = StringField('担保の内容', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')


class InventoryForm(FlaskForm):
    item_name = StringField('商品・製品等の名称', validators=[DataRequired(), Length(max=100)])
    location = StringField('保管場所', validators=[Optional(), Length(max=200)])
    quantity = FloatField('数量', validators=[DataRequired()])
    unit = StringField('単位', validators=[Optional(), Length(max=20)])
    unit_price = IntegerField('単価', validators=[DataRequired()])
    balance_at_eoy = MoneyField('期末現在高', required=True)
    remarks = MemoField()
    submit = SubmitField('保存する')


class SecurityForm(FlaskForm):
    security_type = StringField('種類', validators=[DataRequired(), Length(max=50)])
    issuer = StringField('銘柄・発行者', validators=[DataRequired(), Length(max=100)])
    quantity = IntegerField('数量（株・口）', validators=[Optional()])
    balance_at_eoy = MoneyField('期末現在高', required=True)
    remarks = MemoField()
    submit = SubmitField('保存する')


class FixedAssetForm(FlaskForm):
    asset_type = StringField('種類', validators=[DataRequired(), Length(max=50)])
    location = StringField('所在地', validators=[DataRequired(), Length(max=200)])
    area = FloatField('面積（㎡）', validators=[Optional()])
    balance_at_eoy = MoneyField('期末現在高', required=True)
    remarks = MemoField()
    submit = SubmitField('保存する')


class BorrowingForm(FlaskForm):
    lender_name = StringField('借入先', validators=[DataRequired(), Length(max=100)])
    is_subsidiary = BooleanField('関係会社')
    balance_at_eoy = MoneyField('期末現在高', required=True)
    interest_rate = FloatField('利率（%）', validators=[DataRequired()])
    paid_interest = IntegerField('期間中の支払利子', validators=[Optional()])
    remarks = MemoField()
    submit = SubmitField('保存する')


class ExecutiveCompensationForm(FlaskForm):
    shareholder_name = StringField('氏名', validators=[DataRequired(), Length(max=100)])
    relationship = StringField('関係', validators=[Optional(), Length(max=100)])
    position = StringField('役職', validators=[Optional(), Length(max=100)])
    base_salary = IntegerField('基本給', validators=[Optional()])
    other_allowances = IntegerField('その他手当', validators=[Optional()])
    total_compensation = IntegerField('総額', validators=[DataRequired()])
    submit = SubmitField('保存する')


class LandRentForm(FlaskForm):
    account_name = SelectField('科目', choices=[('地代', '地代'), ('家賃', '家賃')], validators=[DataRequired()])
    lessor_name = StringField('支払先', validators=[DataRequired(), Length(max=100)])
    property_details = StringField('物件の詳細', validators=[Optional(), Length(max=200)])
    rent_paid = MoneyField('支払賃借料', required=True)
    remarks = MemoField()
    submit = SubmitField('保存する')


class MiscellaneousForm(FlaskForm):
    account_name = SelectField('科目', choices=[('雑益', '雑益'), ('雑損失', '雑損失')], validators=[DataRequired()])
    details = StringField('内容', validators=[DataRequired(), Length(max=200)])
    amount = MoneyField('金額', required=True)
    remarks = TextAreaField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')


class MiscellaneousIncomeForm(MiscellaneousForm):
    account_name = HiddenField(default='雑収入')


class MiscellaneousLossForm(MiscellaneousForm):
    account_name = HiddenField(default='雑損失')
