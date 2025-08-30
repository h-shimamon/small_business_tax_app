import pytest
from app import create_app, db
from app.company.models import User


def _make_app():
    cfg = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'ENABLE_NEW_AUTH': True,
    }
    return create_app(cfg)


def _create_user(email="user@example.com", password="password1234"):
    u = User(username='u1', email=email)
    u.set_password(password)
    # 新認証フラグを考慮
    try:
        setattr(u, 'is_email_verified', True)
    except Exception:
        pass
    db.session.add(u)
    db.session.commit()
    return u


def test_login_success_and_logout():
    app = _make_app()
    with app.app_context():
        db.create_all()
        _create_user()
    client = app.test_client()

    # GET login
    r = client.get('/xauth/login')
    assert r.status_code == 200

    # POST login (success)
    r2 = client.post('/xauth/login', data={'email': 'user@example.com', 'password': 'password1234'}, follow_redirects=True)
    assert r2.status_code == 200
    body = (r2.data or b'').decode('utf-8')
    assert 'ログインしました' in body

    # POST logout
    r3 = client.post('/xauth/logout', follow_redirects=True)
    assert r3.status_code == 200
    body3 = (r3.data or b'').decode('utf-8')
    assert 'ログアウトしました' in body3


def test_login_invalid_credentials_shows_error():
    app = _make_app()
    with app.app_context():
        db.create_all()
        _create_user()
    client = app.test_client()

    r = client.post('/xauth/login', data={'email': 'user@example.com', 'password': 'wrongpass'}, follow_redirects=True)
    assert r.status_code in (200, 429)
    body = (r.data or b'').decode('utf-8')
    assert 'メールアドレスまたはパスワードが違います' in body or 'ログインに失敗しました' in body
