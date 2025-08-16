# app/company/services/master_data_service.py
import os
import hashlib
import pandas as pd
from flask import current_app
from app import db
from app.company.models import AccountTitleMaster, MasterVersion

class MasterDataService:
    """マスターデータの同期と管理を行うサービスクラス。"""

    def __init__(self):
        # プロジェクトのルートディレクトリを取得
        project_root = os.path.dirname(current_app.root_path)
        self.base_dir = project_root
        self.master_files = {
            'BS': os.path.join(self.base_dir, 'resources/masters/balance_sheet.csv'),
            'PL': os.path.join(self.base_dir, 'resources/masters/profit_and_loss.csv')
        }
        self.version_file_path = os.path.join(self.base_dir, 'resources/masters/_version.txt')

    def check_and_sync(self):
        """
        マスターデータのバージョンを確認し、変更があれば同期する。
        アプリケーション起動時に呼び出す。
        """
        current_hash = self._get_current_files_hash()
        last_db_hash = self._get_last_db_hash()

        if current_hash != last_db_hash:
            print("マスターデータに変更を検知しました。データベースを更新します...")
            self.force_sync()
            print("データベースの更新が完了しました。")
        else:
            print("マスターデータは最新です。")

    def force_sync(self):
        """
        強制的にマスターデータをCSVから読み込み、データベースを更新する。
        """
        try:
            # 1. 既存データの削除
            db.session.query(AccountTitleMaster).delete()
            db.session.query(MasterVersion).delete()

            # 2. CSVからデータを読み込み、DBに登録
            for master_type, file_path in self.master_files.items():
                if not os.path.exists(file_path):
                    print(f"警告: マスターファイルが見つかりません: {file_path}")
                    continue
                
                df = pd.read_csv(file_path, encoding='utf-8-sig')
                df.dropna(how='all', inplace=True)
                df.dropna(subset=['No.', '勘定科目名'], inplace=True)

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
            
            # 3. 新しいバージョンハッシュをDBに保存
            new_hash = self._get_current_files_hash()
            new_version = MasterVersion(version_hash=new_hash)
            db.session.add(new_version)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"エラー: マスターデータの同期中に問題が発生しました: {e}")
            raise

    def _get_current_files_hash(self):
        """現在のマスターCSVファイル群のハッシュ値を返す。_version.txtから読み込むことを基本とする。"""
        try:
            with open(self.version_file_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            print("警告: _version.txtが見つかりません。動的に生成します。")
            # ファイルが存在しない場合は、その場でハッシュを計算してファイルに保存する
            return calculate_and_save_hash(self.base_dir)


    def _get_last_db_hash(self):
        """データベースに保存されている最新のバージョンハッシュを返す。"""
        last_version = MasterVersion.query.order_by(MasterVersion.id.desc()).first()
        return last_version.version_hash if last_version else None

    def get_bs_master_df(self):
        """貸借対照表マスターをDataFrameとして取得する。"""
        query = AccountTitleMaster.query.filter_by(master_type='BS').all()
        df = pd.DataFrame([m.__dict__ for m in query])
        df.drop(columns=['_sa_instance_state'], inplace=True)
        df.set_index('name', inplace=True)
        return df

    def get_pl_master_df(self):
        """損益計算書マスターをDataFrameとして取得する。"""
        query = AccountTitleMaster.query.filter_by(master_type='PL').all()
        df = pd.DataFrame([m.__dict__ for m in query])
        df.drop(columns=['_sa_instance_state'], inplace=True)
        df.set_index('name', inplace=True)
        return df

def calculate_and_save_hash(base_dir):
    """
    現在のマスターファイルのハッシュを計算し、_version.txtに保存する。
    """
    master_files = [
        os.path.join(base_dir, 'resources/masters/balance_sheet.csv'),
        os.path.join(base_dir, 'resources/masters/profit_and_loss.csv')
    ]
    version_file_path = os.path.join(base_dir, 'resources/masters/_version.txt')

    # 個々のファイルのハッシュを結合して全体のハッシュを生成
    # これにより、ファイル名が変わっても内容が同じなら同じハッシュになる
    combined_hash = hashlib.sha256()
    for file_path in sorted(master_files):
         if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
                combined_hash.update(file_hash.encode('utf-8'))

    final_hash = combined_hash.hexdigest()
    
    with open(version_file_path, 'w') as f:
        f.write(final_hash)
    
    return final_hash
