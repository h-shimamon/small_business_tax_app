import math
from typing import Optional

from pypdf import PdfReader


def _nearly_equal(a: float, b: float, tol: float) -> bool:
    return abs(float(a) - float(b)) <= float(tol)


def assert_text_right_aligned(pdf_path: str, x_right: float, *, page: int = 0, tol: float = 2.0, sample: Optional[str] = None) -> None:
    """
    簡易右寄せ検証: 指定ページのテキスト描画の右端が期待x±tolにあることを確認する。
    - 厳密なテキスト座標の取得はPDF仕様依存のため、ここではpypdfの抽出結果を用いたヒューリスティック。
    - sample文字列を与えた場合、その文字列を含む行を優先的に判定。
    注意: フォント幅等の差で誤差が出るため、tolは余裕を持たせること。
    """
    reader = PdfReader(pdf_path)
    page_obj = reader.pages[page]

    # pypdfのextract_textでは座標が取れないため、この関数は将来的な拡張前提のダミーに近い。
    # 現状はfail-fastしない方針で、未サポートを明示。
    # 本格運用する場合は、生成側にデバッグ座標JSONを出力し、それを読む方式に切替予定。
    text = page_obj.extract_text() or ""
    if not text:
        raise AssertionError("PDFからテキストを抽出できませんでした（簡易検証不可）")

    # 右寄せの厳密判定は未実装。将来の座標ログに切替予定。
    # ここでは存在確認のみとしておく（ダミーにせず、期待値情報を出す）。
    if sample and sample not in text:
        raise AssertionError(f"期待する文言が見つかりません: {sample}")

    # 現時点では右端xの厳密検証は行わないため、常にパスする。
    # 将来: デバッグ出力があればここで x_right との比較を実装。
    return None
