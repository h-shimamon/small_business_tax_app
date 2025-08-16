# tests/conftest.py
from datetime import date
import pytest
from app import create_app, db
from app.company.models import User, Company, Shareholder

@pytest.fixture(scope='function')
def app():
    """
    テスト関数ごとに独立したFlaskアプリケーションインスタンスを作成するフィクスチャ。
    """
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',  # テスト用のシークレットキーを追加
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SERVER_NAME': 'localhost'
    })
    return app

@pytest.fixture(scope='function')
def client(app):
    """
    テスト関数ごとに独立したHTTPクライアントを返すフィクスcha。
    """
    return app.test_client()

@pytest.fixture(scope='function')
def runner(app):
    """
    テスト関数ごとに独立したCLIコマンドランナーを返すフィクスチャ。
    """
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def init_database(app):
    """
    各テスト関数の実行前にデータベースを初期化し、
    テストユーザーと会社、そして株主を1名作成するフィクスチャ。
    テスト終了後にはデータベースをクリーンアップする。
    """
    with app.app_context():
        db.create_all()

        # テスト用のユーザーを作成
        user1 = User(username='testuser1', email='test1@example.com')
        user1.set_password('password')
        user2 = User(username='testuser2', email='test2@example.com')
        user2.set_password('password')
        db.session.add_all([user1, user2])
        db.session.commit()

        # テスト用の会社を作成
        company1 = Company(
            user_id=user1.id,
            corporate_number='1234567890123',
            company_name='株式会社テスト1',
            company_name_kana='カブシキガイシャテストイチ',
            zip_code='1000001',
            prefecture='東京都',
            city='千代田区',
            address='テスト1-1-1',
            phone_number='0312345678',
            establishment_date=date(2023, 1, 1)
        )
        db.session.add(company1)
        db.session.commit()

        # ユーザーBの会社も作成
        company2 = Company(
            user_id=user2.id,
            corporate_number='9876543210987',
            company_name='株式会社テストB',
            company_name_kana='カブシキガイシャテストビー',
            zip_code='1000002',
            prefecture='東京都',
            city='中央区',
            address='テスト2-2-2',
            phone_number='0398765432',
            establishment_date=date(2024, 1, 1)
        )
        db.session.add(company2)
        db.session.commit()

        # テスト用の株主を作成
        shareholder1 = Shareholder(
            company_id=company1.id,
            last_name='初期株主'
        )
        db.session.add(shareholder1)
        db.session.commit()


        yield db

        db.session.remove()
        db.drop_all()
