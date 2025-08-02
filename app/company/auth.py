# app/company/auth.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from app.company import company_bp
from app.company.models import User
from app.company.forms import LoginForm
from app import db

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
