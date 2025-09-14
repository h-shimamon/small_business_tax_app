# small_business_tax_app

A Flask-based small business tax app.

## New Auth (experimental, flagged)

The new user management module is isolated under `/xauth/*` and disabled by default. It does not affect existing features unless explicitly enabled.

- Enable:
  - `export ENABLE_NEW_AUTH=1`
  - `export FLASK_APP=app:create_app`
  - `flask run -h 127.0.0.1 -p 5002`
- Routes (flag ON):
  - `GET  /xauth/healthz` (200 OK)
  - `GET/POST /xauth/login`, `POST /xauth/logout`
  - `GET/POST /xauth/signup` (see modes below)
  - `GET/POST /xauth/reset`, `GET/POST /xauth/reset/confirm?token=...`
- Modes for signup:
  - Default (off): email + password, then email verification → login
  - Email-first (recommended): enable `export ENABLE_SIGNUP_EMAIL_FIRST=1`
    - User submits email only → receives verify link → sets password on verify page → login

- DB:
  - `FLASK_APP=app:create_app flask db upgrade`
  - Adds: `signup_tokens`, `reset_tokens`, and `user.is_email_verified`
- Tests:
  - `PYTHONPATH=. pytest -q tests/test_newauth_*`

See `docs/newauth_guide.md` for details (dev notes, token testing, and safety).

$1

## CSP (scripts)
- Inline初期化を撤去済みのため、unsafe-inlineは不要です。
- 推奨例: `Content-Security-Policy: script-src 'self' https://cdn.jsdelivr.net; object-src 'none'; base-uri 'self';`