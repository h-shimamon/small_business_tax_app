# tests/test_tenancy.py
from flask import url_for, get_flashed_messages
from app.company.models import User, Company
from datetime import date
from app import db

def login(client, username, password):
    """テスト用のログインヘルパー関数"""
    return client.post(url_for('company.login'), data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def test_company_access_unauthorized(client):
    """
    ログインしていない場合、基本情報ページへのアクセスはログインページにリダイレクトされる。
    """
    response = client.get(url_for('company.show'))
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

def test_company_access_authorized(client, app, init_database):
    """
    ログインしているユーザーは、自身の会社情報ページにアクセスできる。
    """
    with app.app_context():
        login(client, 'testuser1', 'password')
        response = client.get(url_for('company.show'), follow_redirects=True)
        
        assert response.status_code == 200
        html_content = response.data.decode('utf-8')
        assert '<h1 class="content-title">基本情報</h1>' in html_content
        assert 'value="株式会社テスト１"' in html_content
        assert '株式会社テスト２' not in html_content

def test_create_new_company_for_new_user(client, app, init_database):
    """
    会社を持っていないユーザーが、新しい会社を作成できる。
    """
    with app.app_context():
        login(client, 'testuser2', 'password')
        user2 = User.query.filter_by(username='testuser2').first()
        
        assert Company.query.filter_by(user_id=user2.id).first() is None

        new_company_data = {
            'corporate_number': '2222222222222',
            'company_name': '株式会社テスト２',
            'company_name_kana': 'テストニ',
            'zip_code': '1000002',
            'prefecture': '東京都',
            'city': '中央区',
            'address': '八重洲2-2-2',
            'phone_number': '03-2222-2222',
            'establishment_date': date(2021, 2, 2),
            'capital_limit': True,
            'is_supported_industry': True,
            'is_not_excluded_business': True,
            'is_excluded_business': False,
        }
        response = client.post(url_for('company.show'), data=new_company_data, follow_redirects=True)
        assert response.status_code == 200
        
        company2 = Company.query.filter_by(user_id=user2.id).first()
        assert company2 is not None
        assert company2.company_name == '株式会社テスト２'

def test_user1_cannot_see_user2_company_on_page(client, app, init_database):
    """
    ユーザー1でログインした際、Webページ上にユーザー2の会社情報が表示されないことを確認する。
    """
    with app.app_context():
        user2 = User.query.filter_by(username='testuser2').first()
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
            is_excluded_business=False,
            user_id=user2.id
        )
        db.session.add(company2)
        db.session.commit()

        login(client, 'testuser1', 'password')
        response = client.get(url_for('company.show'))
        assert response.status_code == 200
        
        html_content = response.data.decode('utf-8')
        assert 'value="株式会社テスト１"' in html_content
        assert '株式会社テスト２' not in html_content

def test_declaration_access_with_no_company(client, app, init_database):
    """
    会社をまだ登録していないユーザーが /declaration にアクセスすると、
    会社登録ページにリダイレクトされることを確認する。
    """
    with app.app_context():
        login(client, 'testuser2', 'password')
        response = client.get(url_for('company.declaration'), follow_redirects=True)
        
        # リダイレクト先のページの内容を確認
        assert response.status_code == 200
        html_content = response.data.decode('utf-8')
        assert '<h1 class="content-title">基本情報</h1>' in html_content # 会社登録ページにいることを確認
        
        # flashメッセージも確認
        assert '最初に会社情報を登録してください。' in html_content

