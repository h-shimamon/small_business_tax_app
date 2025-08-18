# app/company/services/shareholder_service.py
from flask import g, has_request_context
from flask_login import current_user
from sqlalchemy import func, or_
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
    shareholder = get_shareholder_by_id(shareholder_id) # get_shareholder_by_idは既テナントチェック済み
    # まずフォーム値でモデルを更新
    form.populate_obj(shareholder)
    # 特殊関係人の編集時、「主たる株主と住所が同じ」チェックがONなら住所を主たる株主からコピー
    if shareholder.parent_id is not None and hasattr(form, 'is_address_same_as_main'):
        try:
            same = bool(form.is_address_same_as_main.data)
        except Exception:
            same = False
        if same and shareholder.parent is not None:
            shareholder.zip_code = shareholder.parent.zip_code
            shareholder.prefecture_city = shareholder.parent.prefecture_city
            shareholder.address = shareholder.parent.address
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


# ===== 集計ユーティリティ（最小差分・UI非変更） =====

def _get_metric_column_for_company(company_id):
    company = Company.query.filter_by(id=company_id, user_id=current_user.id).first_or_404()
    name = company.company_name or ""
    if any(corp_type in name for corp_type in ['合同会社', '合名会社', '合資会社']):
        return Shareholder.investment_amount, 'investment_amount'
    return Shareholder.voting_rights, 'voting_rights'


def _get_request_cache():
    if has_request_context():
        if not hasattr(g, '_shareholder_totals_cache'):
            g._shareholder_totals_cache = {}
        return g._shareholder_totals_cache
    return {}


def compute_company_total(company_id):
    metric_col, metric_name = _get_metric_column_for_company(company_id)
    cache = _get_request_cache()
    key = ("company_total", company_id, metric_name)
    if key in cache:
        return cache[key]

    total = db.session.query(func.sum(metric_col)).join(Company).filter(
        Company.id == company_id,
        Company.user_id == current_user.id,
        metric_col.isnot(None),
    ).scalar() or 0

    cache[key] = int(total)
    return int(total)


def compute_group_total(company_id, main_shareholder_id):
    metric_col, metric_name = _get_metric_column_for_company(company_id)
    cache = _get_request_cache()
    key = ("group_total", company_id, main_shareholder_id, metric_name)
    if key in cache:
        return cache[key]

    main = get_shareholder_by_id(main_shareholder_id)
    if main.company_id != company_id:
        return 0

    total = db.session.query(func.sum(metric_col)).join(Company).filter(
        Company.id == company_id,
        Company.user_id == current_user.id,
        metric_col.isnot(None),
        or_(Shareholder.id == main_shareholder_id, Shareholder.parent_id == main_shareholder_id),
    ).scalar() or 0

    cache[key] = int(total)
    return int(total)


def compute_group_totals_map(company_id):
    metric_col, metric_name = _get_metric_column_for_company(company_id)
    cache = _get_request_cache()
    key = ("group_totals_map", company_id, metric_name)
    if key in cache:
        return cache[key]

    group_key = func.coalesce(Shareholder.parent_id, Shareholder.id)
    rows = db.session.query(group_key.label('gid'), func.sum(metric_col)).join(Company).filter(
        Company.id == company_id,
        Company.user_id == current_user.id,
        metric_col.isnot(None),
    ).group_by('gid').all()

    result = {int(gid): int(total or 0) for gid, total in rows}
    cache[key] = result
    return result
