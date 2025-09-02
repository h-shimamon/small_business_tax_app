from __future__ import annotations

from typing import List, Tuple, Optional
import os

from flask import has_request_context
from flask_login import current_user

from app import db
from app.company.models import Company, Deposit

from reportlab.pdfbase import pdfmetrics
from .pdf_fill import overlay_pdf, TextSpec
from .layout_utils import (
    load_geometry,
    center_from_row1,
    append_left,
    append_right,
)
from .fonts import default_font_map, ensure_font_registered
from app.utils import format_number



def _format_currency(n: Optional[int]) -> str:
    return format_number(n)


def _load_geometry(repo_root: str, year: str):
    # Backward compatibility shim if called directly elsewhere
    from .layout_utils import load_geometry as _lg
    return _lg("uchiwakesyo_yocyokin", year, repo_root=repo_root, required=True, validate=True)


def generate_uchiwakesyo_yocyokin(company_id: Optional[int], year: str = "2025", *, output_path: str) -> str:
    """
    Generate '預貯金等の内訳書' PDF overlay for the given company.
    Writes to output_path and returns it.
    """
    if company_id is None:
        if not has_request_context():
            raise RuntimeError("company_id is required outside a request context")
        company = Company.query.filter_by(user_id=current_user.id).first_or_404()
        company_id = company.id

    # Resolve paths
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    base_pdf = os.path.join(repo_root, f"resources/pdf_forms/uchiwakesyo_yocyokin/{year}/source.pdf")
    font_map = default_font_map(repo_root)
    try:
        ensure_font_registered("NotoSansJP", font_map["NotoSansJP"])  # best-effort registration
    except Exception:
        pass

    # Optional geometry override
    geom = load_geometry("uchiwakesyo_yocyokin", year, repo_root=repo_root, required=True, validate=True)

    # Row layout
    ROW1_CENTER = float(geom.get('row', {}).get('ROW1_CENTER', 700.0))
    ROW_STEP = float(geom.get('row', {}).get('ROW_STEP', 24.0))

    # Column rects (x, width); y is computed per-row center
    # Defaults are conservative and can be overridden by JSON
    cols = geom.get('cols', {
        'bank':      {'x': 60.0,  'w': 110.0},  # 金融機関名
        'branch':    {'x': 170.0, 'w': 90.0},   # 支店名
        'type':      {'x': 265.0, 'w': 70.0},   # 預金種類
        'number':    {'x': 340.0, 'w': 90.0},   # 口座番号
        'balance':   {'x': 440.0, 'w': 90.0},   # 期末現在高（右寄せ）
        'remarks':   {'x': 535.0, 'w': 60.0},   # 摘要
    })

    def col(name: str) -> Tuple[float, float]:
        c = cols.get(name, {})
        return float(c.get('x', 0.0)), float(c.get('w', 0.0))

    texts: List[TextSpec] = []

    # Fetch items
    items: List[Deposit] = (
        db.session.query(Deposit)
        .filter_by(company_id=company_id)
        .order_by(Deposit.id.asc())
        .all()
    )

    # Paging: 1ページあたり23明細行 + 24行目（合計）
    # 固定仕様: 明細は23行、24行目に総額を必ず印字（年や幾何に依存させない）
    rows_per_page = 23
    sum_row_index = 23  # 24行目（index=23）

    # Shared alignment: compute a common right edge for the balance column (geometry right edge minus small margin)
    vx0, vw0 = col('balance')
    right_margin = float(geom.get('margins', {}).get('right_margin', 0.0))
    common_right = vx0 + vw0 - right_margin

    total_items = len(items)
    pages = (total_items + rows_per_page - 1) // rows_per_page if total_items > 0 else 1

    for page_index in range(pages):
        start = page_index * rows_per_page
        end = min(start + rows_per_page, total_items)
        chunk = items[start:end]

        # 明細行（1..23）
        for i, it in enumerate(chunk):
            row_idx = i  # 0..rows_per_page-1
            center_y = center_from_row1(ROW1_CENTER, ROW_STEP, row_idx)
            # font sizes
            fs = {
                'bank': 9.0,
                'branch': 9.0,
                'type': 9.0,
                'number': 9.0,
                'balance': 15.0,
                'remarks': 7.5,
            }
            # helpers
            def left(page: int, x: float, w: float, text: str, size: float):
                append_left(texts, page=page, x=x, w=w, center_y=center_y, text=text, font_name="NotoSansJP", font_size=size)

            def right(page: int, x: float, w: float, text: str, size: float):
                append_right(texts, page=page, x=x, w=w, center_y=center_y, text=text, font_name="NotoSansJP", font_size=size, right_margin=right_margin)

            p = page_index
            bx, bw = col('bank')
            left(p, bx, bw, it.financial_institution or "", fs['bank'])
            rx, rw = col('branch')
            left(p, rx, rw, it.branch_name or "", fs['branch'])
            tx, tw = col('type')
            left(p, tx, tw, it.account_type or "", fs['type'])
            nx, nw = col('number')
            left(p, nx, nw, it.account_number or "", fs['number'])
            vx, vw = col('balance')
            right(p, vx, vw, _format_currency(it.balance), fs['balance'])
            mx, mw = col('remarks')
            left(p, mx, mw, (it.remarks or ""), fs['remarks'])

        # 合計行（24行目）: そのページの明細合計を期末現在高列にのみ表示。
        page_sum = sum((it.balance or 0) for it in chunk)
        center_y = ROW1_CENTER - ROW_STEP * sum_row_index
        fs_balance = 15.0
        sum_text = _format_currency(page_sum)
        y = center_y - fs_balance / 2.0
        texts.append(TextSpec(page=page_index, x=(vx0 + vw0 - right_margin), y=y, text=sum_text, font_name="NotoSansJP", font_size=fs_balance, align="right"))

    overlay_pdf(
        base_pdf_path=base_pdf,
        output_pdf_path=output_path,
        texts=texts,
        grids=[],
        font_registrations={"NotoSansJP": font_map["NotoSansJP"]},
    )

    return output_path
