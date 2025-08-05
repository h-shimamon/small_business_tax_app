# app/commands.py
import click
import pandas as pd
from flask.cli import with_appcontext
from app import db
from app.company.models import AccountTitleMaster
import os

@click.command('seed-masters')
@with_appcontext
def seed_masters():
    """
    勘定科目マスターデータをCSVファイルからデータベースに登録します。
    既存のデータはすべて削除された後、新しいデータが登録されます。
    """
    try:
        # 1. データ全件削除
        db.session.query(AccountTitleMaster).delete()
        click.echo('Existing master data deleted.')

        # 2. CSVファイルの処理
        base_dir = os.path.abspath(os.path.dirname(__name__))
        master_files = {
            'BS': os.path.join(base_dir, 'resources/masters/balance_sheet.csv'),
            'PL': os.path.join(base_dir, 'resources/masters/profit_and_loss.csv')
        }

        for master_type, file_path in master_files.items():
            if not os.path.exists(file_path):
                click.echo(f'Error: File not found at {file_path}')
                continue

            click.echo(f'Processing {file_path}...')
            
            # CSV読み込み
            df = pd.read_csv(file_path)

            # 空行の完全除去
            df.dropna(how='all', inplace=True)

            # 必須項目の欠損行を除去
            df.dropna(subset=['No.', '勘定科目名'], inplace=True)

            # データの登録
            for _, row in df.iterrows():
                master_entry = AccountTitleMaster(
                    number=int(row['No.']),
                    name=row['勘定科目名'],
                    statement_name=row.get('決算書名'),
                    major_category=row.get('大分類'),
                    middle_category=row.get('中分類'),
                    minor_category=row.get('小分類'),
                    breakdown_document=row.get('内訳書'),
                    master_type=master_type
                )
                db.session.add(master_entry)

        # 3. データベースへの保存
        db.session.commit()
        click.echo('Seeding master data completed successfully.')

    except Exception as e:
        db.session.rollback()
        click.echo(f'An error occurred: {e}')
