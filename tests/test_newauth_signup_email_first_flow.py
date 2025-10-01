import hashlib
from datetime import datetime, timedelta, timezone

from app import create_app, db
from app.company.models import User


def _make_app():
    cfg = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'ENABLE_NEW_AUTH': True,
        'ENABLE_SIGNUP_EMAIL_FIRST': True,
        'SERVER_NAME': 'localhost',
        'PREFERRED_URL_SCHEME': 'http',
    }
    return create_app(cfg)


def _ensure_signup_tokens_table():
    from sqlalchemy import text as _text
    db.session.execute(_text("""
    CREATE TABLE IF NOT EXISTS signup_tokens (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        token_hash VARCHAR(128) NOT NULL,
        expires_at DATETIME NOT NULL,
        used_at DATETIME NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        FOREIGN KEY(user_id) REFERENCES user (id) ON DELETE CASCADE
    )
    """))
    db.session.execute(_text("CREATE UNIQUE INDEX IF NOT EXISTS ux_signup_tokens_token_hash ON signup_tokens (token_hash)"))
    db.session.execute(_text("CREATE INDEX IF NOT EXISTS ix_signup_tokens_user_id ON signup_tokens (user_id)"))
    db.session.commit()


def test_signup_email_first_then_verify_and_login():
    app = _make_app()
    client = app.test_client()
    with app.app_context():
        db.create_all()
        _ensure_signup_tokens_table()

    # 1) email-only signup
    r1 = client.post('/xauth/signup', data={'email': 'flow@example.com'})
    assert r1.status_code == 200

    # 2) insert known token for verify
    clear = 'flow-token-xyz'
    th = hashlib.sha256(clear.encode('utf-8')).hexdigest()
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=24)
    with app.app_context():
        u = User.query.filter_by(email='flow@example.com').first()
        assert u is not None
        db.session.execute(db.text("INSERT INTO signup_tokens (user_id, token_hash, expires_at) VALUES (:uid,:th,:exp)"), {"uid": u.id, "th": th, "exp": exp})
        db.session.commit()

    # 3) GET verify should show password setup form
    r2 = client.get(f'/xauth/verify?token={clear}')
    assert r2.status_code == 200
    body2 = (r2.data or b'').decode('utf-8')
    assert 'パスワードを設定' in body2

    # 4) POST new password and login
    r3 = client.post(f'/xauth/verify?token={clear}', data={'password': 'newpw12345', 'password2': 'newpw12345'}, follow_redirects=True)
    assert r3.status_code == 200
    body3 = (r3.data or b'').decode('utf-8')
    assert 'ログインできます' in body3 or 'ログイン' in body3

    r4 = client.post('/xauth/login', data={'email': 'flow@example.com', 'password': 'newpw12345'}, follow_redirects=True)
    assert r4.status_code == 200
    body4 = (r4.data or b'').decode('utf-8')
    assert 'ログインしました' in body4
