import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# データベースオブジェクトをここでインスタンス化します
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(test_config=None):
    """
    アプリケーションファクトリ: Flaskアプリケーションのインスタンスを作成・設定します。
    """
    app = Flask(__name__, instance_relative_config=True)

    # アプリケーション設定
    app.config.from_mapping(
        SECRET_KEY='dev', # 本番環境ではランダムな値に置き換えること
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, 'database.db')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is None:
        # インスタンス設定があれば読み込む
        app.config.from_pyfile('config.py', silent=True)
    else:
        # テスト設定を読み込む
        app.config.from_mapping(test_config)

    # インスタンスフォルダがなければ作成
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 拡張機能の初期化
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'company.login'

    # ユーザーローダーの定義
    from .company.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ブループリントの登録前にルートをインポート
    from .company import company_bp
    with app.app_context():
        from .company import core, shareholders, offices, import_data, statement_of_accounts, auth
    app.register_blueprint(company_bp)

    # CLIコマンドの登録
    from . import commands
    commands.register_commands(app)

    return app