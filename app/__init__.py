# app/__init__.py
import os
from flask import Flask, flash
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

    # ---- Legacy aliases at root (no blueprint prefix) ----
    from flask import redirect, url_for, request

    from flask_login import login_required

    @app.route('/statement/<page_key>/add')
    def legacy_add_item_root(page_key):
        # /statement/accounts_payable/add -> new add_item
        return redirect(url_for('company.add_item', page_key=page_key), code=302)

    @app.route('/statement_of_accounts')
    def legacy_statement_of_accounts_root():
        # /statement_of_accounts?page=deposits -> new statement_of_accounts (with forward-skip logic)
        from app.navigation_builder import navigation_tree
        from app.navigation import compute_skipped_steps_for_company
        from flask_login import current_user
        # default
        page = request.args.get('page', 'deposits')
        try:
            company = getattr(current_user, 'company', None)
            skipped = compute_skipped_steps_for_company(company.id) if company else set()
            # forward search only if current is skipped
            if skipped:
                # find current index in SoA children
                soa_children = []
                for node in navigation_tree:
                    if node.key == 'statement_of_accounts_group':
                        soa_children = node.children
                        break
                current_idx = None
                for idx, child in enumerate(soa_children):
                    if (child.params or {}).get('page') == page:
                        current_idx = idx
                        break
                if current_idx is not None and (soa_children[current_idx].key in skipped):
                    for nxt in soa_children[current_idx+1:]:
                        if nxt.key not in skipped:
                            page = (nxt.params or {}).get('page', page)
                            try:
                                flash('財務諸表に計上されていない勘定科目は自動でスキップされます。', 'skip')
                            except Exception:
                                pass
                            break
        except Exception:
            pass
        return redirect(url_for('company.statement_of_accounts', page=page), code=302)
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
