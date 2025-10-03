# app/company/services/company_service.py
from app.company.models import Company
from app.services.db_utils import session_scope


class CompanyService:
    @staticmethod
    def get_company_by_user(user_id):
        """ユーザーIDに基づいて会社情報を取得する"""
        return Company.query.filter_by(user_id=user_id).first()

    @staticmethod
    def _ensure_required_fields(company):
        required_values = {
            'corporate_number': company.corporate_number,
            'company_name': company.company_name,
            'company_name_kana': company.company_name_kana,
            'zip_code': company.zip_code,
            'prefecture': company.prefecture,
            'city': company.city,
            'address': company.address,
            'phone_number': company.phone_number,
            'establishment_date': company.establishment_date,
        }
        missing = [field for field, value in required_values.items() if value in (None, '')]
        if missing:
            raise ValueError(f"必須項目が不足しています: {', '.join(missing)}")

    @staticmethod
    def create_or_update_company(form, user_id):
        """会社情報を作成または更新する"""
        company = CompanyService.get_company_by_user(user_id)

        if company:  # 更新
            form.populate_obj(company)
        else:  # 新規作成
            company = Company(user_id=user_id)
            form.populate_obj(company)

        raw_office_count = getattr(getattr(form, 'office_count', None), 'data', None)
        company.apply_office_count_input(raw_office_count if raw_office_count is not None else company.office_count)
        if hasattr(form, 'is_excluded_business'):
            company.apply_excluded_business_input(getattr(form.is_excluded_business, 'data', None))

        CompanyService._ensure_required_fields(company)

        with session_scope() as session:
            session.add(company)

        return company
