# app/company/services/shareholder_service.py
from flask_login import current_user
from app import db
from app.company.models import Shareholder, Company
from app.company.forms import MainShareholderForm, RelatedShareholderForm

def get_shareholders_by_company(company_id):
    """
    指定された会社の株主情報を取得する。
    ただし、その会社が現在のユーザーのものであることを確認する。
    """
    # Company.user_id を使って、current_user の会社であることを保証する
    return Shareholder.query.join(Company).filter(
        Company.id == company_id,
        Company.user_id == current_user.id
    ).order_by(Shareholder.id).all()

def get_main_shareholders(company_id):
    """
    指定された会社の主たる株主（親がいない）を取得する。
    ただし、その会社が現在のユーザーのものであることを確認する。
    """
    return Shareholder.query.join(Company).filter(
        Company.id == company_id,
        Company.user_id == current_user.id,
        Shareholder.parent_id.is_(None)
    ).order_by(Shareholder.id).all()

def get_shareholder_by_id(shareholder_id):
    """
    IDで株主情報を取得する。
    ただし、その株主が現在のユーザーの会社に属していることを確認する。
    """
    return Shareholder.query.join(Company).filter(
        Shareholder.id == shareholder_id,
        Company.user_id == current_user.id
    ).first_or_404()

def add_shareholder(company_id, form, parent_id=None):
    """
    株主を新規登録する。parent_idの有無で主たる/特殊関係人を判断する。
    成功時は (shareholder, None)、失敗時は (None, error_message) を返す。
    """
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first_or_404()
    
    new_shareholder = Shareholder(company_id=company.id)

    if parent_id:
        parent_shareholder = get_shareholder_by_id(parent_id)
        if parent_shareholder.company_id != company.id:
            return None, "親株主の会社が一致しません。"
        new_shareholder.parent_id = parent_id
        
        # フォームに住所コピー機能があれば実行
        if hasattr(form, 'is_address_same_as_main') and form.is_address_same_as_main.data:
            if hasattr(form, 'populate_address_from_main_shareholder'):
                form.populate_address_from_main_shareholder(parent_shareholder)

    form.populate_obj(new_shareholder)
    
    db.session.add(new_shareholder)
    db.session.commit()
    
    return new_shareholder, None

def get_related_shareholders(main_shareholder_id):
    """
    指定された主たる株主に関連する特殊関係人を取得する。
    主たる株主が現在のユーザーのものであることを確認する。
    """
    main_shareholder = get_shareholder_by_id(main_shareholder_id) # get_shareholder_by_idは既テ넌트チェック済み
    return Shareholder.query.filter_by(parent_id=main_shareholder.id).all()

def update_shareholder(shareholder_id, form):
    """
    株主情報を更新する。
    更新対象が現在のユーザーの会社に属することを確認する。
    """
    shareholder = get_shareholder_by_id(shareholder_id) # get_shareholder_by_idは既テ넌트チェック済み
    form.populate_obj(shareholder)
    db.session.commit()
    return shareholder

def delete_shareholder(shareholder_id):
    """
    株主情報を削除する。
    削除対象が現在のユーザーの会社に属することを確認する。
    """
    shareholder = get_shareholder_by_id(shareholder_id) # get_shareholder_by_idは既テ넌트チェック済み
    db.session.delete(shareholder)
    db.session.commit()
    return shareholder


def get_shareholder_form(shareholder):
    """
    株主オブジェクトに基づき、適切なフォームクラスを返す。
    """
    if shareholder.parent_id is None:
        # 主たる株主の場合
        return MainShareholderForm
    else:
        # 特殊関係人の場合
        return RelatedShareholderForm


def get_main_shareholder_group_number(company_id, main_shareholder_id):
    """
    指定された主たる株主が、その会社の主たる株主リストの中で何番目かを返す。
    リストのインデックスは0から始まるため、+1して返す。
    見つからない場合は -1 を返す。
    """
    main_shareholders = get_main_shareholders(company_id)
    for i, shareholder in enumerate(main_shareholders):
        if shareholder.id == main_shareholder_id:
            return i + 1
    return -1

