# app/company/services/company_classification_service.py
from app.company.models import Company, Shareholder
from app import db

def classify_company(company_id):
    """
    指定された会社を「同族会社」「非同族会社」に分類する。
    会社の種別に応じて、議決権または出資金額を基準に判定する。

    Args:
        company_id (int): 判定対象の会社のID。

    Returns:
        dict: 判定結果を含む辞書。
    """
    # 1. 会社情報を取得し、判定基準を決定
    company = Company.query.get_or_404(company_id)
    company_name = company.company_name

    if any(corp_type in company_name for corp_type in ['合同会社', '合名会社', '合資会社']):
        # 持分会社の場合：出資金額を基準にする
        metric_to_sum = Shareholder.investment_amount
    else:
        # 株式会社・有限会社の場合：議決権を基準にする
        metric_to_sum = Shareholder.voting_rights

    # 2. データ準備
    total_value = db.session.query(
        db.func.sum(metric_to_sum)
    ).filter(Shareholder.company_id == company_id, metric_to_sum.isnot(None)).scalar() or 0

    if total_value == 0:
        return {
            'classification': '非同族会社',
            'top_three_percentage': 0.0
        }

    main_shareholders = Shareholder.query.filter_by(
        company_id=company_id, 
        parent_id=None
    ).all()

    group_values = []
    for main_shareholder in main_shareholders:
        group_total = getattr(main_shareholder, metric_to_sum.name) or 0
        for child in main_shareholder.children:
            group_total += getattr(child, metric_to_sum.name) or 0
        group_values.append(group_total)
    
    group_values.sort(reverse=True)

    # 3. 割合計算
    top_three_value = sum(group_values[:3])
    top_three_percentage = round((top_three_value / total_value) * 100, 2)

    # 4. 判定
    classification = '同族会社' if top_three_percentage > 50 else '非同族会社'

    # 5. 戻り値
    return {
        'classification': classification,
        'top_three_percentage': top_three_percentage
    }
