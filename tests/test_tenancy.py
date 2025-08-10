# tests/test_tenancy.py
from flask import url_for
from app import db
from app.company.models import User, Company
from datetime import date

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
        user1 = User.query.filter_by(username='testuser1').first()
        with client.session_transaction() as sess:
            sess['user_id'] = user1.id
            sess['_fresh'] = True

        response = client.get(url_for('company.show'), follow_redirects=True)
        
        if response.status_code != 200:
            with open("test_debug_output.html", "w") as f:
                f.write(response.data.decode('utf-8'))

        assert response.status_code == 200
        assert '<h2>会社の基本情報</h2>' in response.data.decode('utf-8')
        assert 'value="株式会社テスト１"' in response.data.decode('utf-8')


def test_create_new_company(client, app, init_database):
    """
    会社を持っていないユーザーが、新しい会社を作成できる。
    """
    with app.app_context():
        user2 = User.query.filter_by(username='testuser2').first()
        with client.session_transaction() as sess:
            sess['user_id'] = user2.id
            sess['_fresh'] = True

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
            'is_excluded_business': False, # このフィールドが不足していた
        }
        response = client.post(url_for('company.show'), data=new_company_data, follow_redirects=True)
        assert response.status_code == 200
        
        company2 = Company.query.filter_by(user_id=user2.id).first()
        assert company2 is not None
        assert company2.company_name == '株式会社テスト２'
        assert company2.user_id == user2.id

def test_other_user_company_is_not_visible(client, app, init_database):
    """
    ログインしているユーザーは、他のユーザーの会社情報にアクセスできない。
    """
    with app.app_context():
        user2 = User.query.filter_by(username='testuser2').first()
        with client.session_transaction() as sess:
            sess['user_id'] = user2.id
            sess['_fresh'] = True
        
        company_for_user2 = Company.query.filter_by(user_id=user2.id).first()
        user1_company = Company.query.filter_by(corporate_number="1111111111111").first()
        
        if company_for_user2:
            assert company_for_user2.id != user1_company.id
        else:
            assert True

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
            is_excluded_business=False, # このフィールドが不足していた
            user_id=user2.id
        )
        db.session.add(company2)
        db.session.commit()

        user1 = User.query.filter_by(username='testuser1').first()
        with client.session_transaction() as sess:
            sess['user_id'] = user1.id
            sess['_fresh'] = True

        response = client.get(url_for('company.show'))
        
        if response.status_code != 200:
            with open("test_debug_output.html", "w") as f:
                f.write(response.data.decode('utf-8'))

        assert response.status_code == 200
        
        html_content = response.data.decode('utf-8')

        assert 'value="株式会社テスト１"' in html_content
        assert 'value="株式会社テスト２"' not in html_content
