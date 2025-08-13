# app/company/services/shareholder_service.py
from flask_login import current_user
from app import db
from app.company.models import Shareholder, Company

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

def add_main_shareholder(company_id, form):
    """主たる株主を新規登録する。会社が現在のユーザーのものであるか確認する。"""
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first_or_404()
    
    new_shareholder = Shareholder()
    form.populate_obj(new_shareholder)
    new_shareholder.company_id = company.id
    
    db.session.add(new_shareholder)
    db.session.commit()
    
    return new_shareholder, None

def add_related_shareholder(company_id, main_shareholder_id, form):
    """特殊関係人を新規登録する。会社と主たる株主が現在のユーザーのものであるか確認する。"""
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first_or_404()
    main_shareholder = get_shareholder_by_id(main_shareholder_id) # get_shareholder_by_idは既テ넌트チェック済み
    
    # main_shareholderが指定されたcompanyに属しているかも確認
    if main_shareholder.company_id != company.id:
        # 404を返すか、エラーメッセージを返すかは要件による
        # ここではNoneを返して、ビュー側で処理することを想定
        return None

    new_related_shareholder = Shareholder(
        company_id=company.id,
        parent_id=main_shareholder.id,
        last_name=form.last_name.data,
        relationship=form.relationship.data,
        officer_position=form.officer_position.data,
        investment_amount=form.investment_amount.data,
        shares_held=form.shares_held.data,
        voting_rights=form.voting_rights.data,
        is_controlled_company=form.is_controlled_company.data
    )
    
    if form.is_address_same_as_main.data:
        new_related_shareholder.zip_code = main_shareholder.zip_code
        new_related_shareholder.prefecture_city = main_shareholder.prefecture_city
        new_related_shareholder.address = main_shareholder.address
    else:
        new_related_shareholder.zip_code = form.zip_code.data
        new_related_shareholder.prefecture_city = form.prefecture_city.data
        new_related_shareholder.address = form.address.data
        
    db.session.add(new_related_shareholder)
    db.session.commit()
    
    return new_related_shareholder

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

