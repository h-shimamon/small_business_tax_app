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
from typing import TypedDict, Callable, Any, Dict, List

# Typed config for SoA pages (non-functional; for developer clarity)
class StatementPageConfig(TypedDict, total=False):
    model: Any
    form: Any
    title: str
    total_field: str
    template: str
    query_filter: Callable[[Any], Any]
    form_fields: List[Dict[str, Any]]


STATEMENT_PAGES_CONFIG: Dict[str, StatementPageConfig] = {
    'deposits': {'model': Deposit, 'form': DepositForm, 'title': '預貯金等', 'total_field': 'balance', 'template': 'deposit_form.html'},
    'notes_receivable': {'model': NotesReceivable, 'form': NotesReceivableForm, 'title': '受取手形', 'total_field': 'amount', 'template': 'notes_receivable_form.html'},
    'accounts_receivable': {
        'model': AccountsReceivable,
        'form': AccountsReceivableForm,
        'title': '売掛金（未収入金）',
        'total_field': 'balance_at_eoy',
        'template': 'accounts_receivable_form.html',
        'form_fields': [
            {'name': 'account_name', 'autofocus': True},
            {'name': 'registration_number', 'placeholder': '例：1234567890123'},
            {'name': 'partner_name', 'placeholder': '例：株式会社 △△商会'},
            {'name': 'partner_address', 'placeholder': '例：東京都千代田区〇〇町1-2-3'},
            {'name': 'balance_at_eoy', 'type': 'number', 'placeholder': '例：500000'},
            {'name': 'remarks', 'placeholder': '例：商品Aの売上代金'},
        ],
    },
    'temporary_payments': {
        'model': TemporaryPayment,
        'form': TemporaryPaymentForm,
        'title': '仮払金（前渡金）',
        'total_field': 'balance_at_eoy',
        'template': 'temporary_payment_form.html',
        'form_fields': [
            {'name': 'account_name', 'autofocus': True},
            {'name': 'registration_number', 'placeholder': '例：1234567890123'},
            {'name': 'partner_name', 'placeholder': '例：株式会社 □□'},
            {'name': 'partner_address', 'placeholder': '例：東京都中央区〇〇1-2-3'},
            {'name': 'relationship', 'placeholder': '例：代表者の子会社'},
            {'name': 'balance_at_eoy', 'type': 'number', 'placeholder': '例：300000'},
            {'name': 'transaction_details', 'placeholder': '例：出張旅費の仮払い'},
        ],
    },
    'loans_receivable': {
        'model': LoansReceivable,
        'form': LoansReceivableForm,
        'title': '貸付金・受取利息',
        'total_field': 'balance_at_eoy',
        'template': 'loans_receivable_form.html',
        'form_fields': [
            {'name': 'registration_number', 'autofocus': True, 'placeholder': '例：1234567890123'},
            {'name': 'borrower_name', 'placeholder': '例：株式会社 〇〇商事'},
            {'name': 'borrower_address', 'placeholder': '例：東京都千代田区〇〇1-2-3'},
            {'name': 'relationship', 'placeholder': '例：代表者の親族会社'},
            {'name': 'balance_at_eoy', 'placeholder': '例：300000'},
            {'name': 'received_interest', 'placeholder': '例：15000'},
            {'name': 'interest_rate', 'placeholder': '例：2.0'},
            {'name': 'collateral_details', 'placeholder': '例：不動産（東京都港区…）'},
        ],
    },
    'inventories': {
        'model': Inventory,
        'form': InventoryForm,
        'title': '棚卸資産',
        'total_field': 'balance_at_eoy',
        'template': 'inventories_form.html',
        'form_fields': [
            {'name': 'item_name', 'autofocus': True},
            {'name': 'location'},
            {'name': 'quantity'},
            {'name': 'unit'},
            {'name': 'unit_price'},
            {'name': 'balance_at_eoy'},
            {'name': 'remarks'},
        ],
    },
    'securities': {
        'model': Security,
        'form': SecurityForm,
        'title': '有価証券',
        'total_field': 'balance_at_eoy',
        'template': 'securities_form.html',
        'form_fields': [
            {'name': 'security_type', 'autofocus': True},
            {'name': 'issuer'},
            {'name': 'quantity'},
            {'name': 'balance_at_eoy'},
            {'name': 'remarks'},
        ],
    },
    'fixed_assets': {
        'model': FixedAsset,
        'form': FixedAssetForm,
        'title': '固定資産（土地等）',
        'total_field': 'balance_at_eoy',
        'template': 'fixed_assets_form.html',
        'form_fields': [
            {'name': 'asset_type', 'autofocus': True},
            {'name': 'location'},
            {'name': 'area'},
            {'name': 'balance_at_eoy'},
            {'name': 'remarks'},
        ],
    },
    'notes_payable': {'model': NotesPayable, 'form': NotesPayableForm, 'title': '支払手形', 'total_field': 'amount', 'template': 'notes_payable_form.html'},
    'accounts_payable': {
        'model': AccountsPayable,
        'form': AccountsPayableForm,
        'title': '買掛金（未払金・未払費用）',
        'total_field': 'balance_at_eoy',
        'template': 'accounts_payable_form.html',
        'form_fields': [
            {'name': 'registration_number', 'autofocus': True, 'placeholder': '例：1234567890123'},
            {'name': 'partner_name', 'placeholder': '例：株式会社〇〇商事（または氏名）'},
            {'name': 'partner_address', 'placeholder': '例：東京都千代田区丸の内…'},
            {'name': 'balance_at_eoy', 'type': 'number', 'placeholder': '例：1000000'},
            {'name': 'remarks', 'placeholder': '例：仕入代金'},
        ],
    },
    'temporary_receipts': {
        'model': TemporaryReceipt,
        'form': TemporaryReceiptForm,
        'title': '仮受金（前受金・預り金）',
        'total_field': 'balance_at_eoy',
        'template': 'temporary_receipts_form.html',
        'form_fields': [
            {'name': 'account_name', 'autofocus': True, 'placeholder': '例：預り金'},
            {'name': 'partner_name', 'placeholder': '例：株式会社 △△'},
            {'name': 'balance_at_eoy', 'placeholder': '例：100000'},
            {'name': 'transaction_details', 'rows': 3, 'placeholder': '例：保証金の預り'},
        ],
    },
    'borrowings': {
        'model': Borrowing,
        'form': BorrowingForm,
        'title': '借入金及び支払利子',
        'total_field': 'balance_at_eoy',
        'template': 'borrowings_form.html',
        'form_fields': [
            {'name': 'lender_name', 'autofocus': True, 'placeholder': '例：〇〇銀行'},
            {'name': 'is_subsidiary', 'render': 'checkbox'},
            {'name': 'balance_at_eoy', 'placeholder': '例：5000000'},
            {'name': 'interest_rate', 'placeholder': '例：1.8'},
            {'name': 'paid_interest', 'placeholder': '例：120000'},
            {'name': 'remarks', 'placeholder': '例：設備投資のため'},
        ],
    },
    'executive_compensations': {
        'model': ExecutiveCompensation,
        'form': ExecutiveCompensationForm,
        'title': '役員給与等',
        'total_field': 'total_compensation',
        'template': 'executive_compensations_form.html',
        'form_fields': [
            {'name': 'shareholder_name', 'autofocus': True, 'placeholder': '例：山田 太郎'},
            {'name': 'relationship', 'placeholder': '例：代表取締役'},
            {'name': 'position', 'placeholder': '例：代表取締役社長'},
            {'name': 'base_salary', 'placeholder': '例：500000'},
            {'name': 'other_allowances', 'placeholder': '例：役員賞与は無し'},
            {'name': 'total_compensation', 'placeholder': '例：600000'},
        ],
    },
    'land_rents': {
        'model': LandRent,
        'form': LandRentForm,
        'title': '地代家賃等',
        'total_field': 'rent_paid',
        'template': 'land_rents_form.html',
        'form_fields': [
            {'name': 'account_name', 'autofocus': True, 'placeholder': '例：地代'},
            {'name': 'lessor_name', 'placeholder': '例：〇〇不動産'},
            {'name': 'property_details', 'placeholder': '例：東京都港区六本木6-10-1'},
            {'name': 'rent_paid', 'placeholder': '例：200000'},
            {'name': 'remarks', 'placeholder': '例：本店オフィス賃料'},
        ],
    },
    'miscellaneous': {
        'model': Miscellaneous,
        'form': MiscellaneousForm,
        'title': '雑益・雑損失等',
        'total_field': 'amount',
        'template': 'miscellaneous_form.html',
        'form_fields': [
            {'name': 'account_name'},
            {'name': 'details'},
            {'name': 'amount'},
            {'name': 'remarks'},
        ],
    },
    # 分割ページ（雑収入 / 雑損失）
    'misc_income': {
        'model': Miscellaneous,
        'form': MiscellaneousIncomeForm,
        'title': '雑収入',
        'total_field': 'amount',
        'template': 'miscellaneous_form.html',
        'query_filter': lambda q: q.filter(Miscellaneous.account_name == '雑収入'),
        'form_fields': [
            {'name': 'account_name'},
            {'name': 'details'},
            {'name': 'amount'},
            {'name': 'remarks'},
        ],
    },
    'misc_losses': {
        'model': Miscellaneous,
        'form': MiscellaneousLossForm,
        'title': '雑損失',
        'total_field': 'amount',
        'template': 'miscellaneous_form.html',
        'query_filter': lambda q: q.filter(Miscellaneous.account_name == '雑損失'),
        'form_fields': [
            {'name': 'account_name'},
            {'name': 'details'},
            {'name': 'amount'},
            {'name': 'remarks'},
        ],
    },
}
