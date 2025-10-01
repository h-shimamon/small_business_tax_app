# app/company/auth.py
from functools import wraps

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.company import company_bp
from app.company.forms import LoginForm

from .services.auth_service import AuthService


def company_required(f):
    """
    ログインしており、かつ会社情報が登録済みであることを確認するデコレータ。
    紐づく会社情報をビュー関数に渡します。
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        company = AuthService.get_company_for_user(current_user)
        
        if not company:
            flash('最初に会社情報を登録してください。', 'info')
            return redirect(url_for('company.info'))

        return f(company, *args, **kwargs)
    return decorated_function

@company_bp.route('/login', methods=['GET', 'POST'])
def login():
    """ログイン処理"""
    form = LoginForm()
    if form.validate_on_submit():
        user = AuthService.authenticate_user(form.username.data, form.password.data)
        
        if user:
            login_user(user, remember=form.remember_me.data)
            # ログイン後のリダイレクト先は基本情報ページ
            return redirect(url_for('company.info'))
        else:
            flash('ユーザー名またはパスワードが無効です。', 'danger')
            return redirect(url_for('company.login'))
            
    return render_template('login.html', form=form)

@company_bp.route('/logout')
@login_required
def logout():
    """ログアウト処理"""
    logout_user()
    flash('ログアウトしました。', 'info')
    return redirect(url_for('company.login'))
