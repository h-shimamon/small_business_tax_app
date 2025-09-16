# app/__init__.py
import os
import sys
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass
from flask import Flask
from .extensions import db, login_manager, migrate
from .company.models import User

def create_app(test_config=None):
    """
    アプリケーションファクトリ: Flaskアプリケーションのインスタンスを作成・設定します。
    """
    app = Flask(__name__, instance_relative_config=True)

    # --- Jinja テンプレートグローバルの確実な登録（テスト/inline描画でも有効） ---
    try:
        from .constants.ui_options import get_ui_options  # type: ignore
        # 関数をグローバル関数として公開
        app.add_template_global(get_ui_options, name='get_ui_options')
        # データも既定プロファイルで公開（settings未初期化でも参照可能）
        profile = os.getenv('APP_UI_PROFILE', 'default')
        app.add_template_global(get_ui_options(profile), name='ui_options')
    except Exception:
        pass

    # --- 設定の読み込み/初期化 ---
    if test_config is None:
        env = (os.getenv('APP_ENV', 'development') or 'development').lower()
        env_map = {
            'development': 'config.DevConfig',
            'testing': 'config.TestingConfig',
            'production': 'config.ProductionConfig',
        }
        app.config.from_object(env_map.get(env, 'config.Config'))
    else:
        app.config.from_mapping(test_config)

    # インスタンスフォルダがなければ作成
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 型付き設定を app.extensions に登録（DIの根）
    try:
        from .config.schema import AppSettings
        app.extensions.setdefault('settings', AppSettings())
    except Exception:
        pass

    # app レベルで ui_options を context に注入（堅牢化）
    try:
        from .ui.context import attach_app_ui_context  # type: ignore
        attach_app_ui_context(app)
    except Exception:
        pass

    # Logging level setup (env-based)
    try:
        import logging as _logging
        lvl = str(app.config.get('LOG_LEVEL', 'INFO')).upper()
        level = getattr(_logging, lvl, _logging.INFO)
        app.logger.setLevel(level)
        _logging.getLogger('werkzeug').setLevel(level)
    except Exception:
        pass

    # Production secret key safety check
    try:
        if (os.getenv('APP_ENV', 'development').lower() == 'production'):
            sk = str(app.config.get('SECRET_KEY') or '')
            if (not sk) or sk.startswith('a_default_dev_'):
                app.logger.warning('SECRET_KEY is not securely set for production environment')
    except Exception:
        pass

    # --- 拡張機能の初期化 ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'company.login'

    # --- ユーザーローダーの定義 ---
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Jinja2フィルターの登録 ---
    from .utils import format_currency, format_number
    app.jinja_env.filters['format_currency'] = format_currency
    app.jinja_env.filters['format_number'] = format_number

    # --- ブループリントの登録 ---
    from .company import company_bp
    app.register_blueprint(company_bp)

    # --- Optional: new auth module (feature-flagged) ---
    try:
        flag = str(app.config.get('ENABLE_NEW_AUTH') or os.getenv('ENABLE_NEW_AUTH', '0')).lower()
        if flag in ('1', 'true', 'yes', 'on'):
            from .newauth import newauth_bp
            app.register_blueprint(newauth_bp, url_prefix='/xauth')
    except Exception as e:
        print("[newauth] register failed:", e, file=sys.stderr)
        pass

    # ---- Legacy redirector blueprint (root-level compat) ----
    try:
        from app.compat.redirector import bp_redirector
        app.register_blueprint(bp_redirector)
    except Exception:
        pass

    # --- 外部APIスタブ等（失敗しても起動は続ける） ---
    try:
        from app.integrations.houjinbangou.stub_client import StubHojinClient
        from app.services.corporate_number_service import CorporateNumberService
        from app.api.corporate_number import create_blueprint as create_corp_api
        hojin_client = StubHojinClient()
        corp_service = CorporateNumberService(hojin_client)
        app.register_blueprint(create_corp_api(corp_service))
    except Exception:
        pass

    # --- CLIコマンドの登録 ---
    from . import commands
    commands.register_commands(app)

    return app
