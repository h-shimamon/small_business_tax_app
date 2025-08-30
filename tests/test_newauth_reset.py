from datetime import datetime, timedelta, timezone
import hashlib

from app import create_app, db
from app.company.models import User


def _make_app():
    cfg = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'ENABLE_NEW_AUTH': True,
        'SERVER_NAME': 'localhost',
        'PREFERRED_URL_SCHEME': 'http',
    }
    return create_app(cfg)


def _ensure_tables():
    # For tests using create_all(), ensure reset_tokens exists (migration in real env)
    from sqlalchemy import text as _text
    db.session.execute(_text("""
    CREATE TABLE IF NOT EXISTS reset_tokens (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        token_hash VARCHAR(128) NOT NULL,
        expires_at DATETIME NOT NULL,
        used_at DATETIME NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        FOREIGN KEY(user_id) REFERENCES user (id) ON DELETE CASCADE
    )
    """))
    db.session.execute(_text("CREATE UNIQUE INDEX IF NOT EXISTS ux_reset_tokens_token_hash ON reset_tokens (token_hash)"))
    db.session.execute(_text("CREATE INDEX IF NOT EXISTS ix_reset_tokens_user_id ON reset_tokens (user_id)"))
    db.session.commit()


def test_reset_happy_path_and_login_with_new_password():
    app = _make_app()
    client = app.test_client()
    with app.app_context():
        db.create_all()
        _ensure_tables()
        u = User(username='demo', email='reset@example.com'); u.set_password('oldpassword'); u.is_email_verified=True
        db.session.add(u); db.session.commit()

    # Request reset (response is always success page)
    r = client.post('/xauth/reset', data={'email': 'reset@example.com'})
    assert r.status_code == 200

    # Insert known token for confirm
    clear = 'reset-clear-token'
    th = hashlib.sha256(clear.encode('utf-8')).hexdigest()
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=2)
    with app.app_context():
        u = User.query.filter_by(email='reset@example.com').first()
        db.session.execute(db.text("INSERT INTO reset_tokens (user_id, token_hash, expires_at) VALUES (:uid,:th,:exp)"), {"uid": u.id, "th": th, "exp": exp})
        db.session.commit()

    # GET form
    r2 = client.get(f'/xauth/reset/confirm?token={clear}')
    assert r2.status_code == 200
    # POST new password
    r3 = client.post(f'/xauth/reset/confirm?token={clear}', data={'password': 'newpassword123', 'password2': 'newpassword123'}, follow_redirects=True)
    assert r3.status_code == 200
    body = (r3.data or b'').decode('utf-8')
    assert 'パスワードを更新しました' in body

    # Login works with new password, fails with old
    ok = client.post('/xauth/login', data={'email': 'reset@example.com', 'password': 'newpassword123'}, follow_redirects=True)
    assert ok.status_code == 200
    bad = client.post('/xauth/login', data={'email': 'reset@example.com', 'password': 'oldpassword'}, follow_redirects=True)
    assert bad.status_code in (200, 429)
    assert 'メールアドレスまたはパスワードが違います' in (bad.data or b'').decode('utf-8') or 'ログインに失敗しました' in (bad.data or b'').decode('utf-8')


def test_reset_invalid_token_redirects_to_request():
    app = _make_app()
    client = app.test_client()
    with app.app_context():
        db.create_all()
        _ensure_tables()
    r = client.get('/xauth/reset/confirm?token=invalid', follow_redirects=True)
    assert r.status_code == 200
    assert '無効' in (r.data or b'').decode('utf-8') or '再設定' in (r.data or b'').decode('utf-8')
