# tests/test_tenancy.py
from flask import url_for
from flask_login import login_user, logout_user
from app.company.models import User, Shareholder

# --- 正常系テスト (Happy Path Tests) ---

def test_register_main_shareholder_success(client, init_database):
    """正常系: ログインユーザーが主たる株主を正常に登録できる"""
    app = client.application
    db = init_database

    with app.app_context():
        user_a = db.session.get(User, 1)
        with client.session_transaction():
            login_user(user_a)

        # 登録前の株主は1人
        assert Shareholder.query.count() == 1

        register_url = url_for('company.register_main_shareholder')
        shareholder_data = {
            'last_name': '新規株主B',
            'entity_type': 'individual',
            'shares_held': 100
        }
        response = client.post(register_url, data=shareholder_data, follow_redirects=False)

        # 登録後は確認ページへリダイレクトされる
        assert response.status_code == 302
        assert 'confirm/related' in response.location

        # DBに新しい株主が登録されていることを確認
        assert Shareholder.query.count() == 2
        new_shareholder = Shareholder.query.filter_by(last_name='新規株主B').first()
        assert new_shareholder is not None
        assert new_shareholder.company_id == user_a.company.id

        logout_user()

def test_edit_shareholder_success(client, init_database):
    """正常系: ログインユーザーが自身の株主情報を正常に編集できる"""
    app = client.application
    db = init_database

    with app.app_context():
        user_a = db.session.get(User, 1)
        shareholder_to_edit = Shareholder.query.filter_by(company_id=user_a.company.id).first()
        shareholder_id = shareholder_to_edit.id

        with client.session_transaction():
            login_user(user_a)

        edit_url = url_for('company.edit_shareholder', shareholder_id=shareholder_id)
        edited_data = {
            'last_name': '編集後株主',
            'entity_type': 'individual',
            'shares_held': 500
        }
        response = client.post(edit_url, data=edited_data, follow_redirects=True)

        assert response.status_code == 200
        assert '株主情報を更新しました' in response.data.decode('utf-8')

        edited_shareholder = db.session.get(Shareholder, shareholder_id)
        assert edited_shareholder.last_name == '編集後株主'
        assert edited_shareholder.shares_held == 500

        logout_user()

def test_delete_shareholder_success(client, init_database):
    """正常系: ログインユーザーが自身の株主情報を正常に削除できる"""
    app = client.application
    db = init_database

    with app.app_context():
        user_a = db.session.get(User, 1)
        shareholder_to_delete = Shareholder.query.filter_by(company_id=user_a.company.id).first()
        shareholder_id = shareholder_to_delete.id

        assert db.session.get(Shareholder, shareholder_id) is not None

        with client.session_transaction():
            login_user(user_a)

        delete_url = url_for('company.delete_shareholder', shareholder_id=shareholder_id)
        response = client.post(delete_url, follow_redirects=True)

        assert response.status_code == 200
        assert '株主情報を削除しました' in response.data.decode('utf-8')

        assert db.session.get(Shareholder, shareholder_id) is None

        logout_user()

def test_register_more_than_three_main_shareholders(client, init_database):
    """正常系: 4人以上の主たる株主が正常に登録できることを確認する"""
    app = client.application
    db = init_database

    with app.app_context():
        user_a = db.session.get(User, 1)
        with client.session_transaction():
            login_user(user_a)

        register_url = url_for('company.register_main_shareholder')

        for i in range(4):
            shareholder_data = { 'last_name': f'追加株主{i+1}', 'entity_type': 'individual', 'shares_held': 100 + i }
            response = client.post(register_url, data=shareholder_data, follow_redirects=False)
            assert response.status_code == 302

        main_shareholders_count = Shareholder.query.filter(
            Shareholder.company_id == user_a.company.id,
            Shareholder.parent_id.is_(None)
        ).count()
        assert main_shareholders_count == 5

        logout_user()

# --- 異常系テスト ---

def test_shareholder_list_tenancy(client, init_database):
    """異常系: ユーザーBはユーザーAの株主情報が見えない"""
    app = client.application
    db = init_database

    with app.app_context():
        user_b = db.session.get(User, 2)
        with client.session_transaction():
            login_user(user_b)

        response = client.get(url_for('company.shareholders'))
        assert response.status_code == 200
        assert '初期株主' not in response.data.decode('utf-8')

        logout_user()

def test_edit_shareholder_tenancy_fails(client, init_database):
    """異常系: ユーザーBはユーザーAの株主情報を編集できない"""
    app = client.application
    db = init_database

    with app.app_context():
        user_a = db.session.get(User, 1)
        user_b = db.session.get(User, 2)
        shareholder_a = Shareholder.query.filter_by(company_id=user_a.company.id).first()
        shareholder_a_id = shareholder_a.id

        with client.session_transaction():
            login_user(user_b)

        edit_url = url_for('company.edit_shareholder', shareholder_id=shareholder_a_id)
        response_get = client.get(edit_url)
        assert response_get.status_code == 404

        response_post = client.post(edit_url, data={'last_name': '不正'})
        assert response_post.status_code == 404

        logout_user()

def test_delete_shareholder_tenancy_fails(client, init_database):
    """異常系: ユーザーBはユーザーAの株主情報を削除できない"""
    app = client.application
    db = init_database

    with app.app_context():
        user_a = db.session.get(User, 1)
        user_b = db.session.get(User, 2)
        shareholder_a = Shareholder.query.filter_by(company_id=user_a.company.id).first()
        shareholder_a_id = shareholder_a.id

        with client.session_transaction():
            login_user(user_b)

        delete_url = url_for('company.delete_shareholder', shareholder_id=shareholder_a_id)
        response = client.post(delete_url)
        assert response.status_code == 404

        assert db.session.get(Shareholder, shareholder_a_id) is not None

        logout_user()