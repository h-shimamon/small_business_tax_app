# app/company/auth.py
from functools import wraps
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.company import company_bp
from app.company.models import User, Company
from app.company.forms import LoginForm

def company_required(f):
    """
    ログインしており、かつ会社情報が登録済みであることを確認するデコレータ。
    紐づく会社情報をビュー関数に渡します。
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # current_user に紐づく最初の会社を取得
        # 将来的に複数企業に対応する場合は、ここで選択ロジックが必要
        company = Company.query.filter_by(user_id=current_user.id).first()
        
        if not company:
            # まだ会社が登録されていない場合は、登録ページへ誘導
            flash('最初に会社情報を登録してください。', 'info')
            return redirect(url_for('company.show'))

        # ビュー関数に company オブジェクトを渡す
        return f(company, *args, **kwargs)
    return decorated_function

@company_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('company.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('company.show'))
    return render_template('login.html', form=form)

@company_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('company.login'))
