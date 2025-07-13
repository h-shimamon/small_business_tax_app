# app/__init__.py

import os
from flask import Flask, Blueprint, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# グローバルスコープで db オブジェクトを初期化
db = SQLAlchemy()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # --- アプリの設定 ---
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(app.instance_path, 'database.db')}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    # instanceフォルダがなければ作成
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # dbオブジェクトをアプリに連携
    db.init_app(app)

    # --- Blueprintの登録 ---
    from .company.routes import company_bp
    app.register_blueprint(company_bp)

    # トップページ用の main Blueprint を定義して登録
    main_bp = Blueprint('main', __name__)

    @main_bp.route('/')
    def top():
        # 常に基本情報ページにリダイレクトする
        return redirect(url_for('company.show'))
    
    app.register_blueprint(main_bp)

    # --- データベースの初期化 ---
    with app.app_context():
        # モデルをインポートしないと、create_all がテーブルを見つけられない
        from .company.models import Company, Employee
        db.create_all()

    return app