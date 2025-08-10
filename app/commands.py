# app/commands.py
import click
from flask.cli import with_appcontext
from app.company.services.master_data_service import MasterDataService
from app import db
from app.company.models import User

def register_commands(app):
    """アプリケーションにCLIコマンドを登録する"""
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_masters_command)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """
    データベースに初期データ（管理者ユーザーなど）を投入します。
    テーブルは `flask db upgrade` で先に作成しておく必要があります。
    """
    click.echo("データベースの初期データ投入を開始します...")
    try:
        # 管理者ユーザーがなければ作成
        if not User.query.filter_by(username='admin').first():
            from datetime import date
            from app.company.models import Company

            # 管理者ユーザー作成
            admin_user = User(username='admin')
            admin_user.set_password('password')
            db.session.add(admin_user)
            db.session.commit()
            click.echo("管理者ユーザーを作成しました。")

            # ダミーの会社情報を作成し、管理者ユーザーに紐付ける
            dummy_company = Company(
                corporate_number="1111111111111",
                company_name="（ダミー）株式会社 Gemini",
                company_name_kana="ダミー カブシキガイシャジェミニ",
                zip_code="1066126",
                prefecture="東京都",
                city="港区",
                address="六本木6-10-1 六本木ヒルズ森タワー",
                phone_number="03-6384-9000",
                establishment_date=date(2023, 1, 1),
                user_id=admin_user.id
            )
            db.session.add(dummy_company)
            db.session.commit()
            click.echo("管理者ユーザー用のダミー会社情報を作成しました。")
        else:
            click.echo("管理者ユーザーは既に存在します。")

        # マスターデータの同期
        service = MasterDataService()
        service.check_and_sync()
        click.echo("マスターデータの同期を確認しました。")
        click.echo("初期データの投入が完了しました。")
    except Exception as e:
        click.echo(f'エラー: 初期データ投入中に問題が発生しました: {e}')
        # エラーの詳細を出力
        import traceback
        traceback.print_exc()


@click.command('seed-masters')
@with_appcontext
def seed_masters_command():
    """
    勘定科目マスターデータをCSVファイルからデータベースに強制的に再登録します。
    """
    click.echo('マスターデータの強制同期を開始します...')
    try:
        service = MasterDataService()
        service.force_sync()
        click.echo('マスターデータの同期が正常に完了しました。')
    except Exception as e:
        click.echo(f'エラー: マスターデータの同期中に問題が発生しました: {e}')