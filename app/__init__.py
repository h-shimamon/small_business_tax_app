# app/__init__.py
import os
from flask import Flask
from .extensions import db, login_manager, migrate
from .company.models import User

def create_app(test_config=None):
    """
    アプリケーションファクトリ: Flaskアプリケーションのインスタンスを作成・設定します。
    """
    app = Flask(__name__, instance_relative_config=True)

    # --- 設定の読み込み ---
    if test_config is None:
        # デフォルト設定をconfig.pyから読み込む
        app.config.from_object('config.Config')
    else:
        # テスト時など、引数で渡された設定を読み込む
        app.config.from_mapping(test_config)

    # インスタンスフォルダがなければ作成
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # --- 拡張機能の初期化 ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'company.login' # ログインが必要なページのビュー

    # --- ユーザーローダーの定義 ---
    @login_manager.user_loader
    def load_user(user_id):
        # Userモデルのインポートをここで行うことで循環参照を回避
        return db.session.get(User, int(user_id))

    # --- Jinja2フィルターの登録 ---
    from .utils import format_currency
    app.jinja_env.filters['format_currency'] = format_currency

    # --- ブループリントの登録 ---
    from .company import company_bp
    app.register_blueprint(company_bp)
    # --- HoujinBangou integration (dev stub; read-only API) ---
    try:
        from app.integrations.houjinbangou.stub_client import StubHojinClient
        from app.services.corporate_number_service import CorporateNumberService
        from app.api.corporate_number import create_blueprint as create_corp_api

        hojin_client = StubHojinClient()
        corp_service = CorporateNumberService(hojin_client)
        app.register_blueprint(create_corp_api(corp_service))
    except Exception:
        # 連携失敗は起動を阻害しない
        pass

    # --- CLIコマンドの登録 ---
    from . import commands
    commands.register_commands(app)

    return app
