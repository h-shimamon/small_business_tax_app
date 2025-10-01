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


# このブループリントに関連するビューとモデルをインポートします。
# これにより、アプリケーションファクトリ(create_app)がビューの詳細を知る必要がなくなり、
# 構造がクリーンに保たれます。
from . import (  # noqa: E402, F401
    auth,
    core,
    filings,
    financial_statements,
    fixed_assets_pages,
    import_data,
    models,
    offices,
    shareholders,
    statement_of_accounts,
)
