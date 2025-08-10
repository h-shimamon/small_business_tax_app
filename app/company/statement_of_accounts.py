# app/company/statement_of_accounts.py
from flask import render_template, request, redirect, url_for, flash, abort
from app.company import company_bp
from app.company.models import (
    Deposit, NotesReceivable, AccountsReceivable, TemporaryPayment,
    LoansReceivable, Inventory, Security, FixedAsset, NotesPayable,
    AccountsPayable, TemporaryReceipt, Borrowing, ExecutiveCompensation,
    LandRent, Miscellaneous
)
from app.company.forms import (
    DepositForm, NotesReceivableForm, AccountsReceivableForm, TemporaryPaymentForm,
    LoansReceivableForm, InventoryForm, SecurityForm, FixedAssetForm, NotesPayableForm,
    AccountsPayableForm, TemporaryReceiptForm, BorrowingForm, ExecutiveCompensationForm,
    LandRentForm, MiscellaneousForm
)
from app import db
from app.navigation import get_navigation_state
from .auth import company_required

# 各内訳ページの情報を一元管理
STATEMENT_PAGES_CONFIG = {
    'deposits': {'model': Deposit, 'form': DepositForm, 'title': '預貯金等', 'total_field': 'balance', 'template': 'deposit_form.html'},
    'notes_receivable': {'model': NotesReceivable, 'form': NotesReceivableForm, 'title': '受取手形', 'total_field': 'amount', 'template': 'notes_receivable_form.html'},
    'accounts_receivable': {'model': AccountsReceivable, 'form': AccountsReceivableForm, 'title': '売掛金（未収入金）', 'total_field': 'balance_at_eoy', 'template': 'accounts_receivable_form.html'},
    'temporary_payments': {'model': TemporaryPayment, 'form': TemporaryPaymentForm, 'title': '仮払金（前渡金）', 'total_field': 'balance_at_eoy', 'template': 'temporary_payment_form.html'},
    'loans_receivable': {'model': LoansReceivable, 'form': LoansReceivableForm, 'title': '貸付金・受取利息', 'total_field': 'balance_at_eoy', 'template': 'loans_receivable_form.html'},
    'inventories': {'model': Inventory, 'form': InventoryForm, 'title': '棚卸資産', 'total_field': 'balance_at_eoy', 'template': 'inventories_form.html'},
    'securities': {'model': Security, 'form': SecurityForm, 'title': '有価証券', 'total_field': 'balance_at_eoy', 'template': 'securities_form.html'},
    'fixed_assets': {'model': FixedAsset, 'form': FixedAssetForm, 'title': '固定資産（土地等）', 'total_field': 'balance_at_eoy', 'template': 'fixed_assets_form.html'},
    'notes_payable': {'model': NotesPayable, 'form': NotesPayableForm, 'title': '支払手形', 'total_field': 'amount', 'template': 'notes_payable_form.html'},
    'accounts_payable': {'model': AccountsPayable, 'form': AccountsPayableForm, 'title': '買掛金（未払金・未払費用）', 'total_field': 'balance_at_eoy', 'template': 'accounts_payable_form.html'},
    'temporary_receipts': {'model': TemporaryReceipt, 'form': TemporaryReceiptForm, 'title': '仮受金（前受金・預り金）', 'total_field': 'balance_at_eoy', 'template': 'temporary_receipts_form.html'},
    'borrowings': {'model': Borrowing, 'form': BorrowingForm, 'title': '借入金及び支払利子', 'total_field': 'balance_at_eoy', 'template': 'borrowings_form.html'},
    'executive_compensations': {'model': ExecutiveCompensation, 'form': ExecutiveCompensationForm, 'title': '役員給与等', 'total_field': 'total_compensation', 'template': 'executive_compensations_form.html'},
    'land_rents': {'model': LandRent, 'form': LandRentForm, 'title': '地代家賃等', 'total_field': 'rent_paid', 'template': 'land_rents_form.html'},
    'miscellaneous': {'model': Miscellaneous, 'form': MiscellaneousForm, 'title': '雑益・雑損失等', 'total_field': 'amount', 'template': 'miscellaneous_form.html'},
}

@company_bp.route('/statement_of_accounts')
@company_required
def statement_of_accounts(company):
    """勘定科目内訳書ページ"""
    page = request.args.get('page', 'deposits')
    config = STATEMENT_PAGES_CONFIG.get(page)
    if not config:
        abort(404)

    items = db.session.query(config['model']).filter_by(company_id=company.id).all()
    total = sum(getattr(item, config['total_field'], 0) for item in items)
    
    context = {
        'page': page,
        'page_title': config['title'],
        'items': items,
        'total': total,
        'navigation_state': get_navigation_state(page)
    }
    return render_template('company/statement_of_accounts.html', **context)

@company_bp.route('/statement/<string:page_key>/add', methods=['GET', 'POST'])
@company_required
def add_item(company, page_key):
    """汎用的な項目追加ビュー"""
    config = STATEMENT_PAGES_CONFIG.get(page_key)
    if not config:
        abort(404)
        
    form = config['form'](request.form)
    if form.validate_on_submit():
        new_item = config['model'](company_id=company.id)
        form.populate_obj(new_item)
        db.session.add(new_item)
        db.session.commit()
        flash(f'{config["title"]}情報を登録しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page=page_key))
    
    form_template = f"company/{config['template']}"
    return render_template(form_template, form=form, form_title=f'{config["title"]}の新規登録', navigation_state=get_navigation_state(page_key))

@company_bp.route('/statement/<string:page_key>/edit/<int:item_id>', methods=['GET', 'POST'])
@company_required
def edit_item(company, page_key, item_id):
    """汎用的な項目編集ビュー"""
    config = STATEMENT_PAGES_CONFIG.get(page_key)
    if not config:
        abort(404)
        
    item = db.session.query(config['model']).filter_by(id=item_id, company_id=company.id).first_or_404()
    
    form = config['form'](request.form, obj=item)
    if form.validate_on_submit():
        form.populate_obj(item)
        db.session.commit()
        flash(f'{config["title"]}情報を更新しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page=page_key))
        
    if request.method == 'GET':
        form = config['form'](obj=item)

    form_template = f"company/{config['template']}"
    return render_template(form_template, form=form, form_title=f'{config["title"]}の編集', navigation_state=get_navigation_state(page_key))

@company_bp.route('/statement/<string:page_key>/delete/<int:item_id>', methods=['POST'])
@company_required
def delete_item(company, page_key, item_id):
    """汎用的な項目削除ビュー"""
    config = STATEMENT_PAGES_CONFIG.get(page_key)
    if not config:
        abort(404)
        
    item = db.session.query(config['model']).filter_by(id=item_id, company_id=company.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash(f'{config["title"]}情報を削除しました。', 'success')
    return redirect(url_for('company.statement_of_accounts', page=page_key))
