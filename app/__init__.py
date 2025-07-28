import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# データベースオブジェクトをここでインスタンス化します
db = SQLAlchemy()

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

    with app.app_context():
        # リファクタリングで作成したブループリントをインポートします
        from .company import company_bp
        
        # ブループリントをアプリケーションに登録します
        app.register_blueprint(company_bp)

        # データベーステーブルを作成します (まだ存在しない場合)
        db.create_all()

        return app