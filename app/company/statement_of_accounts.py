# app/company/statement_of_accounts.py

from flask import render_template, request, redirect, url_for, flash, current_app, abort
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

# 各内訳ページの情報を一元管理 (変更なし)
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
    
    # テンプレートに渡すコンテキストを更新。add_endpoint_nameは不要になったため削除
    context = {
        'page': page,
        'page_title': config['title'],
        'items': items,
        'total': total,
    }

    return render_template('company/statement_of_accounts.html', **context)

# ---汎用CRUD関数--- (変更なし)
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
    
    form_template = f"company/{config['template']}"
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
        
    form_template = f"company/{config['template']}"
    return render_template(form_template, form=form, form_title=f'{config["title"]}の編集')

def _delete_item(page_key, item_id):
    config = STATEMENT_PAGES_CONFIG[page_key]
    item = db.session.query(config['model']).get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash(f'{config["title"]}情報を削除しました。', 'success')
    return redirect(url_for('company.statement_of_accounts', page=page_key))

# --- ▼▼▼▼▼ ここからがリファクタリングの核心部分 ▼▼▼▼▼ ---
# 45個の個別ルート定義を削除し、以下の3つの汎用ルートに集約する

@company_bp.route('/statement/<string:page_key>/add', methods=['GET', 'POST'])
def add_item(page_key):
    """汎用的な項目追加ビュー"""
    if page_key not in STATEMENT_PAGES_CONFIG:
        abort(404)
    return _add_item(page_key)

@company_bp.route('/statement/<string:page_key>/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(page_key, item_id):
    """汎用的な項目編集ビュー"""
    if page_key not in STATEMENT_PAGES_CONFIG:
        abort(404)
    return _edit_item(page_key, item_id)

@company_bp.route('/statement/<string:page_key>/delete/<int:item_id>', methods=['POST'])
def delete_item(page_key, item_id):
    """汎用的な��目削除ビュー"""
    if page_key not in STATEMENT_PAGES_CONFIG:
        abort(404)
    return _delete_item(page_key, item_id)
