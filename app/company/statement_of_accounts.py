# app/company/statement_of_accounts.py

from flask import render_template, request, redirect, url_for, flash
from app.company import company_bp
from app.company.models import Company, Deposit, NotesReceivable, AccountsReceivable, TemporaryPayment
from app.company.forms import DepositForm, NotesReceivableForm, AccountsReceivableForm, TemporaryPaymentForm
from app import db

@company_bp.route('/statement_of_accounts')
def statement_of_accounts():
    """勘定科目内訳書ページ"""
    page = request.args.get('page', 'deposits')
    company = Company.query.first()
    
    context = {'page': page}

    if not company:
        flash('会社情報が未登録のため、機能を利用できません。', 'warning')
    else:
        if page == 'deposits':
            items = Deposit.query.filter_by(company_id=company.id).all()
            context['items'] = items
        elif page == 'notes_receivable':
            items = NotesReceivable.query.filter_by(company_id=company.id).all()
            context['items'] = items
        elif page == 'accounts_receivable':
            items = AccountsReceivable.query.filter_by(company_id=company.id).all()
            context['items'] = items
        elif page == 'temporary_payments':
            items = TemporaryPayment.query.filter_by(company_id=company.id).all()
            context['items'] = items

    return render_template('statement_of_accounts.html', **context)


# --- 預貯金のCRUD ---
@company_bp.route('/deposit/add', methods=['GET', 'POST'])
def add_deposit():
    """預貯金の新規登録"""
    form = DepositForm()
    company = Company.query.first()
    if not company:
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))
    
    if form.validate_on_submit():
        new_deposit = Deposit(company_id=company.id)
        form.populate_obj(new_deposit)
        db.session.add(new_deposit)
        db.session.commit()
        flash('預貯金情報を登録しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='deposits'))
    
    return render_template('deposit_form.html', form=form, form_title="預貯金の新規登録")

@company_bp.route('/deposit/edit/<int:deposit_id>', methods=['GET', 'POST'])
def edit_deposit(deposit_id):
    """預貯金の編集"""
    deposit = Deposit.query.get_or_404(deposit_id)
    form = DepositForm(obj=deposit)
    
    if form.validate_on_submit():
        form.populate_obj(deposit)
        db.session.commit()
        flash('預貯金情報を更新しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='deposits'))
        
    return render_template('deposit_form.html', form=form, form_title="預貯金の編集")

@company_bp.route('/deposit/delete/<int:deposit_id>', methods=['POST'])
def delete_deposit(deposit_id):
    """預貯金の削除"""
    deposit = Deposit.query.get_or_404(deposit_id)
    db.session.delete(deposit)
    db.session.commit()
    flash('預貯金情報を削除しました。', 'success')
    return redirect(url_for('company.statement_of_accounts', page='deposits'))

# --- 受取手形のCRUD ---
@company_bp.route('/notes_receivable/add', methods=['GET', 'POST'])
def add_notes_receivable():
    """受取手形の新規登録"""
    form = NotesReceivableForm()
    company = Company.query.first()
    if not company:
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))
    
    if form.validate_on_submit():
        new_note = NotesReceivable(company_id=company.id)
        form.populate_obj(new_note)
        db.session.add(new_note)
        db.session.commit()
        flash('受取手形情報を登録しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='notes_receivable'))
    
    return render_template('notes_receivable_form.html', form=form, form_title="受取手形の新規登録")

@company_bp.route('/notes_receivable/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_notes_receivable(note_id):
    """受取手形の編集"""
    note = NotesReceivable.query.get_or_404(note_id)
    form = NotesReceivableForm(obj=note)
    
    if form.validate_on_submit():
        form.populate_obj(note)
        db.session.commit()
        flash('受取手形情報を更新しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='notes_receivable'))
        
    return render_template('notes_receivable_form.html', form=form, form_title="受取手形の編集")

@company_bp.route('/notes_receivable/delete/<int:note_id>', methods=['POST'])
def delete_notes_receivable(note_id):
    """受取手形の削除"""
    note = NotesReceivable.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    flash('受取手形情報を削除しました。', 'success')
    return redirect(url_for('company.statement_of_accounts', page='notes_receivable'))

# --- 売掛金（未収入金）のCRUD ---
@company_bp.route('/accounts_receivable/add', methods=['GET', 'POST'])
def add_accounts_receivable():
    """売掛金（未収入金）の新規登録"""
    form = AccountsReceivableForm()
    company = Company.query.first()
    if not company:
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))
    
    if form.validate_on_submit():
        new_receivable = AccountsReceivable(company_id=company.id)
        form.populate_obj(new_receivable)
        db.session.add(new_receivable)
        db.session.commit()
        flash('売掛金（未収入金）情報を登録しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='accounts_receivable'))
    
    return render_template('accounts_receivable_form.html', form=form, form_title="売掛金（未収入金）の新規登録")

@company_bp.route('/accounts_receivable/edit/<int:receivable_id>', methods=['GET', 'POST'])
def edit_accounts_receivable(receivable_id):
    """売掛金（未収入金）の編集"""
    receivable = AccountsReceivable.query.get_or_404(receivable_id)
    form = AccountsReceivableForm(obj=receivable)
    
    if form.validate_on_submit():
        form.populate_obj(receivable)
        db.session.commit()
        flash('売掛金（未収入金）情報を更新しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='accounts_receivable'))
        
    return render_template('accounts_receivable_form.html', form=form, form_title="売掛金（未収入金）の編集")

@company_bp.route('/accounts_receivable/delete/<int:receivable_id>', methods=['POST'])
def delete_accounts_receivable(receivable_id):
    """売掛金（未収入金）の削除"""
    receivable = AccountsReceivable.query.get_or_404(receivable_id)
    db.session.delete(receivable)
    db.session.commit()
    flash('売掛金（未収入金）情報を削除しました。', 'success')
    return redirect(url_for('company.statement_of_accounts', page='accounts_receivable'))

# --- 仮払金（前渡金）のCRUD ---
@company_bp.route('/temporary_payment/add', methods=['GET', 'POST'])
def add_temporary_payment():
    """仮払金（前渡金）の新規登録"""
    form = TemporaryPaymentForm()
    company = Company.query.first()
    if not company:
        flash('先に会社の基本情報を登録してください。', 'error')
        return redirect(url_for('company.show'))
    
    if form.validate_on_submit():
        new_payment = TemporaryPayment(company_id=company.id)
        form.populate_obj(new_payment)
        db.session.add(new_payment)
        db.session.commit()
        flash('仮払金（前渡金）情報を登録しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='temporary_payments'))
    
    return render_template('temporary_payment_form.html', form=form, form_title="仮払金（前渡金）の新規登録")

@company_bp.route('/temporary_payment/edit/<int:payment_id>', methods=['GET', 'POST'])
def edit_temporary_payment(payment_id):
    """仮払金（前渡金）の編集"""
    payment = TemporaryPayment.query.get_or_404(payment_id)
    form = TemporaryPaymentForm(obj=payment)
    
    if form.validate_on_submit():
        form.populate_obj(payment)
        db.session.commit()
        flash('仮払金（前渡金）情報を更新しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page='temporary_payments'))
        
    return render_template('temporary_payment_form.html', form=form, form_title="仮払金（前渡金）の編集")

@company_bp.route('/temporary_payment/delete/<int:payment_id>', methods=['POST'])
def delete_temporary_payment(payment_id):
    """仮払金（前渡金）の削除"""
    payment = TemporaryPayment.query.get_or_404(payment_id)
    db.session.delete(payment)
    db.session.commit()
    flash('仮払金（前渡金）情報を削除しました。', 'success')
    return redirect(url_for('company.statement_of_accounts', page='temporary_payments'))