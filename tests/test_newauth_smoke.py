from app import create_app


def _make_app():
    cfg = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'ENABLE_NEW_AUTH': True,
    }
    return create_app(cfg)


def test_healthz_and_login_routes_exist():
    app = _make_app()
    client = app.test_client()

    r1 = client.get('/xauth/healthz')
    assert r1.status_code == 200
    assert (r1.data or b'').decode('utf-8').strip() == 'OK'

    r2 = client.get('/xauth/login')
    assert r2.status_code == 200
    body = (r2.data or b'').decode('utf-8')
    assert 'ログイン' in body
