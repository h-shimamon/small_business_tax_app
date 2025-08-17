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

# Summary mapping for other pages: master type and breakdown document name
SUMMARY_PAGE_MAP = {
    'deposits': ('BS', '預貯金'),
    'notes_receivable': ('BS', '受取手形'),
    'accounts_receivable': ('BS', '売掛金'),
    'temporary_payments': ('BS', '仮払金'),
    'loans_receivable': ('BS', '貸付金'),
    'inventories': ('BS', '棚卸資産'),
    'securities': ('BS', '有価証券'),
    'fixed_assets': ('BS', '固定資産（土地等）'),
    'notes_payable': ('BS', '支払手形'),
    'accounts_payable': ('BS', '買掛金'),
    'temporary_receipts': ('BS', '仮受金'),
    'borrowings': ('BS', '借入金'),
    # PL-based pages
    'executive_compensations': ('PL', '役員給与等'),
    'land_rents': ('PL', '地代家賃等'),
    'miscellaneous': ('PL', '雑益・雑損失等'),
}

# Specific account mappings for PL pages where master does not provide breakdown_document linkage
PL_PAGE_ACCOUNTS = {
    # 役員給与等は少なくとも役員報酬・役員賞与を合算対象とする
    'executive_compensations': ['役員報酬', '役員賞与'],
    # 地代家賃等: 地代家賃と賃借料を合算
    'land_rents': ['地代家賃', '賃借料'],
    # 雑益・雑損失等: 雑収入と雑損失を合算
    'miscellaneous': ['雑収入', '雑損失'],
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

    # Helper to compute accounting (source) total for a given SoA page key
    def compute_accounting_total_for(page_key):
        if page_key not in SUMMARY_PAGE_MAP:
            return 0
        master_type, breakdown_name = SUMMARY_PAGE_MAP[page_key]
        data_key = 'balance_sheet' if master_type == 'BS' else 'profit_loss_statement'
        from .models import AccountingData
        accounting_data = AccountingData.query.filter_by(company_id=company.id).order_by(AccountingData.created_at.desc()).first()
        if not accounting_data:
            return 0
        # Special rule: borrowings skip criterion uses BS(借入金) + PL(支払利息)
        if page_key == 'borrowings':
            master_service = MasterDataService()
            def find_and_sum_names(data_dict, names):
                total_local = 0
                for _, value in data_dict.items():
                    if isinstance(value, dict):
                        if 'items' in value and isinstance(value['items'], list):
                            for it in value['items']:
                                if isinstance(it, dict) and it.get('name') in names:
                                    total_local += it.get('amount', 0)
                        else:
                            total_local += find_and_sum_names(value, names)
                return total_local
            bs_source = accounting_data.data.get('balance_sheet', {})
            bs_df = master_service.get_bs_master_df()
            bs_accounts = bs_df[bs_df['breakdown_document'] == '借入金'].index.tolist()
            bs_total_local = find_and_sum_names(bs_source, bs_accounts)
            pl_source = accounting_data.data.get('profit_loss_statement', {})
            pl_total_local = find_and_sum_names(pl_source, ['支払利息'])
            return bs_total_local + pl_total_local

        source = accounting_data.data.get(data_key, {})
        master_service = MasterDataService()
        df = master_service.get_bs_master_df() if master_type == 'BS' else master_service.get_pl_master_df()
        if master_type == 'BS':
            target_accounts = df[df['breakdown_document'] == breakdown_name].index.tolist()
        else:
            # PL: map by predefined accounts (no breakdown_document in PL master)
            target_accounts = PL_PAGE_ACCOUNTS.get(page_key, [])
            if not target_accounts and breakdown_name in df.index:
                target_accounts = [breakdown_name]
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
        return find_and_sum(source)

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
            if compute_accounting_total_for(child_page) == 0:
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

    # Compute generic summary for pages other than those already explicitly handled
    if page in SUMMARY_PAGE_MAP:
        master_type, breakdown_name = SUMMARY_PAGE_MAP[page]
        # Determine source data key and master df
        data_key = 'balance_sheet' if master_type == 'BS' else 'profit_loss_statement'
        accounting_total = 0
        from .models import AccountingData
        accounting_data = AccountingData.query.filter_by(company_id=company.id).order_by(AccountingData.created_at.desc()).first()
        if accounting_data:
            master_service = MasterDataService()
            def find_and_sum_names(data_dict, names):
                total_local = 0
                for _, value in data_dict.items():
                    if isinstance(value, dict):
                        if 'items' in value and isinstance(value['items'], list):
                            for it in value['items']:
                                if isinstance(it, dict) and it.get('name') in names:
                                    total_local += it.get('amount', 0)
                        else:
                            total_local += find_and_sum_names(value, names)
                return total_local

            if page == 'borrowings':
                # BS total for 借入金
                bs_source = accounting_data.data.get('balance_sheet', {})
                bs_df = master_service.get_bs_master_df()
                bs_accounts = bs_df[bs_df['breakdown_document'] == '借入金'].index.tolist()
                bs_total_specific = find_and_sum_names(bs_source, bs_accounts)
                # PL total for 支払利息
                pl_source = accounting_data.data.get('profit_loss_statement', {})
                pl_interest_total = find_and_sum_names(pl_source, ['支払利息'])
            else:
                source = accounting_data.data.get(data_key, {})
                df = master_service.get_bs_master_df() if master_type == 'BS' else master_service.get_pl_master_df()
                if master_type == 'BS':
                    target_accounts = df[df['breakdown_document'] == breakdown_name].index.tolist()
                else:
                    target_accounts = PL_PAGE_ACCOUNTS.get(page, [])
                    if not target_accounts and breakdown_name in df.index:
                        target_accounts = [breakdown_name]
                accounting_total = find_and_sum_names(source, target_accounts)
        else:
            accounting_total = 0
        # Breakdown total from DB
        model = config['model']
        total_field = getattr(model, config['total_field'])
        if page == 'borrowings':
            sum_balance = db.session.query(db.func.sum(model.balance_at_eoy)).filter_by(company_id=company.id).scalar() or 0
            sum_interest = db.session.query(db.func.sum(model.paid_interest)).filter_by(company_id=company.id).scalar() or 0
            breakdown_total = (sum_balance or 0) + (sum_interest or 0)
            # difference = (BS借入金 + PL支払利息) - breakdown_total
            difference = (bs_total_specific if accounting_data else 0) + (pl_interest_total if accounting_data else 0) - breakdown_total
            context['borrowings_summary'] = {
                'bs_total': bs_total_specific if accounting_data else 0,
                'pl_interest_total': pl_interest_total if accounting_data else 0,
                'breakdown_total': breakdown_total,
                'difference': difference,
            }
            # 互換性のため generic_summary にも同値を入れておく（ヘッダー等の判定用）
            context['generic_summary'] = context['borrowings_summary']
            context['generic_summary_label'] = 'B/S上の借入金残高'
        else:
            breakdown_total = db.session.query(db.func.sum(total_field)).filter_by(company_id=company.id).scalar() or 0
            difference = accounting_total - breakdown_total
            context['generic_summary'] = {
                'bs_total': accounting_total,
                'breakdown_total': breakdown_total,
                'difference': difference
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
