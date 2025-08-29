from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length

from .base_fields import MoneyField, MemoField


class DepositForm(FlaskForm):
    financial_institution = StringField('金融機関名', validators=[DataRequired(message="金融機関名は必須です。"), Length(max=100)])
    branch_name = StringField('支店名', validators=[DataRequired(message="支店名は必須です。"), Length(max=100)])
    account_type = SelectField('預金種類', choices=[('普通預金', '普通預金'), ('当座預金', '当座預金'), ('通知預金', '通知預金'), ('定期預金', '定期預金'), ('定期積金', '定期積金'), ('別段預金', '別段預金'), ('納税準備預金', '納税準備預金'), ('その他', 'その他')], validators=[DataRequired(message="預金種類は必須です。")])
    account_number = StringField('口座番号', validators=[DataRequired(message="口座番号は必須です。"), Length(max=50)])
    balance = MoneyField('期末現在高', required=True)
    remarks = MemoField()
    submit = SubmitField('保存する')
