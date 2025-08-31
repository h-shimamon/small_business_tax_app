# New Auth Module Guide (experimental)

This document explains how to run and verify the new user management module without affecting existing features.

## Overview
- Isolated under `/xauth/*` and disabled by default
- Feature flag: `ENABLE_NEW_AUTH` (off by default)
- No UI/route changes when the flag is off

## Quick Start (local)
1) Enable and run on a non-conflicting port
```
export ENABLE_NEW_AUTH=1
export FLASK_APP=app:create_app
flask run -h 127.0.0.1 -p 5002
```
2) Health check
- http://127.0.0.1:5002/xauth/healthz → 200 OK

## Signup Modes
- Default (email + password):
  1. Submit email+password on /xauth/signup
  2. Receive verify link → click → account verified
  3. Login on /xauth/login
- Email-first (flag `ENABLE_SIGNUP_EMAIL_FIRST=1`):
  1. Submit email only on /xauth/signup
  2. Receive verify link → click → set password on verify page
  3. Login on /xauth/login

Enable email-first:
```
export ENABLE_SIGNUP_EMAIL_FIRST=1
```

## Testing Tokens in Development
Since email is a dummy sender, create a clear token manually for testing.

1) Create an unverified user via signup (or manually):
```
FLASK_APP=app:create_app flask shell
>>> from app import db
>>> from app.company.models import User
>>> u = User(username='demo', email='demo@example.com'); u.set_password('password1234'); db.session.add(u); db.session.commit()
```
2) Insert a known verification token:
```
>>> import hashlib
>>> from sqlalchemy import text
>>> from datetime import datetime, timedelta, timezone
>>> clear = 'devtoken-verify'
>>> th = hashlib.sha256(clear.encode()).hexdigest()
>>> exp = datetime.now(timezone.utc) + timedelta(hours=24)
>>> db.session.execute(text("INSERT INTO signup_tokens (user_id, token_hash, expires_at) VALUES (:uid,:th,:exp)"), {"uid": u.id, "th": th, "exp": exp}); db.session.commit()
```
3) Open: `http://127.0.0.1:5002/xauth/verify?token=devtoken-verify`

4) For password reset, use `reset_tokens` similarly with TTL 2h and clear token, then `GET /xauth/reset/confirm?token=...`.

## Tests
- Run only newauth tests:
```
PYTHONPATH=. pytest -q tests/test_newauth_smoke.py tests/test_newauth_login.py tests/test_newauth_signup_verify.py tests/test_newauth_reset.py
```
- Run all tests:
```
PYTHONPATH=. pytest -q
```

## Safety and Rollback
- Flag off (default) means zero impact on existing app
- Rollback DB changes (if needed):
```
FLASK_APP=app:create_app flask db downgrade
```
- Keep using port `5002` locally to avoid collision with existing services

## Notes for Production Enablement (future)
- Replace DummyEmailSender with a real provider (API keys via env)
- Move rate limits to a shared store (e.g., Redis)
- Provide UI navigation within newauth (avoid touching existing navigation)
- Consider i18n and wording review before enabling broadly


## UI Screens (placeholders)
Place PNGs under `docs/images/` and they will be rendered in README as well.

- `docs/images/newauth_login.png`
- `docs/images/newauth_signup_legacy.png`
- `docs/images/newauth_signup_email_first.png`
- `docs/images/newauth_verify_set_password.png`
- `docs/images/newauth_reset_request.png`
- `docs/images/newauth_reset_confirm.png`

## Launch Examples
- Local run (port 5002):
```
export ENABLE_NEW_AUTH=1
export FLASK_APP=app:create_app
flask run -h 127.0.0.1 -p 5002
```
- Email-first mode:
```
export ENABLE_SIGNUP_EMAIL_FIRST=1
```
- Health check:
```
curl -sS http://127.0.0.1:5002/xauth/healthz
```
- Basic smoke (login page):
```
curl -sS http://127.0.0.1:5002/xauth/login | head -n 5
```
