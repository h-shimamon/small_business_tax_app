# app/commands.py
import click
from flask.cli import with_appcontext
from flask import current_app
from app.company.services.master_data_service import MasterDataService, calculate_and_save_hash

@click.command('seed-masters')
@with_appcontext
def seed_masters():
    """
    勘定科目マスターデータをCSVファイルからデータベースに強制的に再登録します。
    """
    click.echo('マスターデータの強制同期を開始します...')
    try:
        # MasterDataServiceを使用して同期処理を実行
        service = MasterDataService()
        service.force_sync()
        
        # 同期後、新しいハッシュ値をファイルに保存
        # サービスのbase_dir（正しいプロジェクトルート）を渡す
        new_hash = calculate_and_save_hash(service.base_dir)
        click.echo(f'新しいバージョンハッシュ ({new_hash}) を _version.txt に保存しました。')

        click.echo('マスターデータの同期が正常に完了しました。')
    except Exception as e:
        click.echo(f'エラー: マスターデータの同期中に問題が発生しました: {e}')
