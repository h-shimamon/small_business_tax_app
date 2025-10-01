# app/company/services/auth_service.py
from app.company.models import Company, User


class AuthService:
    @staticmethod
    def authenticate_user(username, password):
        """
        ユーザー名とパスワードでユーザーを認証する。
        成功すればUserオブジェクトを、失敗すればNoneを返す。
        """
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def get_company_for_user(user):
        """
        指定されたユーザーに紐づく会社情報を取得する。
        """
        # 現状は最初の1社を返す仕様
        return Company.query.filter_by(user_id=user.id).first()
