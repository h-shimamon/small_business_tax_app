from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length


class LoginForm(FlaskForm):
    email = StringField("メールアドレス", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("パスワード", validators=[DataRequired(), Length(min=8, max=256)])
    remember = BooleanField("ログイン状態を保持")
    submit = SubmitField("ログイン")


class SignupForm(FlaskForm):
    email = StringField("メールアドレス", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("パスワード", validators=[DataRequired(), Length(min=8, max=256)])
    password2 = PasswordField("パスワード（確認）", validators=[DataRequired(), Length(min=8, max=256)])
    submit = SubmitField("登録する")


class ResetRequestForm(FlaskForm):
    email = StringField("メールアドレス", validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField("再設定メールを送信")


class ResetConfirmForm(FlaskForm):
    password = PasswordField("新しいパスワード", validators=[DataRequired(), Length(min=8, max=256)])
    password2 = PasswordField("パスワード（確認）", validators=[DataRequired(), Length(min=8, max=256)])
    submit = SubmitField("パスワードを更新")


class SignupEmailForm(FlaskForm):
    email = StringField("メールアドレス", validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField("確認メールを送信")
