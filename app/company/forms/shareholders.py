from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, RadioField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Optional

from .base_fields import AddressMixin


class BaseShareholderForm(FlaskForm, AddressMixin):
    shareholder_number = StringField('株主番号', validators=[Optional(), Length(max=20)], render_kw={"placeholder": "例：12345"})
    last_name = StringField('氏名', validators=[DataRequired(message="氏名は必須です。"), Length(max=50)], render_kw={"placeholder": "例：鈴木 一郎"})
    officer_position = SelectField('役職名', choices=[], validators=[Optional()])
    investment_amount = IntegerField('出資金額', validators=[Optional()], render_kw={"placeholder": "例：1000000"})
    shares_held = IntegerField('保有株式数', validators=[Optional()], render_kw={"placeholder": "例：100"})
    voting_rights = IntegerField('議決権の数', validators=[Optional()], render_kw={"placeholder": "例：100"})
    is_controlled_company = RadioField('被支配会社の該当', choices=[('yes', '該当する'), ('no', '該当しない')], default='no', coerce=lambda x: x == 'yes')


class MainShareholderForm(BaseShareholderForm):
    entity_type = RadioField('株主の区分', choices=[('individual', '個人'), ('corporation', '法人'), ('self_company', '自社')], default='individual', validators=[DataRequired(message="株主の区分は必須です。")])
    submit = SubmitField('登録する')


class RelatedShareholderForm(BaseShareholderForm):
    relationship = StringField('主たる株主との関係', validators=[DataRequired(message="主たる株主との関係は必須です。"), Length(max=100)], render_kw={"placeholder": "例：妻や長男など、主たる株主からみた関係"})
    is_address_same_as_main = BooleanField('主たる株主と住所が同じ')
    submit = SubmitField('登録する')

    def populate_address_from_main_shareholder(self, main_shareholder):
        self.zip_code.data = main_shareholder.zip_code
        self.prefecture_city.data = main_shareholder.prefecture_city
        self.address.data = main_shareholder.address
