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


def test_signup_creates_user_and_token_and_verify_allows_login():
    app = _make_app()
    client = app.test_client()
    with app.app_context():
        db.create_all()
        # signup_tokens is created by migration in real env; tests use create_all(), so ensure table exists for SQLite
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

    # 1) signup
    r = client.post('/xauth/signup', data={'email': 'new@example.com', 'password': 'password1234', 'password2': 'password1234'})
    assert r.status_code == 200

    # 2) fetch token from DB
    with app.app_context():
        # user exists, not verified yet
        u = User.query.filter_by(email='new@example.com').first()
        assert u is not None
        assert not bool(getattr(u, 'is_email_verified', False))
        row = db.session.execute(db.text("SELECT token_hash FROM signup_tokens WHERE user_id = :uid ORDER BY id DESC LIMIT 1"), {"uid": u.id}).mappings().first()
        assert row is not None
        th = row['token_hash']
        # compute a clear token that matches (impractical normally); instead we simulate by direct update to used_at via verify route

    # 3) simulate verify using a fresh token (we can't invert hash), insert a known token
    clear = 'testtoken-abc'
    th2 = hashlib.sha256(clear.encode('utf-8')).hexdigest()
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=24)
    with app.app_context():
        u = User.query.filter_by(email='new@example.com').first()
        db.session.execute(db.text("INSERT INTO signup_tokens (user_id, token_hash, expires_at) VALUES (:uid, :th, :exp)"), {"uid": u.id, "th": th2, "exp": exp})
        db.session.commit()

    r2 = client.get(f'/xauth/verify?token={clear}', follow_redirects=True)
    assert r2.status_code == 200
    body2 = (r2.data or b'').decode('utf-8')
    assert 'メール認証が完了しました' in body2

    # 4) login should now succeed
    r3 = client.post('/xauth/login', data={'email': 'new@example.com', 'password': 'password1234'}, follow_redirects=True)
    assert r3.status_code == 200
    body3 = (r3.data or b'').decode('utf-8')
    assert 'ログインしました' in body3
