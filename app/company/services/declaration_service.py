# app/company/services/declaration_service.py
from werkzeug.exceptions import NotFound

from app.company.forms import DeclarationForm
from app.company.models import Company
from app.company.services.statement_of_accounts_service import (
    StatementOfAccountsService,
)
from app.extensions import db


class DeclarationService:
    """
    申告書フォームに関連するビジネスロジックを処理するサービスクラス。
    """

    def __init__(self, company_id):
        self.company_id = company_id

    def _get_company(self):
        company = db.session.get(Company, self.company_id)
        if company is None:
            raise NotFound()
        return company

    def _get_all_statement_data(self):
        """STATEMENT_PAGES_CONFIG に基づき各ページのデータを収集する。"""
        soa_service = StatementOfAccountsService(self.company_id)
        keys = [
            'accounts_receivable',
            'accounts_payable',
            'temporary_payments',
            'temporary_receipts',
            'loans_receivable',
            'inventories',
            'securities',
            'fixed_assets',
            'borrowings',
            'executive_compensations',
            'land_rents',
            'misc_income',
            'misc_losses',
        ]
        data = {key: soa_service.get_data_by_type(key) or [] for key in keys}
        data['miscellaneous_items'] = (data.get('misc_income') or []) + (data.get('misc_losses') or [])
        return data

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
