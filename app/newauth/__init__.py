from flask import Blueprint, render_template, Response, request, redirect, url_for, flash
import secrets

from flask_login import login_user, logout_user

from app.company.models import User
from .forms import (
    LoginForm,
    SignupForm,
    ResetRequestForm,
    ResetConfirmForm,
    SignupEmailForm,
)
from .rate_limit import (
    too_many_attempts,
    too_many_reset_requests,
    too_many_signup_requests,
)

newauth_bp = Blueprint("newauth", __name__)


@newauth_bp.get("/healthz")
def healthz() -> Response:
    return Response("OK", mimetype="text/plain")


@newauth_bp.route("/signup", methods=["GET", "POST"])  # type: ignore[misc]
def signup_page():
    """Signup entry.
    - Email-first mode (flag ENABLE_SIGNUP_EMAIL_FIRST): email only -> send token -> signup_sent
    - Legacy mode: email+password -> send token -> signup_sent
    """
    # Flag: email-first mode
    form_email_first = False
    try:
        from flask import current_app as _app
        flag = str(_app.config.get("ENABLE_SIGNUP_EMAIL_FIRST")).lower()
        form_email_first = flag in ("1", "true", "yes", "on")
    except Exception:
        pass

    if form_email_first:
        form = SignupEmailForm()
        if request.method == "POST" and form.validate_on_submit():
            email = (form.email.data or "").strip().lower()
            # rate limit
            if too_many_signup_requests(request, email):
                return render_template("newauth/signup_sent.html"), 200

            from app import db
            from .tokens import new_signup_token
            from .email_sender import get_sender

            user = User.query.filter_by(email=email).first()
            send_mail = True
            if user is None:
                # create unverified user with temporary password
                user = User(username=email.split("@")[0], email=email)
                user.set_password(secrets.token_urlsafe(12))
                db.session.add(user)
                db.session.commit()
            else:
                # existing user: avoid enumeration; if already verified, suppress email
                try:
                    if bool(getattr(user, "is_email_verified", False)):
                        send_mail = False
                except Exception:
                    pass

            if send_mail:
                token, token_hash, expires_at = new_signup_token()
                db.session.execute(
                    db.text(
                        "INSERT INTO signup_tokens (user_id, token_hash, expires_at) VALUES (:uid, :th, :exp)"
                    ),
                    {"uid": user.id, "th": token_hash, "exp": expires_at},
                )
                db.session.commit()
                try:
                    base = request.url_root.rstrip("/")
                    verify_url = base + url_for("newauth.verify", token=token)
                    sender = get_sender()
                    subject = render_template("newauth/emails/verify_subject_signup.txt")
                    text = render_template("newauth/emails/verify_body_signup.txt", verify_url=verify_url)
                    html = render_template("newauth/emails/verify_body_signup.html", verify_url=verify_url)
                    sender.send(to=email, subject=subject.strip(), html=html, text=text)
                except Exception:
                    pass
            return render_template("newauth/signup_sent.html"), 200
        return render_template("newauth/signup.html", form=form)

    # Legacy (email + password)
    form = SignupForm()
    if request.method == "POST" and form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        if too_many_signup_requests(request, email):
            flash("しばらく待ってからお試しください。", "danger")
            return render_template("newauth/signup.html", form=form), 429
        from app import db
        from .tokens import new_signup_token
        from .email_sender import get_sender
        if User.query.filter_by(email=email).first():
            flash("このメールアドレスは既に登録されています。", "danger")
            return render_template("newauth/signup.html", form=form), 400
        user = User(username=email.split("@")[0], email=email)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        token, token_hash, expires_at = new_signup_token()
        db.session.execute(
            db.text("INSERT INTO signup_tokens (user_id, token_hash, expires_at) VALUES (:uid, :th, :exp)"),
            {"uid": user.id, "th": token_hash, "exp": expires_at},
        )
        db.session.commit()
        try:
            base = request.url_root.rstrip("/")
            verify_url = base + url_for("newauth.verify", token=token)
            sender = get_sender()
            subject = render_template("newauth/emails/verify_subject.txt")
            text = render_template("newauth/emails/verify_body.txt", verify_url=verify_url)
            html = render_template("newauth/emails/verify_body.html", verify_url=verify_url)
            sender.send(to=email, subject=subject.strip(), html=html, text=text)
        except Exception:
            pass
        return render_template("newauth/signup_sent.html"), 200
    return render_template("newauth/signup.html", form=form)


@newauth_bp.route("/verify", methods=["GET", "POST"])  # type: ignore[misc]
def verify():
    from app import db
    import hashlib
    from datetime import datetime, timezone

    def _to_dt(v):
        if v is None:
            return None
        if isinstance(v, datetime):
            d = v
        else:
            try:
                d = datetime.fromisoformat(str(v))
            except Exception:
                return None
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d

    token = request.args.get("token", "").strip()
    if not token:
        flash("無効なリンクです。", "danger")
        return redirect(url_for("newauth.login_page"))
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    row = db.session.execute(
        db.text("SELECT id, user_id, expires_at, used_at FROM signup_tokens WHERE token_hash = :th"),
        {"th": token_hash},
    ).mappings().first()
    if not row:
        flash("リンクが無効か期限切れです。", "danger")
        return redirect(url_for("newauth.login_page"))

    exp_dt = _to_dt(row["expires_at"])  # type: ignore[index]
    used_dt = _to_dt(row["used_at"])    # type: ignore[index]
    now = datetime.now(timezone.utc)
    if used_dt is not None or (exp_dt and exp_dt < now):
        flash("リンクが無効か期限切れです。", "danger")
        return redirect(url_for("newauth.login_page"))

    # Flag: email-first mode
    email_first = False
    try:
        from flask import current_app as _app
        flag = str(_app.config.get("ENABLE_SIGNUP_EMAIL_FIRST")).lower()
        email_first = flag in ("1", "true", "yes", "on")
    except Exception:
        pass

    if email_first:
        form = ResetConfirmForm()
        if request.method == "POST" and form.validate_on_submit():
            from app.company.models import User
            user = db.session.get(User, row["user_id"])  # type: ignore[index]
            if not user:
                flash("リンクが無効か期限切れです。", "danger")
                return redirect(url_for("newauth.login_page"))
            user.set_password(form.password.data)
            db.session.execute(db.text("UPDATE signup_tokens SET used_at = :now WHERE id = :id"), {"now": now, "id": row["id"]})
            db.session.execute(db.text("UPDATE user SET is_email_verified = 1 WHERE id = :uid"), {"uid": row["user_id"]})
            db.session.commit()
            flash("パスワードを設定しました。ログインできます。", "success")
            return redirect(url_for("newauth.login_page"))
        return render_template(
            "newauth/reset_confirm.html",
            form=form,
            token=token,
            title="パスワードを設定",
            submit_label="パスワードを設定",
        )

    # Legacy: verify and go to login
    db.session.execute(db.text("UPDATE signup_tokens SET used_at = :now WHERE id = :id"), {"now": now, "id": row["id"]})
    db.session.execute(db.text("UPDATE user SET is_email_verified = 1 WHERE id = :uid"), {"uid": row["user_id"]})
    db.session.commit()
    flash("メール認証が完了しました。ログインできます。", "success")
    return redirect(url_for("newauth.login_page"))


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


@newauth_bp.route("/reset", methods=["GET", "POST"])  # type: ignore[misc]
def reset_request():
    form = ResetRequestForm()
    if request.method == "POST" and form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        if too_many_reset_requests(request, email):
            return render_template("newauth/reset_sent.html"), 200
        from app import db
        from app.company.models import User
        from .tokens import new_reset_token
        from .email_sender import get_sender
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
    from app import db
    import hashlib
    from datetime import datetime, timezone

    def _to_dt(v):
        if v is None:
            return None
        if isinstance(v, datetime):
            d = v
        else:
            try:
                d = datetime.fromisoformat(str(v))
            except Exception:
                return None
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d

    token = (request.args.get("token") or request.form.get("token") or "").strip()
    if not token:
        flash("無効なリンクです。", "danger")
        return redirect(url_for("newauth.reset_request"))
    th = hashlib.sha256(token.encode("utf-8")).hexdigest()
    row = db.session.execute(
        db.text("SELECT id, user_id, expires_at, used_at FROM reset_tokens WHERE token_hash = :th"),
        {"th": th},
    ).mappings().first()
    if not row:
        flash("リンクが無効か期限切れです。", "danger")
        return redirect(url_for("newauth.reset_request"))
    exp_dt = _to_dt(row["expires_at"])  # type: ignore[index]
    used_dt = _to_dt(row["used_at"])    # type: ignore[index]
    now = datetime.now(timezone.utc)
    if used_dt is not None or (exp_dt and exp_dt < now):
        flash("リンクが無効か期限切れです。", "danger")
        return redirect(url_for("newauth.reset_request"))

    form = ResetConfirmForm()
    if request.method == "POST" and form.validate_on_submit():
        from app.company.models import User
        user = db.session.get(User, row["user_id"])  # type: ignore[index]
        if not user:
            flash("リンクが無効か期限切れです。", "danger")
            return redirect(url_for("newauth.reset_request"))
        user.set_password(form.password.data)
        db.session.execute(db.text("UPDATE reset_tokens SET used_at = :now WHERE id = :id"), {"now": now, "id": row["id"]})
        db.session.commit()
        flash("パスワードを更新しました。ログインできます。", "success")
        return redirect(url_for("newauth.login_page"))

    return render_template("newauth/reset_confirm.html", form=form, token=token)
