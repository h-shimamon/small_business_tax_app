
from flask import (
    Blueprint,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    current_app,
)
from flask_login import login_user, logout_user

from app.company.models import User

from .forms import (
    LoginForm,
    ResetConfirmForm,
    ResetRequestForm,
    SignupEmailForm,
    SignupForm,
)
from .rate_limit import (
    too_many_attempts,
    too_many_reset_requests,
    too_many_signup_requests,
)

newauth_bp = Blueprint("newauth", __name__)


@newauth_bp.record_once
def _log_newauth_mode(state) -> None:
    try:
        mode = _signup_mode_from_config(state.app.config)
        state.app.logger.info("NewAuth signup mode=%s", mode)
    except Exception:
        state.app.logger.debug("Failed to resolve NewAuth signup mode", exc_info=True)


@newauth_bp.get("/healthz")
def healthz() -> Response:
    mode = _signup_mode_from_config(current_app.config)
    payload = {"status": "ok", "signup_mode": mode}
    return jsonify(payload)



def _signup_mode_from_config(config) -> str:
    try:
        flag = str(config.get("ENABLE_SIGNUP_EMAIL_FIRST", "")).lower()
        return "email-first" if flag in ("1", "true", "yes", "on") else "legacy"
    except Exception:
        return "legacy"


def _email_first_mode() -> bool:
    try:
        from flask import current_app as _app
        return _signup_mode_from_config(_app.config) == "email-first"
    except Exception:
        return False


def _prepare_email_first_user(db, email: str) -> tuple[User, bool]:
    from secrets import token_urlsafe

    user = User.query.filter_by(email=email).first()
    if user is None:
        username = email.split("@")[0]
        user = User(username=username, email=email)
        user.set_password(token_urlsafe(12))
        db.session.add(user)
        db.session.commit()
        return user, True
    already_verified = bool(getattr(user, "is_email_verified", False))
    return user, not already_verified


def _create_signup_token(db, user_id: int):
    from .tokens import new_signup_token

    token, token_hash, expires_at = new_signup_token()
    db.session.execute(
        db.text("INSERT INTO signup_tokens (user_id, token_hash, expires_at) VALUES (:uid, :th, :exp)"),
        {"uid": user_id, "th": token_hash, "exp": expires_at},
    )
    db.session.commit()
    return token


def _send_signup_email(email: str, token: str, template_prefix: str) -> None:
    from .email_sender import get_sender

    base = request.url_root.rstrip("/")
    verify_url = base + url_for("newauth.verify", token=token)
    sender = get_sender()
    subject = render_template(f"newauth/emails/{template_prefix}_subject.txt")
    text = render_template(f"newauth/emails/{template_prefix}_body.txt", verify_url=verify_url)
    html = render_template(f"newauth/emails/{template_prefix}_body.html", verify_url=verify_url)
    sender.send(to=email, subject=subject.strip(), html=html, text=text)


def _fetch_signup_token(db, token_hash: str):
    return db.session.execute(
        db.text("SELECT id, user_id, expires_at, used_at FROM signup_tokens WHERE token_hash = :th"),
        {"th": token_hash},
    ).mappings().first()


def _parse_dt(value):
    from datetime import datetime, timezone

    if value is None:
        return None
    if isinstance(value, datetime):
        dt_value = value
    else:
        try:
            dt_value = datetime.fromisoformat(str(value))
        except Exception:
            return None
    if dt_value.tzinfo is None:
        dt_value = dt_value.replace(tzinfo=timezone.utc)
    return dt_value


def _token_expired(token_row, now):
    expires = _parse_dt(token_row.get("expires_at"))
    if expires and expires < now:
        return True
    used = _parse_dt(token_row.get("used_at"))
    return used is not None


def _complete_signup(db, token_row, now):
    db.session.execute(
        db.text("UPDATE signup_tokens SET used_at = :now WHERE id = :id"),
        {"now": now, "id": token_row["id"]},
    )
    db.session.execute(
        db.text("UPDATE user SET is_email_verified = 1 WHERE id = :uid"),
        {"uid": token_row["user_id"]},
    )
    db.session.commit()


def _render_invalid_signup_link():
    flash("無効なリンクです。", "danger")
    return redirect(url_for("newauth.login_page"))


def _email_first_verify_flow(db, token_row, token, now):
    form = ResetConfirmForm()
    if request.method == "POST" and form.validate_on_submit():
        user = db.session.get(User, token_row["user_id"])
        if not user:
            return _render_invalid_signup_link()
        user.set_password(form.password.data)
        _complete_signup(db, token_row, now)
        flash("パスワードを設定しました。ログインできます。", "success")
        return redirect(url_for("newauth.login_page"))
    return render_template(
        "newauth/reset_confirm.html",
        form=form,
        token=token,
        title="パスワードを設定",
        submit_label="パスワードを設定",
    )



def _handle_email_first_signup(form: SignupEmailForm):
    if request.method != "POST" or not form.validate_on_submit():
        return None
    email = (form.email.data or "").strip().lower()
    if too_many_signup_requests(request, email):
        return render_template("newauth/signup_sent.html"), 200

    from app.extensions import db

    user, should_send = _prepare_email_first_user(db, email)
    if should_send:
        token = _create_signup_token(db, user.id)
        try:
            _send_signup_email(email, token, "verify_signup")
        except Exception:
            pass
    return render_template("newauth/signup_sent.html"), 200


def _handle_legacy_signup(form: SignupForm):
    if request.method != "POST" or not form.validate_on_submit():
        return None
    email = (form.email.data or "").strip().lower()
    if too_many_signup_requests(request, email):
        flash("しばらく待ってからお試しください。", "danger")
        return render_template("newauth/signup.html", form=form), 429

    from app.extensions import db

    if User.query.filter_by(email=email).first():
        flash("このメールアドレスは既に登録されています。", "danger")
        return render_template("newauth/signup.html", form=form), 400

    user = User(username=email.split("@")[0], email=email)
    user.set_password(form.password.data)
    db.session.add(user)
    db.session.commit()

    token = _create_signup_token(db, user.id)
    try:
        _send_signup_email(email, token, "verify")
    except Exception:
        pass
    return render_template("newauth/signup_sent.html"), 200

@newauth_bp.route("/signup", methods=["GET", "POST"])  # type: ignore[misc]

def signup_page():
    """Signup entry supporting both email-first and legacy flows."""
    if _email_first_mode():
        form = SignupEmailForm()
        response = _handle_email_first_signup(form)
        if response is not None:
            return response
        return render_template("newauth/signup.html", form=form)

    form = SignupForm()
    response = _handle_legacy_signup(form)
    if response is not None:
        return response
    return render_template("newauth/signup.html", form=form)


@newauth_bp.route("/verify", methods=["GET", "POST"])  # type: ignore[misc]

def verify():
    import hashlib
    from datetime import datetime, timezone

    from app.extensions import db

    token = request.args.get("token", "").strip()
    if not token:
        return _render_invalid_signup_link()

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    token_row = _fetch_signup_token(db, token_hash)
    if not token_row:
        return _render_invalid_signup_link()

    now = datetime.now(timezone.utc)
    if _token_expired(token_row, now):
        flash("リンクが無効か期限切れです。", "danger")
        return redirect(url_for("newauth.login_page"))

    if _email_first_mode():
        response = _email_first_verify_flow(db, token_row, token, now)
        if response is not None:
            return response

    _complete_signup(db, token_row, now)
    flash("メール認証が完了しました。ログインできます。", "success")
    return redirect(url_for("newauth.login_page", verified=1))


@newauth_bp.route("/login", methods=["GET", "POST"])  # type: ignore[misc]
def login_page():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        if too_many_attempts(request, form.email.data or ""):
            flash("ログインに失敗しました。しばらく待ってからお試しください。", "danger")
            return render_template("newauth/login.html", form=form), 429
        email = (form.email.data or "").strip().lower()
        user: User | None = User.query.filter_by(email=email).first()
        ok = bool(user and user.check_password(form.password.data))
        if ok and not getattr(user, "is_email_verified", False):
            flash("メール認証が必要です。受信メールのリンクを確認してください。", "info")
            return render_template("newauth/login.html", form=form), 200
        if ok:
            login_user(user, remember=bool(form.remember.data))
            flash("ログインしました。", "success")
            nxt = request.args.get("next")
            if nxt and nxt.startswith("/"):
                return redirect(nxt)
            return redirect(url_for("newauth.login_page"))
        flash("メールアドレスまたはパスワードが違います。", "danger")
    return render_template("newauth/login.html", form=form)


@newauth_bp.post("/logout")
def logout_action():
    try:
        logout_user()
    except Exception:
        pass
    flash("ログアウトしました。", "info")
    return redirect(url_for("newauth.login_page"))




def _fetch_reset_token(db, token_hash: str):
    return db.session.execute(
        db.text("SELECT id, user_id, expires_at, used_at FROM reset_tokens WHERE token_hash = :th"),
        {"th": token_hash},
    ).mappings().first()


def _render_invalid_reset_link():
    flash("無効なリンクです。", "danger")
    return redirect(url_for("newauth.reset_request"))


def _complete_reset(db, token_row, now):
    db.session.execute(
        db.text("UPDATE reset_tokens SET used_at = :now WHERE id = :id"),
        {"now": now, "id": token_row["id"]},
    )
    db.session.commit()

@newauth_bp.route("/reset", methods=["GET", "POST"])  # type: ignore[misc]
def reset_request():
    form = ResetRequestForm()
    if request.method == "POST" and form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        if too_many_reset_requests(request, email):
            return render_template("newauth/reset_sent.html"), 200
        from app.company.models import User
        from app.extensions import db

        from .email_sender import get_sender
        from .tokens import new_reset_token
        user = User.query.filter_by(email=email).first()
        if user is not None:
            token, token_hash, expires_at = new_reset_token()
            db.session.execute(
                db.text("INSERT INTO reset_tokens (user_id, token_hash, expires_at) VALUES (:uid, :th, :exp)"),
                {"uid": user.id, "th": token_hash, "exp": expires_at},
            )
            db.session.commit()
            try:
                base = request.url_root.rstrip("/")
                confirm_url = base + url_for("newauth.reset_confirm", token=token)
                sender = get_sender()
                subject = render_template("newauth/emails/reset_subject.txt")
                text = render_template("newauth/emails/reset_body.txt", confirm_url=confirm_url)
                html = render_template("newauth/emails/reset_body.html", confirm_url=confirm_url)
                sender.send(to=email, subject=subject.strip(), html=html, text=text)
            except Exception:
                pass
        return render_template("newauth/reset_sent.html"), 200
    return render_template("newauth/reset.html", form=form)


@newauth_bp.route("/reset/confirm", methods=["GET", "POST"])  # type: ignore[misc]

def reset_confirm():
    import hashlib
    from datetime import datetime, timezone

    from app.extensions import db

    token = (request.args.get("token") or request.form.get("token") or "").strip()
    if not token:
        return _render_invalid_reset_link()

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    token_row = _fetch_reset_token(db, token_hash)
    if not token_row:
        return _render_invalid_reset_link()

    now = datetime.now(timezone.utc)
    if _token_expired(token_row, now):
        flash("リンクが無効か期限切れです。", "danger")
        return redirect(url_for("newauth.reset_request"))

    form = ResetConfirmForm()
    if request.method == "POST" and form.validate_on_submit():
        user = db.session.get(User, token_row["user_id"])
        if not user:
            return _render_invalid_reset_link()
        user.set_password(form.password.data)
        _complete_reset(db, token_row, now)
        flash("パスワードを更新しました。ログインできます。", "success")
        return redirect(url_for("newauth.login_page"))

    return render_template("newauth/reset_confirm.html", form=form, token=token)
