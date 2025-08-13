Here is the folder structure of the current working directories:

/Users/shimamorihayato/Projects/small_business_tax_app/
├───.gitignore
├───config.py
├───requirements.txt
├───run.py
├───template_beppyo1.pdf
├───test_debug_output.html
├───開発指令書.txt
├───__pycache__/
├───.git/...
├───.pytest_cache/
│   ├───.gitignore
│   ├───CACHEDIR.TAG
│   ├───README.md
│   └───v/
│       └───cache/
│           ├───lastfailed
│           └───nodeids
├───.ruff_cache/
│   ├───.gitignore
│   ├───CACHEDIR.TAG
│   └───0.12.5/
│       ├───10837701606304150466
│       ├───13266355873280770664
│       ├───1564760373340744003
│       ├───16315717994540566649
│       ├───3584378682808118370
│       └───6730629354560116639
├───.serena/
│   ├───project.yml
│   ├───cache/
│   │   └───python/
│   │       └───document_symbols_cache_v23-06-25.pkl
│   └───memories/
├───app/
│   ├───__init__.py
│   ├───commands.py
│   ├───extensions.py
│   ├───navigation_builder.py
│   ├───navigation_models.py
│   ├───navigation.py
│   ├───utils.py
│   ├───__pycache__/
│   ├───company/
│   │   ├───__init__.py
│   │   ├───auth.py
│   │   ├───core.py
│   │   ├───forms.py
│   │   ├───import_data.py
│   │   ├───models.py
│   │   ├───offices.py
│   │   ├───parser_factory.py
│   │   ├───shareholders.py
│   │   ├───statement_of_accounts.py
│   │   ├───utils.py
│   │   ├───__pycache__/
│   │   ├───parsers/
│   │   │   ├───base_parser.py
│   │   │   ├───freee_parser.py
│   │   │   ├───moneyforward_parser.py
│   │   │   ├───other_parser.py
│   │   │   ├───yayoi_parser.py
│   │   │   └───__pycache__/
│   │   └───services/
│   │       ├───__init__.py
│   │       ├───auth_service.py
│   │       ├───company_classification_service.py
│   │       ├───company_service.py
│   │       ├───data_mapping_service.py
│   │       ├───declaration_service.py
│   │       ├───financial_statement_service.py
│   │       ├───master_data_service.py
│   │       ├───shareholder_service.py
│   │       ├───statement_of_accounts_service.py
│   │       └───__pycache__/
│   ├───static/
│   │   ├───css/
│   │   │   ├───base/
│   │   │   │   ├───base.css
│   │   │   │   └───variables.css
│   │   │   ├───components/
│   │   │   │   ├───buttons.css
│   │   │   │   ├───card.css
│   │   │   │   ├───common_components.css
│   │   │   │   ├───forms.css
│   │   │   │   ├───layout.css
│   │   │   │   ├───navigation.css
│   │   │   │   └───tables.css
│   │   │   └───pages/
│   │   │       ├───data_mapping.css
│   │   │       ├───declaration_form.css
│   │   │       ├───financial_statements.css
│   │   │       ├───misc.css
│   │   │       ├───register_shareholder.css
│   │   │       ├───select_software.css
│   │   │       ├───shareholder_list.css
│   │   │       ├───statement_of_accounts.css
│   │   │       └───upload_data.css
│   │   └───js/
│   │       └───address_autofill.js
│   └───templates/
│       ├───base.html
│       ├───index.html
│       ├───register.html
│       ├───result.html
│       └───company/
│           ├───_form_helpers.html
│           ├───_layout_helpers.html
│           ├───_wizard_sidebar.html
│           ├───accounts_payable_form.html
│           ├───accounts_receivable_form.html
│           ├───borrowings_form.html
│           ├───confirm_related_shareholder.html
│           ├───data_mapping.html
│           ├───declaration_form.html
│           ├───deposit_form.html
│           ├───edit_related_shareholder.html
│           ├───edit_shareholder.html
│           ├───executive_compensations_form.html
│           ├───financial_statements.html
│           ├───fixed_assets_form.html
│           ├───inventories_form.html
│           ├───land_rents_form.html
│           ├───loans_receivable_form.html
│           ├───login.html
│           ├───manage_mappings.html
│           ├───miscellaneous_form.html
│           ├───next_main_shareholder.html
│           ├───notes_payable_form.html
│           ├───notes_receivable_form.html
│           ├───office_form.html
│           ├───office_list.html
│           ├───register_related_shareholder.html
│           ├───register_shareholder.html
│           ├───reset_confirmation.html
│           ├───securities_form.html
│           ├───select_software.html
│           ├───shareholder_form.html
│           ├───shareholder_list.html
│           ├───statement_of_accounts.html
│           ├───temporary_payment_form.html
│           ├───temporary_receipts_form.html
│           ├───upload_data.html
│           └───_cards/
│               ├───accounts_payable_card.html
│               ├───accounts_receivable_card.html
│               ├───borrowings_card.html
│               ├───deposits_card.html
│               ├───executive_compensations_card.html
│               ├───fixed_assets_card.html
│               ├───inventories_card.html
│               ├───land_rents_card.html
│               ├───loans_receivable_card.html
│               ├───miscellaneous_card.html
│               ├───notes_payable_card.html
│               ├───notes_receivable_card.html
│               ├───securities_card.html
│               ├───temporary_payments_card.html
│               └───temporary_receipts_card.html
├───instance/
│   └───uploads/...
├───migrations/
│   ├───alembic.ini
│   ├───env.py
│   ├───README
│   ├───script.py.mako
│   ├───__pycache__/
│   └───versions/
│       ├───31722a09f46e_add_email_column_to_user_model.py
│       ├───4d076bbb4efb_add_constraints_and_columns_to_.py
│       ├───71f6d8f1b56b_add_address_components_to_shareholder.py
│       ├───8d675e777cd4_change_zip_code_length_in_shareholder_.py
│       ├───91859660db66_initial_migration_from_current_models.py
│       ├───d70af01038af_rename_is_officer_to_is_controlled_.py
│       ├───f4f5494df524_add_parent_id_and_investment_amount_to_.py
│       └───__pycache__/
├───resources/
│   └───masters/
│       ├───_version.txt
│       ├───balance_sheet.csv
│       └───profit_and_loss.csv
├───temporary/
│   ├───マネーフォワードサンプル202404-202403.txt
│   ├───勘定科目サンプル2025.csv
│   └───仕訳帳データ取込要件.txt
├───tests/
│   ├───conftest.py
│   ├───test_tenancy.py
│   └───__pycache__/
└───venv/
    ├───bin/...
    ├───include/...
    └───lib/...