# app/utils.py
import pandas as pd

def format_currency(value):
    """数値を日本円の通貨書式にフォーマットする。"""
    if value is None:
        return "0円"
    # 3桁区切りのカンマを付け、末尾に「円」を追加
    return f"{int(value):,}円"

def load_master_data():
    """
    マスターCSVファイルを読み込み、データフレームの辞書として返す。
    アプリケーション起動時に一度だけ呼び出されることを想定。
    """
    try:
        bs_master_df = pd.read_csv('resources/masters/balance_sheet.csv', encoding='utf-8-sig')
        bs_master_df.dropna(subset=['勘定科目名'], inplace=True)
        bs_master_df['勘定科目名'] = bs_master_df['勘定科目名'].str.strip()
        bs_master_df = bs_master_df.set_index('勘定科目名')

        pl_master_df = pd.read_csv('resources/masters/profit_and_loss.csv', encoding='utf-8-sig')
        pl_master_df.dropna(subset=['勘定科目名'], inplace=True)
        pl_master_df['勘定科目名'] = pl_master_df['勘定科目名'].str.strip()
        pl_master_df = pl_master_df.set_index('勘定科目名')
        
        return {
            'bs_master': bs_master_df,
            'pl_master': pl_master_df
        }
    except FileNotFoundError as e:
        raise RuntimeError(f"マスターファイルが見つかりません: {e}. アプリケーションを起動できません。")
    except Exception as e:
        raise RuntimeError(f"マスターファイルの読み込み中にエラーが発生しました: {e}")


def format_number(value):
    """整数値を3桁区切りの文字列にフォーマット（単位や通貨記号は付けない）。"""
    if value is None:
        return ""
    try:
        return f"{int(value):,}"
    except Exception:
        return ""
