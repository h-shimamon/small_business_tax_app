# app/utils.py
from functools import lru_cache

from app.services.master_data_loader import load_master_dataframe


def format_currency(value):
    """数値を日本円の通貨書式にフォーマットする。"""
    if value is None:
        return "0円"
    # 3桁区切りのカンマを付け、末尾に「円」を追加
    return f"{int(value):,}円"

@lru_cache(maxsize=1)
def _load_master_frames():
    try:
        bs_master_df = load_master_dataframe('resources/masters/balance_sheet.csv', index_column='勘定科目名')
        pl_master_df = load_master_dataframe('resources/masters/profit_and_loss.csv', index_column='勘定科目名')
        return bs_master_df, pl_master_df
    except FileNotFoundError as e:
        raise RuntimeError(f"マスターファイルが見つかりません: {e}. アプリケーションを起動できません。") from e
    except Exception as e:
        raise RuntimeError(f"マスターファイルの読み込み中にエラーが発生しました: {e}") from e


def load_master_data():
    """マスターCSVを読み込み、呼び出し側には複製を返す。"""
    bs_master_df, pl_master_df = _load_master_frames()
    return {
        'bs_master': bs_master_df.copy(deep=True),
        'pl_master': pl_master_df.copy(deep=True)
    }


def format_number(value):
    """整数値を3桁区切りの文字列にフォーマット（単位や通貨記号は付けない）。"""
    if value is None:
        return ""
    try:
        return f"{int(value):,}"
    except Exception:
        return ""
