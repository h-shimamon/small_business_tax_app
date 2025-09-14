# app/company/__init__.py
from flask import Blueprint

# Blueprintをここで定義
company_bp = Blueprint(
    'company',
    __name__,
    template_folder='../templates/company',
    static_folder='../static',
    url_prefix='/company'
)

# Inject UI context (ui_options) into templates via app_context_processor
try:
    from app.ui.context import attach_company_ui_context  # lazy import
    attach_company_ui_context(company_bp)
except Exception:
    pass

# このブループリントに関連するビューとモデルをインポートします。
# これにより、アプリケーションファクトリ(create_app)がビューの詳細を知る必要がなくなり、
# 構造がクリーンに保たれます。
from . import core, shareholders, offices, import_data, statement_of_accounts, auth, models, financial_statements, fixed_assets_pages, filings  # noqa: E402, F401
