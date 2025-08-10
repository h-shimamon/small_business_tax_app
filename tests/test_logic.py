# tests/test_logic.py
from app import db
from app.company.models import User, Company
from datetime import date

def test_user_can_only_see_their_own_company(app, init_database):
    """
    データベースレベルで、ユーザーが自分の会社情報のみを取得できることを確認する。
    """
    with app.app_context():
        # ユーザー1とユーザー2を取得
        user1 = User.query.filter_by(username='testuser1').first()
        user2 = User.query.filter_by(username='testuser2').first()

        # ユーザー2の会社を作成
        company2 = Company(
            corporate_number='2222222222222',
            company_name='株式会社テスト２',
            company_name_kana='テストニ',
            zip_code='1000002',
            prefecture='東京都',
            city='中央区',
            address='八重洲2-2-2',
            phone_number='03-2222-2222',
            establishment_date=date(2021, 2, 2),
            capital_limit=True,
            is_supported_industry=True,
            is_not_excluded_business=True,
            is_excluded_business=False,
            user_id=user2.id
        )
        db.session.add(company2)
        db.session.commit()

        # ユーザー1として会社情報をクエリ
        user1_companies = Company.query.filter_by(user_id=user1.id).all()
        
        # ユーザー1は自分の会社（company1）のみ取得できるはず
        assert len(user1_companies) == 1
        assert user1_companies[0].company_name == '株式会社テスト１'

        # ユーザー2として会社情報をクエリ
        user2_companies = Company.query.filter_by(user_id=user2.id).all()

        # ユーザー2は自分の会社（company2）のみ取得できるはず
        assert len(user2_companies) == 1
        assert user2_companies[0].company_name == '株式会社テスト２'
