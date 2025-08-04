# app/company/statement_of_accounts.py

from flask import render_template, request, redirect, url_for, flash, current_app
from datetime import date
from app.company import company_bp
from app.company.models import (
    Company, Deposit, NotesReceivable, AccountsReceivable, TemporaryPayment,
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

# 各内訳ページの情報を一元管理
STATEMENT_PAGES_CONFIG = {
    'deposits': {'model': Deposit, 'form': DepositForm, 'title': '預貯金等', 'total_field': 'balance', 'add_endpoint': 'company.add_deposit'},
    'notes_receivable': {'model': NotesReceivable, 'form': NotesReceivableForm, 'title': '受取手形', 'total_field': 'amount', 'add_endpoint': 'company.add_notes_receivable'},
    'accounts_receivable': {'model': AccountsReceivable, 'form': AccountsReceivableForm, 'title': '売掛金（未収入金）', 'total_field': 'balance_at_eoy', 'add_endpoint': 'company.add_accounts_receivable'},
    'temporary_payments': {'model': TemporaryPayment, 'form': TemporaryPaymentForm, 'title': '仮払金（前渡金）', 'total_field': 'balance_at_eoy', 'add_endpoint': 'company.add_temporary_payment'},
    'loans_receivable': {'model': LoansReceivable, 'form': LoansReceivableForm, 'title': '貸付金・受取利息', 'total_field': 'balance_at_eoy', 'add_endpoint': 'company.add_loans_receivable'},
    'inventories': {'model': Inventory, 'form': InventoryForm, 'title': '棚卸資産', 'total_field': 'balance_at_eoy', 'add_endpoint': 'company.add_inventory'},
    'securities': {'model': Security, 'form': SecurityForm, 'title': '有価証券', 'total_field': 'balance_at_eoy', 'add_endpoint': 'company.add_security'},
    'fixed_assets': {'model': FixedAsset, 'form': FixedAssetForm, 'title': '固定資産（土地等）', 'total_field': 'balance_at_eoy', 'add_endpoint': 'company.add_fixed_asset'},
    'notes_payable': {'model': NotesPayable, 'form': NotesPayableForm, 'title': '支払手形', 'total_field': 'amount', 'add_endpoint': 'company.add_notes_payable'},
    'accounts_payable': {'model': AccountsPayable, 'form': AccountsPayableForm, 'title': '買掛金（未払金・未払費用）', 'total_field': 'balance_at_eoy', 'add_endpoint': 'company.add_accounts_payable'},
    'temporary_receipts': {'model': TemporaryReceipt, 'form': TemporaryReceiptForm, 'title': '仮受金（前受金・預り金）', 'total_field': 'balance_at_eoy', 'add_endpoint': 'company.add_temporary_receipt'},
    'borrowings': {'model': Borrowing, 'form': BorrowingForm, 'title': '借入金及び支払利子', 'total_field': 'balance_at_eoy', 'add_endpoint': 'company.add_borrowing'},
    'executive_compensations': {'model': ExecutiveCompensation, 'form': ExecutiveCompensationForm, 'title': '役員給与等', 'total_field': 'total_compensation', 'add_endpoint': 'company.add_executive_compensation'},
    'land_rents': {'model': LandRent, 'form': LandRentForm, 'title': '地代家賃等', 'total_field': 'rent_paid', 'add_endpoint': 'company.add_land_rent'},
    'miscellaneous': {'model': Miscellaneous, 'form': MiscellaneousForm, 'title': '雑益・雑損失等', 'total_field': 'amount', 'add_endpoint': 'company.add_miscellaneous'},
}

def _get_company_or_redirect():
    """
    DBから会社情報を取得する。
    会社情報が存在せず、かつ開発モード(app.debug is True)の場合、
    ダミーの会社情報を自動で作成して返す。
    本番モードで会社情報が存在しない場合はリダイレクトする。
    """
    company = Company.query.first()
    if company:
        return company, None

    if not current_app.debug:
        flash('先に会社の基本情報を登録してください。', 'error')
        return None, redirect(url_for('company.show'))

    # 開発モードで会社が存在しない場合、ダミーデータを作成
    flash('開発用のダミー会社情報を作成しました。', 'info')
    dummy_company = Company(
        corporate_number="1234567890123",
        company_name="ダミー株式会社",
        company_name_kana="ダミーカブシキガイシャ",
        zip_code="1000001",
        prefecture="東京都",
        city="千代田区",
        address="丸の内1-1",
        phone_number="03-1234-5678",
        establishment_date=date(2020, 1, 1)
    )
    db.session.add(dummy_company)
    db.session.commit()
    return dummy_company, None

@company_bp.route('/statement_of_accounts')
def statement_of_accounts():
    """勘定科目内訳書ページ"""
    page = request.args.get('page', 'deposits')
    company, response = _get_company_or_redirect()
    if response:
        # 開発モードでダミー会社が作られた場合、再度companyをクエリする
        company = Company.query.first()

    config = STATEMENT_PAGES_CONFIG.get(page)
    if not config:
        flash('無効なページです。', 'danger')
        return redirect(url_for('company.statement_of_accounts'))

    items = []
    total = 0
    if not company:
        flash('会社情報が未登録のため、機能を利用できません。', 'warning')
    else:
        items = db.session.query(config['model']).filter_by(company_id=company.id).all()
        if items:
            total = sum(getattr(item, config['total_field'], 0) for item in items)

    context = {
        'page': page,
        'page_title': config['title'],
        'items': items,
        'total': total,
        'add_endpoint_name': config['add_endpoint']
    }

    return render_template('statement_of_accounts.html', **context)

# ---汎用CRUD関数---
def _add_item(page_key):
    config = STATEMENT_PAGES_CONFIG[page_key]
    form = config['form']()
    company, response = _get_company_or_redirect()
    if response: return response
    
    if form.validate_on_submit():
        new_item = config['model'](company_id=company.id)
        form.populate_obj(new_item)
        db.session.add(new_item)
        db.session.commit()
        flash(f'{config["title"]}情報を登録しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page=page_key))
    
    form_template = f'company/{page_key}_form.html'
    return render_template(form_template, form=form, form_title=f'{config["title"]}の新規登録')

def _edit_item(page_key, item_id):
    config = STATEMENT_PAGES_CONFIG[page_key]
    item = db.session.query(config['model']).get_or_404(item_id)
    form = config['form'](obj=item)
    
    if form.validate_on_submit():
        form.populate_obj(item)
        db.session.commit()
        flash(f'{config["title"]}情報を更新しました。', 'success')
        return redirect(url_for('company.statement_of_accounts', page=page_key))
        
    form_template = f'company/{page_key}_form.html'
    return render_template(form_template, form=form, form_title=f'{config["title"]}の編集')

def _delete_item(page_key, item_id):
    config = STATEMENT_PAGES_CONFIG[page_key]
    item = db.session.query(config['model']).get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash(f'{config["title"]}情報を削除しました。', 'success')
    return redirect(url_for('company.statement_of_accounts', page=page_key))

# --- 各項目のルート定義 ---
@company_bp.route('/deposit/add', methods=['GET', 'POST'])
def add_deposit(): return _add_item('deposits')
@company_bp.route('/deposit/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_deposit(item_id): return _edit_item('deposits', item_id)
@company_bp.route('/deposit/delete/<int:item_id>', methods=['POST'])
def delete_deposit(item_id): return _delete_item('deposits', item_id)

@company_bp.route('/notes_receivable/add', methods=['GET', 'POST'])
def add_notes_receivable(): return _add_item('notes_receivable')
@company_bp.route('/notes_receivable/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_notes_receivable(item_id): return _edit_item('notes_receivable', item_id)
@company_bp.route('/notes_receivable/delete/<int:item_id>', methods=['POST'])
def delete_notes_receivable(item_id): return _delete_item('notes_receivable', item_id)

@company_bp.route('/accounts_receivable/add', methods=['GET', 'POST'])
def add_accounts_receivable(): return _add_item('accounts_receivable')
@company_bp.route('/accounts_receivable/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_accounts_receivable(item_id): return _edit_item('accounts_receivable', item_id)
@company_bp.route('/accounts_receivable/delete/<int:item_id>', methods=['POST'])
def delete_accounts_receivable(item_id): return _delete_item('accounts_receivable', item_id)

@company_bp.route('/temporary_payment/add', methods=['GET', 'POST'])
def add_temporary_payment(): return _add_item('temporary_payments')
@company_bp.route('/temporary_payment/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_temporary_payment(item_id): return _edit_item('temporary_payments', item_id)
@company_bp.route('/temporary_payment/delete/<int:item_id>', methods=['POST'])
def delete_temporary_payment(item_id): return _delete_item('temporary_payments', item_id)

@company_bp.route('/loans_receivable/add', methods=['GET', 'POST'])
def add_loans_receivable(): return _add_item('loans_receivable')
@company_bp.route('/loans_receivable/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_loans_receivable(item_id): return _edit_item('loans_receivable', item_id)
@company_bp.route('/loans_receivable/delete/<int:item_id>', methods=['POST'])
def delete_loans_receivable(item_id): return _delete_item('loans_receivable', item_id)

@company_bp.route('/inventory/add', methods=['GET', 'POST'])
def add_inventory(): return _add_item('inventories')
@company_bp.route('/inventory/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_inventory(item_id): return _edit_item('inventories', item_id)
@company_bp.route('/inventory/delete/<int:item_id>', methods=['POST'])
def delete_inventory(item_id): return _delete_item('inventories', item_id)

@company_bp.route('/security/add', methods=['GET', 'POST'])
def add_security(): return _add_item('securities')
@company_bp.route('/security/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_security(item_id): return _edit_item('securities', item_id)
@company_bp.route('/security/delete/<int:item_id>', methods=['POST'])
def delete_security(item_id): return _delete_item('securities', item_id)

@company_bp.route('/fixed_asset/add', methods=['GET', 'POST'])
def add_fixed_asset(): return _add_item('fixed_assets')
@company_bp.route('/fixed_asset/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_fixed_asset(item_id): return _edit_item('fixed_assets', item_id)
@company_bp.route('/fixed_asset/delete/<int:item_id>', methods=['POST'])
def delete_fixed_asset(item_id): return _delete_item('fixed_assets', item_id)

@company_bp.route('/notes_payable/add', methods=['GET', 'POST'])
def add_notes_payable(): return _add_item('notes_payable')
@company_bp.route('/notes_payable/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_notes_payable(item_id): return _edit_item('notes_payable', item_id)
@company_bp.route('/notes_payable/delete/<int:item_id>', methods=['POST'])
def delete_notes_payable(item_id): return _delete_item('notes_payable', item_id)

@company_bp.route('/accounts_payable/add', methods=['GET', 'POST'])
def add_accounts_payable(): return _add_item('accounts_payable')
@company_bp.route('/accounts_payable/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_accounts_payable(item_id): return _edit_item('accounts_payable', item_id)
@company_bp.route('/accounts_payable/delete/<int:item_id>', methods=['POST'])
def delete_accounts_payable(item_id): return _delete_item('accounts_payable', item_id)

@company_bp.route('/temporary_receipt/add', methods=['GET', 'POST'])
def add_temporary_receipt(): return _add_item('temporary_receipts')
@company_bp.route('/temporary_receipt/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_temporary_receipt(item_id): return _edit_item('temporary_receipts', item_id)
@company_bp.route('/temporary_receipt/delete/<int:item_id>', methods=['POST'])
def delete_temporary_receipt(item_id): return _delete_item('temporary_receipts', item_id)

@company_bp.route('/borrowing/add', methods=['GET', 'POST'])
def add_borrowing(): return _add_item('borrowings')
@company_bp.route('/borrowing/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_borrowing(item_id): return _edit_item('borrowings', item_id)
@company_bp.route('/borrowing/delete/<int:item_id>', methods=['POST'])
def delete_borrowing(item_id): return _delete_item('borrowings', item_id)

@company_bp.route('/executive_compensation/add', methods=['GET', 'POST'])
def add_executive_compensation(): return _add_item('executive_compensations')
@company_bp.route('/executive_compensation/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_executive_compensation(item_id): return _edit_item('executive_compensations', item_id)
@company_bp.route('/executive_compensation/delete/<int:item_id>', methods=['POST'])
def delete_executive_compensation(item_id): return _delete_item('executive_compensations', item_id)

@company_bp.route('/land_rent/add', methods=['GET', 'POST'])
def add_land_rent(): return _add_item('land_rents')
@company_bp.route('/land_rent/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_land_rent(item_id): return _edit_item('land_rents', item_id)
@company_bp.route('/land_rent/delete/<int:item_id>', methods=['POST'])
def delete_land_rent(item_id): return _delete_item('land_rents', item_id)

@company_bp.route('/miscellaneous/add', methods=['GET', 'POST'])
def add_miscellaneous(): return _add_item('miscellaneous')
@company_bp.route('/miscellaneous/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_miscellaneous(item_id): return _edit_item('miscellaneous', item_id)
@company_bp.route('/miscellaneous/delete/<int:item_id>', methods=['POST'])
def delete_miscellaneous(item_id): return _delete_item('miscellaneous', item_id)