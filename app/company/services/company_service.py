# app/company/services/company_service.py
from app import db
from app.company.models import Company

class CompanyService:
    @staticmethod
    def get_company_by_user(user_id):
        """ユーザーIDに基づいて会社情報を取得する"""
        return Company.query.filter_by(user_id=user_id).first()

    @staticmethod
    def create_or_update_company(form, user_id):
        """会社情報を作成または更新する"""
        company = CompanyService.get_company_by_user(user_id)
        
        if company:  # 更新
            form.populate_obj(company)
        else:  # 新規作成
            company = Company(user_id=user_id)
            form.populate_obj(company)
            db.session.add(company)
        
        db.session.commit()
        return company
