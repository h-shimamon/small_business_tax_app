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
# このインポートは、各ファイルがBlueprintにルートを登録するために必要ですが、
# 循環インポートを避けるため、通常はビュー関数の末尾やアプリケーションファクトリ内で行います。
# ruffのエラー(F401)を避けるため、ここではコメントアウトし、必要に応じて他の場所でインポートします。
# from app.company import core, shareholders, offices, import_data, statement_of_accounts, auth, models

