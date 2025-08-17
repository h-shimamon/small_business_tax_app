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
from app.company.services.statement_of_accounts_service import StatementOfAccountsService
from app.company.services.financial_statement_service import FinancialStatementService
from app.company.services.master_data_service import MasterDataService
from flask import session

# Summary mapping for other pages: master type and breakdown document name
SUMMARY_PAGE_MAP = {
    'temporary_payments': ('BS', '仮払金（前渡金）'),
    'loans_receivable': ('BS', '貸付金・受取利息'),
    'inventories': ('BS', '棚卸資産'),
    'securities': ('BS', '有価証券'),
    'fixed_assets': ('BS', '固定資産（土地等）'),
    'notes_payable': ('BS', '支払手形'),
    'accounts_payable': ('BS', '買掛金（未払金・未払費用）'),
    'temporary_receipts': ('BS', '仮受金（前受金・預り金）'),
    'borrowings': ('BS', '借入金及び支払利子'),
    # PL-based pages
    'executive_compensations': ('PL', '役員給与等'),
    'land_rents': ('PL', '地代家賃等'),
    'miscellaneous': ('PL', '雑益・雑損失等'),
}


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
        'navigation_state': get_navigation_state(page),
        'deposit_summary': None
    }

    # Compute generic summary for pages other than those already explicitly handled
    if page in SUMMARY_PAGE_MAP:
        master_type, breakdown_name = SUMMARY_PAGE_MAP[page]
        # Determine source data key and master df
        data_key = 'balance_sheet' if master_type == 'BS' else 'profit_and_loss'
        accounting_total = 0
        from .models import AccountingData
        accounting_data = AccountingData.query.filter_by(company_id=company.id).order_by(AccountingData.created_at.desc()).first()
        if accounting_data:
            source = accounting_data.data.get(data_key, {})
            master_service = MasterDataService()
            df = master_service.get_bs_master_df() if master_type == 'BS' else master_service.get_pl_master_df()
            target_accounts = df[df['breakdown_document'] == breakdown_name].index.tolist()
            def find_and_sum(data_dict):
                total_local = 0
                for _, value in data_dict.items():
                    if isinstance(value, dict):
                        if 'items' in value and isinstance(value['items'], list):
                            for it in value['items']:
                                if isinstance(it, dict) and it.get('name') in target_accounts:
                                    total_local += it.get('amount', 0)
                        else:
                            total_local += find_and_sum(value)
                return total_local
            accounting_total = find_and_sum(source)
        else:
            accounting_total = 0
        # Breakdown total from DB
        model = config['model']
        total_field = getattr(model, config['total_field'])
        breakdown_total = db.session.query(db.func.sum(total_field)).filter_by(company_id=company.id).scalar() or 0
        difference = accounting_total - breakdown_total
        context['generic_summary'] = {
            'bs_total': accounting_total,
            'breakdown_total': breakdown_total,
            'difference': difference
        }
        context['generic_summary_label'] = f"{'B/S上の' if master_type == 'BS' else 'P/L上の'}{config['title']}残高"

    if page == 'deposits':
        from .models import AccountingData
        
        accounting_data = AccountingData.query.filter_by(company_id=company.id).order_by(AccountingData.created_at.desc()).first()

        if not accounting_data:
            flash('会計データがアップロードされていません。合計額を照合するには、先に会計データを選択してください。', 'info')
        else:
            bs_data = accounting_data.data.get('balance_sheet', {})
            
            # マスターデータから「預貯金」に該当する勘定科目リストを取得
            master_data_service = MasterDataService()
            bs_master_df = master_data_service.get_bs_master_df()
            deposit_accounts = bs_master_df[bs_master_df['breakdown_document'] == '預貯金'].index.tolist()

            # 貸借対照表データから該当する勘定科目の残高を合計する
            bs_deposits_total = 0
            
            def find_and_sum(data_dict):
                total = 0
                for key, value in data_dict.items():
                    if isinstance(value, dict):
                        if 'items' in value and isinstance(value['items'], list):
                            for item in value['items']:
                                if isinstance(item, dict) and item.get('name') in deposit_accounts:
                                    total += item.get('amount', 0)
                        else:
                            total += find_and_sum(value)
                return total

            bs_deposits_total = find_and_sum(bs_data)
            
            soa_service = StatementOfAccountsService(company.id)
            deposit_summary = soa_service.get_deposit_summary(bs_deposits_total)
            context['deposit_summary'] = deposit_summary

    elif page == 'notes_receivable':
        from .models import AccountingData

        accounting_data = AccountingData.query.filter_by(company_id=company.id).order_by(AccountingData.created_at.desc()).first()

        if not accounting_data:
            bs_notes_total = 0
            breakdown_total = db.session.query(db.func.sum(NotesReceivable.amount)).filter_by(company_id=company.id).scalar() or 0
            difference = bs_notes_total - breakdown_total
            context['notes_receivable_summary'] = {
                'bs_total': bs_notes_total,
                'breakdown_total': breakdown_total,
                'difference': difference
            }
        else:
            bs_data = accounting_data.data.get('balance_sheet', {})

            # マスターデータから「受取手形」に該当する勘定科目リストを取得
            master_data_service = MasterDataService()
            bs_master_df = master_data_service.get_bs_master_df()
            notes_accounts = bs_master_df[bs_master_df['breakdown_document'] == '受取手形'].index.tolist()

            # 貸借対照表データから該当する勘定科目の残高を合計する
            def find_and_sum(data_dict):
                total = 0
                for key, value in data_dict.items():
                    if isinstance(value, dict):
                        if 'items' in value and isinstance(value['items'], list):
                            for item in value['items']:
                                if isinstance(item, dict) and item.get('name') in notes_accounts:
                                    total += item.get('amount', 0)
                        else:
                            total += find_and_sum(value)
                return total

            bs_notes_total = find_and_sum(bs_data)

            breakdown_total = db.session.query(db.func.sum(NotesReceivable.amount)).filter_by(company_id=company.id).scalar() or 0
            difference = bs_notes_total - breakdown_total
            context['notes_receivable_summary'] = {
                'bs_total': bs_notes_total,
                'breakdown_total': breakdown_total,
                'difference': difference
            }

    elif page == 'accounts_receivable':
        from .models import AccountingData

        accounting_data = AccountingData.query.filter_by(company_id=company.id).order_by(AccountingData.created_at.desc()).first()

        if not accounting_data:
            bs_ar_total = 0
        else:
            bs_data = accounting_data.data.get('balance_sheet', {})

            master_data_service = MasterDataService()
            bs_master_df = master_data_service.get_bs_master_df()
            ar_accounts = bs_master_df[bs_master_df['breakdown_document'] == '売掛金（未収入金）'].index.tolist()

            def find_and_sum(data_dict):
                total = 0
                for key, value in data_dict.items():
                    if isinstance(value, dict):
                        if 'items' in value and isinstance(value['items'], list):
                            for item in value['items']:
                                if isinstance(item, dict) and item.get('name') in ar_accounts:
                                    total += item.get('amount', 0)
                        else:
                            total += find_and_sum(value)
                return total

            bs_ar_total = find_and_sum(bs_data)

        breakdown_total = db.session.query(db.func.sum(AccountsReceivable.balance_at_eoy)).filter_by(company_id=company.id).scalar() or 0
        difference = bs_ar_total - breakdown_total
        context['accounts_receivable_summary'] = {
            'bs_total': bs_ar_total,
            'breakdown_total': breakdown_total,
            'difference': difference
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
