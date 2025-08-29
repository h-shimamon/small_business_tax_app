from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, Optional

from .base_fields import CorporateNumberField, MoneyField, MemoField


class NotesReceivableForm(FlaskForm):
    drawer = StringField('振出人', validators=[DataRequired(message="振出人は必須です。"), Length(max=100)])
    registration_number = CorporateNumberField('登録番号（法人番号）', required=False)
    issue_date = DateField('振出年月日', format='%Y-%m-%d', validators=[DataRequired(message="振出年月日は必須です。")], render_kw={'class': 'js-date'})
    due_date = DateField('支払期日', format='%Y-%m-%d', validators=[DataRequired(message="支払期日は必須です。")], render_kw={'class': 'js-date'})
    payer_bank = StringField('支払銀行名', validators=[DataRequired(message="支払銀行名は必須です。"), Length(max=100)])
    payer_branch = StringField('支払支店名', validators=[Optional(), Length(max=100)])
    amount = MoneyField('金額', required=True)
    discount_bank = StringField('割引銀行名', validators=[Optional(), Length(max=100)])
    discount_branch = StringField('割引支店名', validators=[Optional(), Length(max=100)])
    remarks = MemoField()
    submit = SubmitField('保存する')


class NotesPayableForm(FlaskForm):
    # 2025-08-27 仕様: 登録番号/銀行/支店/金額/摘要
    registration_number = CorporateNumberField('登録番号（法人番号）', required=False)
    payee = StringField('支払先', validators=[DataRequired(message="支払先は必須です。"), Length(max=100)])
    issue_date = DateField('振出年月日', format='%Y-%m-%d', validators=[DataRequired()], render_kw={'class': 'js-date'})
    due_date = DateField('支払期日', format='%Y-%m-%d', validators=[DataRequired()], render_kw={'class': 'js-date'})
    payer_bank = StringField('支払銀行名', validators=[Optional(), Length(max=100)])  # TODO: 旧実装は必須
    payer_branch = StringField('支払支店名', validators=[Optional(), Length(max=100)])
    amount = MoneyField('金額', required=True)
    remarks = MemoField()
    submit = SubmitField('保存する')
