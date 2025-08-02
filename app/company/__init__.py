# app/company/__init__.py

from flask import Blueprint

# Blueprintをここで定義
company_bp = Blueprint(
    'company',
    __name__,
    template_folder='../templates/company', # テンプレートフォルダをより具体的に指定
    static_folder='../static',
    url_prefix='/company'
)

# 分割したルートファイルをインポートして、定義したBlueprintにルートを登録する
from app.company import core, employees, offices, import_data, statement_of_accounts, auth
