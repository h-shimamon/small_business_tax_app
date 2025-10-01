# app/company/utils.py
from functools import wraps

from flask import redirect, url_for


def set_page_title_and_verify_company_type(f):
    """
    会社の法人種別に基づいてページタイトルを設定し、不適切な場合はリダイレクトするデコレーター。
    このデコレーターは @company_required の後に適用される必要があり、
    第一引数として company オブジェクトを受け取ることを前提とします。
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # @company_required から渡される company オブジェクトは第一引数に入っている
        if not args:
            # company オブジェクトが渡されないエラーケース
            return redirect(url_for('company.info')) # または適切なエラーページへ
        
        company = args[0]
        
        company_name = company.company_name
        if '株式会社' in company_name or '有限会社' in company_name:
            page_title = '株主情報'
        elif any(corp_type in company_name for corp_type in ['合同会社', '合名会社', '合資会社']):
            page_title = '社員情報'
        else:
            return redirect(url_for('company.declaration'))
        
        # page_titleをキーワード引数としてビュー関数に渡す
        kwargs['page_title'] = page_title
        return f(*args, **kwargs)
    return decorated_function

def get_officer_choices(page_title):
    """
    法人種別（ページタイトル）に応じて役職の選択肢を返すヘルパー関数。
    """
    if page_title == '株主情報':
        return [
            ('代表取締役', '代表取締役'),
            ('取締役', '取締役'),
            ('会計参与', '会計参与'),
            ('監査役', '監査役'),
            ('その他', 'その他')
        ]
    elif page_title == '社員情報':
        return [
            ('代表社員', '代表社員'),
            ('業務執行社員', '業務執行社員'),
            ('有限責任社員', '有限責任社員'),
            ('無限責任社員', '無限責任社員'),
            ('その他', 'その他')
        ]
    return []
