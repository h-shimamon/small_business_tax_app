# app/__init__.py
import os
from flask import Flask
from .extensions import db, login_manager, migrate
from .company.models import User

def create_app(config_class=None):
    """
    アプリケーションファクトリ: Flaskアプリケーションのインスタンスを作成・設定します。
    """
    app = Flask(__name__, instance_relative_config=True)

    # --- 設定の読み込み ---
    if config_class is None:
        # デフォルト設定をconfig.pyから読み込む
        app.config.from_object('config.Config')
    else:
        # テスト時など、引数で渡された設定クラスを読み込む
        app.config.from_object(config_class)

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
        return User.query.get(int(user_id))

    # --- ブループリントの登録 ---
    from .company import company_bp
    app.register_blueprint(company_bp)

    # --- CLIコマンドの登録 ---
    from . import commands
    commands.register_commands(app)

    return app
