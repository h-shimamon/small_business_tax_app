from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FloatField,
    HiddenField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional

from .base_fields import CorporateNumberField, MemoField, MoneyField

FieldFactory = tuple[str, callable]
FormFieldDefinitions = dict[str, list[FieldFactory]]


def _data_required(message: str | None = None):
    return DataRequired(message=message) if message else DataRequired()


SOA_FORM_FIELDS: FormFieldDefinitions = {
    'AccountsReceivableForm': [
        ('account_name', lambda: SelectField(
            '科目',
            choices=[('売掛金', '売掛金'), ('未収入金', '未収入金')],
            validators=[_data_required('科目は必須です。')],
        )),
        ('partner_name', lambda: StringField(
            '取引先名',
            validators=[_data_required('取引先名は必須です。'), Length(max=100)],
        )),
        ('registration_number', lambda: CorporateNumberField('登録番号（法人番号）', required=False)),
        ('is_subsidiary', lambda: BooleanField('関係会社')),
        ('partner_address', lambda: StringField(
            '取引先住所',
            validators=[_data_required('取引先住所は必須です。'), Length(max=200)],
        )),
        ('balance_at_eoy', lambda: MoneyField('期末現在高', required=True)),
        ('remarks', lambda: MemoField()),
    ],
    'AccountsPayableForm': [
        ('registration_number', lambda: CorporateNumberField('登録番号（法人番号）', required=False)),
        ('partner_name', lambda: StringField('名称（氏名）', validators=[_data_required(), Length(max=100)])),
        ('partner_address', lambda: StringField('所在地（住所）', validators=[Optional(), Length(max=200)])),
        ('balance_at_eoy', lambda: MoneyField('期末現在高', required=True)),
        ('remarks', lambda: MemoField()),
    ],
    'TemporaryPaymentForm': [
        ('account_name', lambda: SelectField(
            '科目',
            choices=[('仮払金', '仮払金'), ('前渡金', '前渡金')],
            validators=[_data_required('科目は必須です。')],
        )),
        ('partner_name', lambda: StringField(
            '取引先名',
            validators=[_data_required('取引先名は必須です。'), Length(max=100)],
        )),
        ('registration_number', lambda: CorporateNumberField('登録番号（法人番号）', required=False)),
        ('is_subsidiary', lambda: BooleanField('関係会社')),
        ('partner_address', lambda: StringField('取引先住所', validators=[Optional(), Length(max=200)])),
        ('relationship', lambda: StringField('法人・代表者との関係', validators=[Optional(), Length(max=100)])),
        ('balance_at_eoy', lambda: MoneyField('期末現在高', required=True)),
        ('transaction_details', lambda: StringField('摘要', validators=[Optional(), Length(max=200)])),
    ],
    'TemporaryReceiptForm': [
        ('account_name', lambda: SelectField(
            '科目',
            choices=[('仮受金', '仮受金'), ('前受金', '前受金'), ('預り金', '預り金')],
            validators=[_data_required()],
        )),
        ('partner_name', lambda: StringField('相手先名', validators=[_data_required(), Length(max=100)])),
        ('balance_at_eoy', lambda: MoneyField('期末現在高', required=True)),
        ('transaction_details', lambda: TextAreaField('取引の内容', validators=[Optional(), Length(max=200)])),
    ],
    'LoansReceivableForm': [
        ('registration_number', lambda: CorporateNumberField('登録番号（法人番号）', required=False)),
        ('borrower_name', lambda: StringField('貸付先（氏名）', validators=[_data_required(), Length(max=100)])),
        ('borrower_address', lambda: StringField('貸付先（住所）', validators=[Optional(), Length(max=200)])),
        ('relationship', lambda: StringField('法人・代表者との関係', validators=[Optional(), Length(max=100)])),
        ('balance_at_eoy', lambda: MoneyField('期末現在高', required=True)),
        ('received_interest', lambda: IntegerField('期中の受取利息額', validators=[Optional()])),
        ('interest_rate', lambda: FloatField('利率', validators=[_data_required()])),
        ('collateral_details', lambda: StringField('担保の内容', validators=[Optional(), Length(max=200)])),
    ],
    'InventoryForm': [
        ('item_name', lambda: StringField('商品・製品等の名称', validators=[_data_required(), Length(max=100)])),
        ('location', lambda: StringField('保管場所', validators=[Optional(), Length(max=200)])),
        ('quantity', lambda: FloatField('数量', validators=[_data_required()])),
        ('unit', lambda: StringField('単位', validators=[Optional(), Length(max=20)])),
        ('unit_price', lambda: IntegerField('単価', validators=[_data_required()])),
        ('balance_at_eoy', lambda: MoneyField('期末現在高', required=True)),
        ('remarks', lambda: MemoField()),
    ],
    'SecurityForm': [
        ('security_type', lambda: StringField('種類', validators=[_data_required(), Length(max=50)])),
        ('issuer', lambda: StringField('銘柄・発行者', validators=[_data_required(), Length(max=100)])),
        ('quantity', lambda: IntegerField('数量（株・口）', validators=[Optional()])),
        ('balance_at_eoy', lambda: MoneyField('期末現在高', required=True)),
        ('remarks', lambda: MemoField()),
    ],
    'FixedAssetForm': [
        ('asset_type', lambda: StringField('種類', validators=[_data_required(), Length(max=50)])),
        ('location', lambda: StringField('所在地', validators=[_data_required(), Length(max=200)])),
        ('area', lambda: FloatField('面積（㎡）', validators=[Optional()])),
        ('balance_at_eoy', lambda: MoneyField('期末現在高', required=True)),
        ('remarks', lambda: MemoField()),
    ],
    'BorrowingForm': [
        ('lender_name', lambda: StringField('借入先', validators=[_data_required(), Length(max=100)])),
        ('is_subsidiary', lambda: BooleanField('関係会社')),
        ('balance_at_eoy', lambda: MoneyField('期末現在高', required=True)),
        ('interest_rate', lambda: FloatField('利率（%）', validators=[_data_required()])),
        ('paid_interest', lambda: IntegerField('期間中の支払利子', validators=[Optional()])),
        ('remarks', lambda: MemoField()),
    ],
    'ExecutiveCompensationForm': [
        ('shareholder_name', lambda: StringField('氏名', validators=[_data_required(), Length(max=100)])),
        ('relationship', lambda: StringField('関係', validators=[Optional(), Length(max=100)])),
        ('position', lambda: StringField('役職', validators=[Optional(), Length(max=100)])),
        ('base_salary', lambda: IntegerField('基本給', validators=[Optional()])),
        ('other_allowances', lambda: IntegerField('その他手当', validators=[Optional()])),
        ('total_compensation', lambda: IntegerField('総額', validators=[_data_required()])),
    ],
    'LandRentForm': [
        ('account_name', lambda: SelectField(
            '科目',
            choices=[('地代', '地代'), ('家賃', '家賃')],
            validators=[_data_required()],
        )),
        ('lessor_name', lambda: StringField('支払先', validators=[_data_required(), Length(max=100)])),
        ('property_details', lambda: StringField('物件の詳細', validators=[Optional(), Length(max=200)])),
        ('rent_paid', lambda: MoneyField('支払賃借料', required=True)),
        ('remarks', lambda: MemoField()),
    ],
    'MiscellaneousForm': [
        ('account_name', lambda: SelectField(
            '科目',
            choices=[('雑益', '雑益'), ('雑損失', '雑損失')],
            validators=[_data_required()],
        )),
        ('details', lambda: StringField('内容', validators=[_data_required(), Length(max=200)])),
        ('amount', lambda: MoneyField('金額', required=True)),
        ('remarks', lambda: TextAreaField('摘要', validators=[Optional(), Length(max=200)])),
    ],
}


def get_soa_form_classes() -> dict[str, type[FlaskForm]]:
    classes: dict[str, type[FlaskForm]] = {}

    for form_name, field_factories in SOA_FORM_FIELDS.items():
        attrs = {name: factory() for name, factory in field_factories}
        attrs.setdefault('submit', SubmitField('保存する'))
        classes[form_name] = type(form_name, (FlaskForm,), attrs)

    base_misc = classes['MiscellaneousForm']
    classes['MiscellaneousIncomeForm'] = type(
        'MiscellaneousIncomeForm',
        (base_misc,),
        {'account_name': HiddenField(default='雑収入')}
    )
    classes['MiscellaneousLossForm'] = type(
        'MiscellaneousLossForm',
        (base_misc,),
        {'account_name': HiddenField(default='雑損失')}
    )

    return classes
