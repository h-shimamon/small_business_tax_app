# Auxiliary forms module for NotesPayable and AccountsPayable (inlined for minimal change)
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, BooleanField, IntegerField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, Optional

class NotesPayableForm(FlaskForm):
    registration_number = StringField('登録番号（法人番号）', validators=[Optional(), Length(max=20)])
    payee = StringField('支払先', validators=[DataRequired(message="支払先は必須です。"), Length(max=100)])
    issue_date = DateField('振出年月日', format='%Y-%m-%d', validators=[DataRequired()], render_kw={'class': 'js-date'})
    due_date = DateField('支払期日', format='%Y-%m-%d', validators=[DataRequired()], render_kw={'class': 'js-date'})
    payer_bank = StringField('支払銀行名', validators=[Optional(), Length(max=100)])
    payer_branch = StringField('支払支店名', validators=[Optional(), Length(max=100)])
    amount = IntegerField('金額', validators=[DataRequired()])
    remarks = StringField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')

class AccountsPayableForm(FlaskForm):
    registration_number = StringField('登録番号（法人番号）', validators=[Optional(), Length(max=20)])
    partner_name = StringField('名称（氏名）', validators=[DataRequired(), Length(max=100)])
    partner_address = StringField('所在地（住所）', validators=[Optional(), Length(max=200)])
    balance_at_eoy = IntegerField('期末現在高', validators=[DataRequired()])
    remarks = StringField('摘要', validators=[Optional(), Length(max=200)])
    submit = SubmitField('保存する')
