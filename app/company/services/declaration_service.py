# app/company/services/declaration_service.py
from app.company.forms import DeclarationForm
from app.company.models import (
    Company, Deposit, NotesReceivable, AccountsReceivable, TemporaryPayment,
    LoansReceivable, Inventory, Security, FixedAsset, NotesPayable,
    AccountsPayable, TemporaryReceipt, Borrowing, ExecutiveCompensation,
    LandRent, Miscellaneous
)
from app import db


class DeclarationService:
    """
    申告書フォームに関連するビジネスロジックを処理するサービスクラス。
    """

    def __init__(self, company_id):
        self.company_id = company_id

    def _get_company(self):
        return Company.query.get_or_404(self.company_id)

    def _get_all_statement_data(self):
        return {
            'deposits': Deposit.query.filter_by(company_id=self.company_id).all(),
            'notes_receivable': NotesReceivable.query.filter_by(company_id=self.company_id).all(),
            'accounts_receivable': AccountsReceivable.query.filter_by(company_id=self.company_id).all(),
            'temporary_payments': TemporaryPayment.query.filter_by(company_id=self.company_id).all(),
            'loans_receivable': LoansReceivable.query.filter_by(company_id=self.company_id).all(),
            'inventories': Inventory.query.filter_by(company_id=self.company_id).all(),
            'securities': Security.query.filter_by(company_id=self.company_id).all(),
            'fixed_assets': FixedAsset.query.filter_by(company_id=self.company_id).all(),
            'notes_payable': NotesPayable.query.filter_by(company_id=self.company_id).all(),
            'accounts_payable': AccountsPayable.query.filter_by(company_id=self.company_id).all(),
            'temporary_receipts': TemporaryReceipt.query.filter_by(company_id=self.company_id).all(),
            'borrowings': Borrowing.query.filter_by(company_id=self.company_id).all(),
            'executive_compensations': ExecutiveCompensation.query.filter_by(company_id=self.company_id).all(),
            'land_rents': LandRent.query.filter_by(company_id=self.company_id).all(),
            'miscellaneous_items': Miscellaneous.query.filter_by(company_id=self.company_id).all(),
        }

    def populate_declaration_form(self):
        company = self._get_company()
        form = DeclarationForm(obj=company)
        return form, company

    def get_context_for_declaration_form(self):
        company = self._get_company()
        statement_data = self._get_all_statement_data()
        context = {'company': company, **statement_data}
        return context

    def update_declaration_data(self, form):
        company = self._get_company()
        form.populate_obj(company)
        db.session.add(company)
        db.session.commit()
