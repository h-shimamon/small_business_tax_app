# tests/conftest.py
import pytest
from datetime import date
from app import create_app, db
from app.company.models import User, Company

@pytest.fixture(scope='module')
def app():
    """
    テスト用のFlaskアプリケーションインスタンスを作成するフィクスチャ。
    データベースはインメモリのSQLiteを使用する。
    """
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,  # テストではCSRF保護を無効化
            'SECRET_KEY': 'test-secret-key',  # テスト用セッションのためのキー
        
    })
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='module')
def client(app):
    """
    テストクライアントを作成するフィクスチャ。
    """
    return app.test_client()

@pytest.fixture(scope='function')
def runner(app):
    """
    CLIコマンドをテストするためのランナーを作成するフィクスチャ。
    """
    return app.test_cli_runner()

@pytest.fixture(scope='function')
def init_database(app):
    """
    各テストの前後にデータベースをクリーンアップし、
    テスト用の基本データを作成するフィクスチャ。
    """
    with app.app_context():
        # 既存のデータを全て削除
        db.drop_all()
        db.create_all()

        # テスト用ユーザーを作成
        user1 = User(username='testuser1')
        user1.set_password('password')
        user2 = User(username='testuser2')
        user2.set_password('password')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        # ユーザー1の会社を作成
        company1 = Company(
            corporate_number="1111111111111",
            company_name="株式会社テスト１",
            company_name_kana="テストイチ",
            zip_code="1000001",
            prefecture="東京都",
            city="千代田区",
            address="丸の内1-1-1",
            phone_number="03-1111-1111",
            establishment_date=date(2020, 1, 1),
            user_id=user1.id
        )
        db.session.add(company1)
        db.session.commit()

        yield db

        # テスト終了後に再度クリーンアップ
        db.drop_all()
