# app/company/services/master_data_service.py
from __future__ import annotations

import hashlib
import logging
import os
from functools import lru_cache
from typing import Dict

import pandas as pd
from flask import current_app

from app.services.master_data_loader import (
    clear_master_dataframe_cache,
    load_master_dataframe,
)

from app import db
from app.company.models import AccountTitleMaster, MasterVersion

class MasterDataService:
    """マスターデータの同期と管理を行うサービスクラス。"""

    def __init__(self):
        cfg = current_app.config
        base_dir = cfg.get('MASTER_DATA_BASE_DIR') or os.path.dirname(current_app.root_path)
        self.base_dir = base_dir

        def _resolve(path_value: str) -> str:
            if os.path.isabs(path_value):
                return path_value
            return os.path.join(base_dir, path_value)
        self.master_files: Dict[str, str] = {
            'BS': _resolve(cfg.get('MASTER_DATA_BS_FILE', 'resources/masters/balance_sheet.csv')),
            'PL': _resolve(cfg.get('MASTER_DATA_PL_FILE', 'resources/masters/profit_and_loss.csv')),
        }
        self.version_file_path = _resolve(cfg.get('MASTER_DATA_VERSION_FILE', 'resources/masters/_version.txt'))
        self.logger = logging.getLogger(__name__)

    def check_and_sync(self):
        """
        マスターデータのバージョンを確認し、変更があれば同期する。
        アプリケーション起動時に呼び出す。
        """
        current_hash = self._get_current_files_hash()
        last_db_hash = self._get_last_db_hash()

        if current_hash != last_db_hash:
            self.logger.info("マスターデータの変更を検知。データベースを更新します…")
            self.force_sync()
            self.logger.info("マスターデータの更新が完了しました。")
        else:
            self.logger.info("マスターデータは最新です。")

    def force_sync(self):
        """
        強制的にマスターデータをCSVから読み込み、データベースを更新する。
        """
        try:
            with db.session.begin():
                db.session.query(AccountTitleMaster).delete()
                db.session.query(MasterVersion).delete()

                for master_type, file_path in self.master_files.items():
                    if not os.path.exists(file_path):
                        self.logger.warning("マスターファイルが見つかりません: %s", file_path)
                        continue

                    df = load_master_dataframe(file_path, index_column=None).copy()
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
                            master_type=master_type,
                        )
                        db.session.add(master_entry)

                new_hash = self._get_current_files_hash()
                new_version = MasterVersion(version_hash=new_hash)
                db.session.add(new_version)
        except Exception as exc:
            self.logger.exception("マスターデータ同期中に問題が発生しました")
            raise
        finally:
            clear_master_dataframe_cache()


    def _get_current_files_hash(self):
        """現在のマスターCSVファイル群のハッシュ値を返す。_version.txtから読み込むことを基本とする。"""
        try:
            with open(self.version_file_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            self.logger.warning("_version.txt が見つかりません。動的に生成します。")
            return calculate_and_save_hash(self.base_dir, self.version_file_path, list(self.master_files.values()))


    def _get_last_db_hash(self):
        """データベースに保存されている最新のバージョンハッシュを返す。"""
        last_version = MasterVersion.query.order_by(MasterVersion.id.desc()).first()
        return last_version.version_hash if last_version else None


    def get_bs_master_df(self):
        """貸借対照表マスターをDataFrameとして取得する。"""
        try:
            from flask import current_app as _app
            if bool(_app.config.get('TESTING', False)):
                query = AccountTitleMaster.query.filter_by(master_type='BS').all()
                df = pd.DataFrame([m.__dict__ for m in query])
                df.drop(columns=['_sa_instance_state'], inplace=True, errors='ignore')
                if 'name' in df.columns:
                    df.set_index('name', inplace=True)
                return df
        except Exception:
            pass
        version_hash = self._get_last_db_hash() or ''
        return _load_master_df_cached('BS', version_hash)

    def get_pl_master_df(self):
        """損益計算書マスターをDataFrameとして取得する。"""
        try:
            from flask import current_app as _app
            if bool(_app.config.get('TESTING', False)):
                query = AccountTitleMaster.query.filter_by(master_type='PL').all()
                df = pd.DataFrame([m.__dict__ for m in query])
                df.drop(columns=['_sa_instance_state'], inplace=True, errors='ignore')
                if 'name' in df.columns:
                    df.set_index('name', inplace=True)
                return df
        except Exception:
            pass
        version_hash = self._get_last_db_hash() or ''
        return _load_master_df_cached('PL', version_hash)

@lru_cache(maxsize=8)
def _load_master_df_cached(master_type: str, version_hash: str):
    """指定タイプのマスタをDataFrameで返す（プロセス内LRUキャッシュ）。
    version_hashをキーに含めることで更新時に自動無効化する。
    """
    query = AccountTitleMaster.query.filter_by(master_type=master_type).all()
    df = pd.DataFrame([m.__dict__ for m in query])
    df.drop(columns=['_sa_instance_state'], inplace=True, errors='ignore')
    if 'name' in df.columns:
        df.set_index('name', inplace=True)
    return df

def clear_master_df_cache():
    """Invalidate the in-process cache for master DataFrames."""
    try:
        _load_master_df_cached.cache_clear()
    except Exception:
        pass


def calculate_and_save_hash(base_dir, version_file_path=None, master_files=None):
    """現在のマスターファイルのハッシュを計算し、指定パスに保存する。"""
    master_files = master_files or [
        os.path.join(base_dir, 'resources/masters/balance_sheet.csv'),
        os.path.join(base_dir, 'resources/masters/profit_and_loss.csv'),
    ]
    version_file_path = version_file_path or os.path.join(base_dir, 'resources/masters/_version.txt')

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
