# config.py
# NOTE: 設定値は「.env → app.config.schema.AppSettings → Flask app.config」の順で反映されます。
import os

# アプリケーションのベースディレクトリ
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # ---- Legacy compatibility flags ----
    import os as _os
    COMPAT_LEGACY_ENABLED = _os.getenv('COMPAT_LEGACY_ENABLED', 'true').lower() == 'true'
    COMPAT_DEADLINE = _os.getenv('COMPAT_DEADLINE', '2026-03-31')

    # ---- SoA completion marking behavior ----
    # GETでの自動完了マーク（互換維持のため既定True。将来的にFalseへ）
    SOA_MARK_ON_GET = _os.getenv('SOA_MARK_ON_GET', 'true').lower() == 'true'
    # POST成功時に完了マーク（既定True）
    SOA_MARK_ON_POST = _os.getenv('SOA_MARK_ON_POST', 'true').lower() == 'true'
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


class TestingConfig(Config):
    """テスト環境向けの設定。"""
    TESTING = True
    SERVER_NAME = os.environ.get('SERVER_NAME', 'localhost')
    # ログ関連（必要に応じてアプリ初期化時に使用）
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')


class ProductionConfig(Config):
    """本番環境向けの設定。"""
    # 本番では詳細ログを抑制
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    # SQLAlchemy接続の健全性向上（ドライバが対応していれば有効）
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True
    }
    # Cookie/CSRF/HTTPS の強化（本番想定）
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    PREFERRED_URL_SCHEME = 'https'


class DevConfig(Config):
    """開発環境向けの設定。"""
    # Differences from ProductionConfig:
    # - DEBUG/LOG_LEVEL are verbose for local diagnosis.
    # - CSRF is disabled to simplify local form testing.
    # - Session/remember cookies are not marked Secure and use HTTP scheme.
    # - Preferred URL scheme remains http for local endpoints.
    DEBUG = True
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    # 開発体験を優先（本番は ProductionConfig が強化設定）
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    PREFERRED_URL_SCHEME = 'http'
