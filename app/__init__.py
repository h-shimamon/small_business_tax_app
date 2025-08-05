import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# データベースオブジェクトをここでインスタンス化します
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# Alembicがモデルを確実に検知できるように、ここでインポートします
from .company import models

def create_app():
    """
    アプリケーションファクトリ: Flaskアプリケーションのインスタンスを作成・設定します。
    """
    app = Flask(__name__, instance_relative_config=True)

    # アプリケーション設定
    # SECRET_KEYはセッション情報を暗号化するために必須です
    app.config['SECRET_KEY'] = 'a-secret-key-that-you-should-change'
    # データベースのパスをinstanceフォルダ内に設定します
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'database.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # インスタンスフォルダがなければ作成
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # データベースをアプリケーションに紐付けます
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'company.login'

    from .company.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        # リファクタリングで作成したブループリントをインポートします
        from .company import company_bp
        
        # ブループリントをアプリケーションに登録します
        app.register_blueprint(company_bp)

        # データベーステーブルを作成します (まだ存在しない場合)
        db.create_all()

        # テストユーザーがなければ作成
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin')
            admin_user.set_password('password')
            db.session.add(admin_user)
            db.session.commit()

        # CLIコマンドを登録
        from . import commands
        app.cli.add_command(commands.seed_masters)

        return app