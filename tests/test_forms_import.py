import importlib

from app import create_app


def test_import_and_instantiate_forms():
    app = create_app()
    with app.app_context(), app.test_request_context('/'):
        forms_pkg = importlib.import_module('app.company.forms')
        for cls_name in [
            'CompanyForm', 'DeclarationForm', 'LoginForm',
            'MainShareholderForm', 'RelatedShareholderForm',
            'DepositForm', 'NotesReceivableForm', 'NotesPayableForm',
            'AccountsReceivableForm', 'AccountsPayableForm',
        ]:
            cls = getattr(forms_pkg, cls_name)
            assert cls is not None
            _ = cls()
