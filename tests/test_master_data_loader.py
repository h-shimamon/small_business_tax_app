from pathlib import Path

from app.services.master_data_loader import (
    clear_master_dataframe_cache,
    load_master_dataframe,
)


def test_load_master_dataframe_trims_and_sets_index(tmp_path: Path):
    csv_path = tmp_path / 'master.csv'
    csv_path.write_text('勘定科目名,No.\n 現金 ,1\n', encoding='utf-8-sig')

    try:
        df = load_master_dataframe(str(csv_path), index_column='勘定科目名')
        assert '現金' in df.index
        assert df.loc['現金', 'No.'] == 1
    finally:
        clear_master_dataframe_cache()
