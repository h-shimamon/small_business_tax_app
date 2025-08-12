# app/company/services/company_classification_service.py
from app.company.models import Shareholder
from app import db

def classify_company(company_id):
    """
    指定された会社を「同族会社」「非同族会社」に分類する。

    Args:
        company_id (int): 判定対象の会社のID。

    Returns:
        dict: 判定結果を含む辞書。
              例: {
                  'classification': '同族会社',
                  'top_three_percentage': 75.0
              }
              株主が存在しない場合は、'非同族会社'として基本的な値を返す。
    """
    # 1. データ準備
    total_voting_rights = db.session.query(
        db.func.sum(Shareholder.voting_rights)
    ).filter_by(company_id=company_id).scalar() or 0

    if total_voting_rights == 0:
        return {
            'classification': '非同族会社',
            'top_three_percentage': 0.0
        }

    main_shareholders = Shareholder.query.filter_by(
        company_id=company_id, 
        parent_id=None
    ).all()

    group_voting_rights = []
    for main_shareholder in main_shareholders:
        group_total = main_shareholder.voting_rights or 0
        for child in main_shareholder.children:
            group_total += child.voting_rights or 0
        group_voting_rights.append(group_total)
    
    group_voting_rights.sort(reverse=True)

    # 2. 割合計算
    top_three_rights = sum(group_voting_rights[:3])
    top_three_percentage = round((top_three_rights / total_voting_rights) * 100, 2)

    # 3. 判定
    classification = '同族会社' if top_three_percentage > 50 else '非同族会社'

    # 4. 戻り値
    return {
        'classification': classification,
        'top_three_percentage': top_three_percentage
    }
