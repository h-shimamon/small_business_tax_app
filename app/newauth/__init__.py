from __future__ import annotations

from flask import Blueprint, render_template, Response, request, redirect, url_for, flash

newauth_bp = Blueprint("newauth", __name__)

from flask_login import login_user, logout_user
from app.company.models import User
from .forms import LoginForm, SignupForm, ResetRequestForm, ResetConfirmForm
from .rate_limit import too_many_attempts, too_many_reset_requests


@newauth_bp.get("/healthz")
def healthz() -> Response:
    return Response("OK", mimetype="text/plain")


@newauth_bp.route("/signup", methods=["GET", "POST"]) 
def signup_page():
    form = SignupForm()
    if request.method == "POST" and form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        from app import db
        from .tokens import new_signup_token
        from .email_sender import get_sender
        # 既存メール重複チェック
        from app.company.models import User
        if User.query.filter_by(email=email).first():
            flash("このメールアドレスは既に登録されています。", "danger")
            return render_template("newauth/signup.html", form=form), 400
        # ユーザー作成（未認証）
        user = User(username=email.split("@")[0], email=email)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        # トークン作成
        token, token_hash, expires_at = new_signup_token()
        db.session.execute(
            db.text(
                "INSERT INTO signup_tokens (user_id, token_hash, expires_at) VALUES (:uid, :th, :exp)"
            ),
            {"uid": user.id, "th": token_hash, "exp": expires_at},
        )
        db.session.commit()
        # メール送信
        try:
            base = request.url_root.rstrip("/")
            verify_url = base + url_for("newauth.verify", token=token)
            sender = get_sender()
            subject = render_template("newauth/emails/verify_subject.txt")
            text = render_template("newauth/emails/verify_body.txt", verify_url=verify_url)
            html = render_template("newauth/emails/verify_body.html", verify_url=verify_url)
            sender.send(to=email, subject=subject.strip(), html=html, text=text)
        except Exception:
            # 送信失敗でも画面は同じ（セキュリティ上: 存在漏洩回避）
            pass
        return render_template("newauth/signup_sent.html"), 200
    return render_template("newauth/signup.html", form=form)


@newauth_bp.get("/verify")
def verify():
    from app import db
    import hashlib
    from datetime import datetime, timezone
    token = request.args.get("token", "").strip()
    if not token:
        flash("無効なリンクです。", "danger")
        return redirect(url_for("newauth.login_page"))
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    row = db.session.execute(
        db.text("SELECT id, user_id, expires_at, used_at FROM signup_tokens WHERE token_hash = :th"),
        {"th": token_hash},
    ).mappings().first()
    if not row:
        flash("リンクが無効か期限切れです。", "danger")
        return redirect(url_for("newauth.login_page"))
    # 期限/使用チェック
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
    exp_dt = _to_dt(row["expires_at"]) 
    used_dt = _to_dt(row["used_at"]) 
    now = datetime.now(timezone.utc)
    if used_dt is not None or (exp_dt and exp_dt < now):
        flash("リンクが無効か期限切れです。", "danger")
        return redirect(url_for("newauth.login_page"))
    # マーク使用済み + ユーザーを認証済みに
    db.session.execute(
        db.text("UPDATE signup_tokens SET used_at = :now WHERE id = :id"),
        {"now": now, "id": row["id"]},
    )
    db.session.execute(
        db.text("UPDATE user SET is_email_verified = 1 WHERE id = :uid"),
        {"uid": row["user_id"]},
    )
    db.session.commit()
    flash("メール認証が完了しました。ログインできます。", "success")
    return redirect(url_for("newauth.login_page"))


@newauth_bp.route("/login", methods=["GET", "POST"]) 
def login_page():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        if too_many_attempts(request, form.email.data or ""):
            # 最小限の漏洩防止: メッセージは一般化、429
            flash("ログインに失敗しました。しばらく待ってからお試しください。", "danger")
            return render_template("newauth/login.html", form=form), 429
        email = (form.email.data or "").strip().lower()
        user: User | None = User.query.filter_by(email=email).first()
        ok = bool(user and user.check_password(form.password.data))
        if ok and not getattr(user, 'is_email_verified', False):
            flash("メール認証が必要です。受信メールのリンクを確認してください。", "info")
            return render_template("newauth/login.html", form=form), 200
        if ok:
            login_user(user, remember=bool(form.remember.data))
            flash("ログインしました。", "success")
            nxt = request.args.get("next")
            # nextは相対パスのみ許容（簡易）
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


@newauth_bp.route("/reset", methods=["GET", "POST"]) 
def reset_request():
    form = ResetRequestForm()
    if request.method == "POST" and form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        if too_many_reset_requests(request, email):
            # 常に同じ画面を返す（ユーザー探索防止）。429は付けない。
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


@newauth_bp.route("/reset/confirm", methods=["GET", "POST"]) 
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
    th = hashlib.sha256(token.encode('utf-8')).hexdigest()
    row = db.session.execute(
        db.text("SELECT id, user_id, expires_at, used_at FROM reset_tokens WHERE token_hash = :th"),
        {"th": th},
    ).mappings().first()
    if not row:
        flash("リンクが無効か期限切れです。", "danger")
        return redirect(url_for("newauth.reset_request"))
    exp_dt = _to_dt(row["expires_at"]) 
    used_dt = _to_dt(row["used_at"]) 
    now = datetime.now(timezone.utc)
    if used_dt is not None or (exp_dt and exp_dt < now):
        flash("リンクが無効か期限切れです。", "danger")
        return redirect(url_for("newauth.reset_request"))

    form = ResetConfirmForm()
    if request.method == "POST" and form.validate_on_submit():
        # update password and mark used
        from app.company.models import User
        user = db.session.get(User, row["user_id"]) if hasattr(db.session, 'get') else User.query.get(row["user_id"])  # compat
        if not user:
            flash("リンクが無効か期限切れです。", "danger")
            return redirect(url_for("newauth.reset_request"))
        user.set_password(form.password.data)
        db.session.execute(db.text("UPDATE reset_tokens SET used_at = :now WHERE id = :id"), {"now": now, "id": row["id"]})
        db.session.commit()
        flash("パスワードを更新しました。ログインできます。", "success")
        return redirect(url_for("newauth.login_page"))

    return render_template("newauth/reset_confirm.html", form=form, token=token)
