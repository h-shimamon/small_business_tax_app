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


## CSP (scripts)
- Inline初期化を撤去済みのため、unsafe-inlineは不要です。
- 推奨例: `Content-Security-Policy: script-src 'self' https://cdn.jsdelivr.net; object-src 'none'; base-uri 'self';`

## Documentation
- SoAフォーム設定の詳細は `docs/soa_form_fields.md` を参照してください。
- ドメイン逆引き辞書: `docs/domain_dictionary.md`。

## 開発ガイドライン
- 新しいモデル/テーブルは `app/company/models`（または同配下の `model_parts`）に配置してから `app/company/models/__init__.py` で公開する。
- モデルを別ディレクトリに追加する場合は、Alembic マイグレーションが正しく検出されるよう import 経路を整備すること。
- 必要に応じて `ruff check --select I,UP,B,C90` で型アノテーションやimportの診断を行い、段階的に改善する。
