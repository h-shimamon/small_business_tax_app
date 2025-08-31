# Centralized configuration for Statement of Accounts pages
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
    LandRentForm, MiscellaneousForm, MiscellaneousIncomeForm, MiscellaneousLossForm
)
from typing import TypedDict, Optional, Callable, Any, Dict

# Typed config for SoA pages (non-functional; for developer clarity)
class StatementPageConfig(TypedDict, total=False):
    model: Any
    form: Any
    title: str
    total_field: str
    template: str
    query_filter: Callable[[Any], Any]


STATEMENT_PAGES_CONFIG: Dict[str, StatementPageConfig] = {
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
    # 分割ページ（雑収入 / 雑損失）
    'misc_income': {'model': Miscellaneous, 'form': MiscellaneousIncomeForm, 'title': '雑収入', 'total_field': 'amount', 'template': 'miscellaneous_form.html', 'query_filter': lambda q: q.filter(Miscellaneous.account_name == '雑収入')},
    'misc_losses': {'model': Miscellaneous, 'form': MiscellaneousLossForm, 'title': '雑損失', 'total_field': 'amount', 'template': 'miscellaneous_form.html', 'query_filter': lambda q: q.filter(Miscellaneous.account_name == '雑損失')},
}
