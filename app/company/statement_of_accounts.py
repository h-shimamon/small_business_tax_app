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
from app.navigation import get_navigation_state, mark_step_as_completed, unmark_step_as_completed
from .auth import company_required
from app.company.services.master_data_service import MasterDataService
from app.company.services.soa_summary_service import SoASummaryService
from app.company.soa_mappings import SUMMARY_PAGE_MAP, PL_PAGE_ACCOUNTS

# mappings are centralized in app.company.soa_mappings


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

    # Use service to determine source totals for skip decisions

    # Compute skipped pages (source total == 0) for SoA group and optionally redirect forward
    from app.navigation_builder import navigation_tree
    skipped_steps = set()
    soa_children = []
    for node in navigation_tree:
        if node.key == 'statement_of_accounts_group':
            soa_children = node.children
            break
    for child in soa_children:
        child_page = (child.params or {}).get('page')
        if child_page:
            if SoASummaryService.compute_skip_total(company.id, child_page) == 0:
                skipped_steps.add(child.key)

    # If current page should be skipped, redirect to the next non-skipped page (forward search only)
    current_child_index = None
    for idx, child in enumerate(soa_children):
        if (child.params or {}).get('page') == page:
            current_child_index = idx
            break
    if current_child_index is not None and soa_children:
        current_child = soa_children[current_child_index]
        if current_child.key in skipped_steps:
            # forward search to next non-skipped
            for nxt in soa_children[current_child_index+1:]:
                if nxt.key not in skipped_steps:
                    flash('財務諸表に計上されていない勘定科目は自動でスキップされます。', 'skip')
                    return redirect(url_for('company.statement_of_accounts', page=(nxt.params or {}).get('page')))
            # wrap-around to 申告書データ は保留のため遷移しない

    items = db.session.query(config['model']).filter_by(company_id=company.id).all()
    total = sum(getattr(item, config['total_field'], 0) for item in items)
    
    context = {
        'page': page,
        'page_title': config['title'],
        'items': items,
        'total': total,
        'navigation_state': get_navigation_state(page, skipped_steps=skipped_steps),
        'deposit_summary': None,
        'soa_next_url': None,
        'soa_next_name': None
    }

    # Helper: compute next Statement of Accounts page URL and name
    def compute_next_soa(page_key):
        try:
            from app.navigation_builder import navigation_tree
            from flask import url_for
            for node in navigation_tree:
                if node.key == 'statement_of_accounts_group':
                    children = node.children
                    for idx, child in enumerate(children):
                        child_page = (child.params or {}).get('page')
                        if child_page == page_key:
                            if idx + 1 < len(children):
                                nxt = children[idx + 1]
                                return url_for('company.statement_of_accounts', page=(nxt.params or {}).get('page')), nxt.name
                            break
        except Exception:
            pass
        return None, None

    # Compute generic summary using service (no UI/keys change)
    if page in SUMMARY_PAGE_MAP:
        master_type, _ = SUMMARY_PAGE_MAP[page]
        model = config['model']
        total_field_name = config['total_field']
        diff = SoASummaryService.compute_difference(company.id, page, model, total_field_name)
        if page == 'borrowings':
            context['borrowings_summary'] = {
                'bs_total': diff.get('bs_total', 0),
                'pl_interest_total': diff.get('pl_interest_total', 0),
                'breakdown_total': diff.get('breakdown_total', 0),
                'difference': diff.get('difference', 0),
            }
            # Keep generic_summary aligned for header logic
            context['generic_summary'] = context['borrowings_summary']
            context['generic_summary_label'] = 'B/S上の借入金残高'
        else:
            context['generic_summary'] = {
                'bs_total': diff.get('bs_total', 0),
                'breakdown_total': diff.get('breakdown_total', 0),
                'difference': diff.get('difference', 0),
            }
            context['generic_summary_label'] = f"{'B/S上の' if master_type == 'BS' else 'P/L上の'}{config['title']}残高"
        # Map to page-specific summary keys for templates
        if page == 'deposits':
            context['deposit_summary'] = context['generic_summary']
        elif page == 'notes_receivable':
            context['notes_receivable_summary'] = context['generic_summary']
        elif page == 'accounts_receivable':
            context['accounts_receivable_summary'] = context['generic_summary']
        # Mark step completed if reconciled
        step_key = 'fixed_assets_soa' if page == 'fixed_assets' else page
        difference = context.get('generic_summary', {}).get('difference', 0)
        if difference == 0:
            mark_step_as_completed(step_key)
        else:
            unmark_step_as_completed(step_key)
        # Next link
        context['soa_next_url'], context['soa_next_name'] = compute_next_soa(page)
    # Refresh navigation after potential step completion
    context['navigation_state'] = get_navigation_state(page, skipped_steps=skipped_steps)
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
        flash(f"{config['title']}情報を登録しました。", 'success')
        return redirect(url_for('company.statement_of_accounts', page=page_key))
    form_template = f"company/{config['template']}"
    return render_template(form_template, form=form, form_title=f"{config['title']}の新規登録", navigation_state=get_navigation_state(page_key))

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
        flash(f"{config['title']}情報を更新しました。", 'success')
        return redirect(url_for('company.statement_of_accounts', page=page_key))
    if request.method == 'GET':
        form = config['form'](obj=item)
    form_template = f"company/{config['template']}"
    return render_template(form_template, form=form, form_title=f"{config['title']}の編集", navigation_state=get_navigation_state(page_key))

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
    flash(f"{config['title']}情報を削除しました。", 'success')
    return redirect(url_for('company.statement_of_accounts', page=page_key))
