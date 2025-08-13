# config.py
import os

# アプリケーションのベースディレクトリ
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    アプリケーションの基本設定クラス。
    環境変数から設定を読み込むことを推奨。
    """
    # --- セキュリティ関連 ---
    # SECRET_KEYはFlaskセッションの暗号化に使用されます。
    # 本番環境では必ず強力でランダムな値を環境変数から設定してください。
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_default_dev_secret_key')

    # --- データベース関連 ---
    # SQLALCHEMY_DATABASE_URIはデータベースの接続情報を定義します。
    # デフォルトでは、プロジェクトのinstanceフォルダにsqliteデータベースを作成します。
    # 本番環境ではPostgreSQLやMySQLなどの堅牢なデータベースを推奨します。
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')
    
    # パフォーマンス向上のため、Flask-SQLAlchemyのイベントシステムを無効化します。
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- その他の設定 ---
    # ここに他のアプリケーション設定を追加できます。
    # 例: MAIL_SERVER, MAIL_PORT, etc.
