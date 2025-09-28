from __future__ import annotations

from pathlib import Path
from unittest import mock

import pandas as pd
import pytest

from app import db
from app.company.models import AccountTitleMaster, MasterVersion
from app.company.services.master_data_service import MasterDataService


def _write_master_files(base_dir: Path) -> None:
    resources = base_dir / "resources" / "masters"
    resources.mkdir(parents=True, exist_ok=True)

    bs_df = pd.DataFrame([
        {"No.": 1, "勘定科目名": "現金", "決算書名": "資産", "大分類": "資産", "中分類": "流動資産", "小分類": "現金預金", "内訳書": "現金等"}
    ])
    pl_df = pd.DataFrame([
        {"No.": 10, "勘定科目名": "売上高", "決算書名": "損益", "大分類": "売上", "中分類": "売上", "小分類": "売上", "内訳書": "売上"}
    ])

    bs_df.to_csv(resources / "balance_sheet.csv", index=False)
    pl_df.to_csv(resources / "profit_and_loss.csv", index=False)
    (resources / "_version.txt").write_text("initial")


def _configure_master_paths(app, base_dir: Path) -> None:
    app.config.update(
        MASTER_DATA_BASE_DIR=str(base_dir),
        MASTER_DATA_BS_FILE='resources/masters/balance_sheet.csv',
        MASTER_DATA_PL_FILE='resources/masters/profit_and_loss.csv',
        MASTER_DATA_VERSION_FILE='resources/masters/_version.txt',
    )


@pytest.mark.usefixtures('init_database')
def test_force_sync_imports_master_data(app, tmp_path):
    _write_master_files(tmp_path)
    with app.app_context():
        _configure_master_paths(app, tmp_path)
        service = MasterDataService()

        service.force_sync()

        bs_count = AccountTitleMaster.query.filter_by(master_type='BS').count()
        pl_count = AccountTitleMaster.query.filter_by(master_type='PL').count()
        version = MasterVersion.query.order_by(MasterVersion.id.desc()).first()

        assert bs_count == 1
        assert pl_count == 1
        assert version is not None and version.version_hash


@pytest.mark.usefixtures('init_database')
def test_force_sync_rolls_back_on_error(app, tmp_path, monkeypatch):
    _write_master_files(tmp_path)
    with app.app_context():
        _configure_master_paths(app, tmp_path)
        db.session.add(AccountTitleMaster(number=99, name='既存', master_type='BS'))
        db.session.commit()

        service = MasterDataService()
        monkeypatch.setattr('app.company.services.master_data_service.pd.read_csv', mock.Mock(side_effect=ValueError('boom')))

        with pytest.raises(ValueError):
            service.force_sync()

        assert AccountTitleMaster.query.count() == 1
        assert MasterVersion.query.count() == 0
