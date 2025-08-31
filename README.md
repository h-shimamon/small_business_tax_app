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

## Screenshots (newauth)

Replace the placeholder paths below with actual PNGs under `docs/images/`.

- Login: ![Login](docs/images/newauth_login.png)
- Signup (email + password): ![Signup](docs/images/newauth_signup_legacy.png)
- Signup (email-first): ![Signup Email First](docs/images/newauth_signup_email_first.png)
- Verify → Set Password: ![Verify-Set](docs/images/newauth_verify_set_password.png)
- Reset request: ![Reset Request](docs/images/newauth_reset_request.png)
- Reset confirm: ![Reset Confirm](docs/images/newauth_reset_confirm.png)

Tip: run with `ENABLE_NEW_AUTH=1` (and `ENABLE_SIGNUP_EMAIL_FIRST=1`) on port 5002, then capture each page.


## Keyboard focus (developer memo)
- Initial cursor: use `render_field(..., autofocus=True)` on the first input of a page (no JS needed).
- Tab order: kept by structure (Main → Sidebar → Nav). Do not change DOM order.
- Skip links: provided in base; they appear only when focused (Tab once → Enter to jump).
