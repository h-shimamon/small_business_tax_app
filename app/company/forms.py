# app/company/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional

class EmployeeForm(FlaskForm):
    """従業員情報を登録・編集するためのフォーム"""
    name = StringField('氏名', validators=[DataRequired(message='氏名は必須です。')])
    group = StringField('グループ', validators=[Optional()])
    joined_date = DateField('社員となった日', validators=[Optional()])
    relationship = StringField('続柄', validators=[Optional()])
    address = StringField('住所', validators=[Optional()])
    shares_held = IntegerField('株式数', validators=[Optional()])
    voting_rights = IntegerField('議決権', validators=[Optional()])
    position = StringField('役職', validators=[Optional()])
    investment_amount = IntegerField('出資金額', validators=[Optional()])
    submit = SubmitField('登録する')