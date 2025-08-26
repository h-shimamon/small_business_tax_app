from __future__ import annotations

from typing import List, Tuple, Optional
import os

from flask import has_request_context, request, current_app
from flask_login import current_user

from app import db
from app.company.models import Company, NotesReceivable

from reportlab.pdfbase import pdfmetrics  # noqa: F401 (kept for parity with siblings)
from .pdf_fill import overlay_pdf, TextSpec
from .layout_utils import (
    load_geometry,
    baseline0_from_center,
    center_from_baseline,
    append_left,
    append_right,
)
from .fonts import default_font_map, ensure_font_registered
from .date_jp import wareki_numeric_parts
from app.utils import format_number


def _format_currency(n: Optional[int]) -> str:
    return format_number(n)


def generate_uchiwakesyo_uketoritegata(company_id: Optional[int], year: str = "2025", *, output_path: str) -> str:
    """
    Generate '受取手形の内訳書' PDF overlay for the given company.
    Writes to output_path and returns it.
    """
    if company_id is None:
        if not has_request_context():
            raise RuntimeError("company_id is required outside a request context")
        company = Company.query.filter_by(user_id=current_user.id).first_or_404()
        company_id = company.id

    # Resolve paths
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    base_pdf = os.path.join(repo_root, f"resources/pdf_forms/uchiwakesyo_uketoritegata/{year}/source.pdf")
    font_map = default_font_map(repo_root)

    # Ensure font is registered before measuring string widths for right alignment
    try:
        ensure_font_registered("NotoSansJP", font_map["NotoSansJP"])  # best-effort
    except Exception:
        pass

    # Geometry (required=True for fail-fast if missing)
    geom = load_geometry("uchiwakesyo_uketoritegata", year, repo_root=repo_root, required=True, validate=True)

    # Row layout
    ROW1_CENTER = float(geom.get('row', {}).get('ROW1_CENTER', 760.0))
    ROW_STEP = float(geom.get('row', {}).get('ROW_STEP', 28.3))

    # Column rects (x, width); y is computed per-row center
    cols = geom.get('cols', {
        'account':  {'x': 60.0,  'w': 60.0},   # 科目（受取手形）
        'partner':  {'x': 80.0,  'w': 110.0},  # 振出人
        'reg_no':   {'x': 170.0, 'w': 90.0},   # 登録番号（法人番号）
        'address':  {'x': 265.0, 'w': 110.0},  # 支払銀行/支店
        'balance':  {'x': 377.5, 'w': 90.0},   # 金額（右寄せ）
        'remarks':  {'x': 535.0, 'w': 60.0},   # 摘要
    })

    def col(name: str) -> Tuple[float, float]:
        c = cols.get(name, {})
        return float(c.get('x', 0.0)), float(c.get('w', 0.0))

    texts: List[TextSpec] = []
    rectangles: List[Tuple[int, float, float, float, float]] = []

    # Fetch items
    items: List[NotesReceivable] = (
        db.session.query(NotesReceivable)
        .filter_by(company_id=company_id)
        .order_by(NotesReceivable.id.asc())
        .all()
    )

    # Paging: default 20明細/ページ + 合計行（JSONでrow.DETAIL_ROWSを上書き可能）
    rows_per_page = int(geom.get('row', {}).get('DETAIL_ROWS', 20))
    sum_row_index = rows_per_page  # 合計行の行インデックス

    # Shared alignment: compute common right edge for the balance column (geometry right edge minus small margin)
    vx0, vw0 = col('balance')
    right_margin = float(geom.get('margins', {}).get('right_margin', 0.0))
    common_right = vx0 + vw0 - right_margin  # noqa: F841 (reserved for future fine alignment)

    total_items = len(items)
    pages = (total_items + rows_per_page - 1) // rows_per_page if total_items > 0 else 1

    for page_index in range(pages):
        start = page_index * rows_per_page
        end = min(start + rows_per_page, total_items)
        chunk = items[start:end]

        baseline0 = None

        # 明細行
        for i, it in enumerate(chunk):
            row_idx = i  # 0..rows_per_page-1
            natural_center = ROW1_CENTER - ROW_STEP * row_idx
            fs = {
                'account': 10.0,
                'reg_no': 8.0,
                'partner': 7.0,         # 振出人 -1pt
                'issue_date': 9.0,
                'due_date': 9.0,
                'payer_bank': 7.5,      # 支払銀行名 -1pt（8.5→7.5）
                'payer_branch': 7.5,    # 支払支店名 -1pt（8.5→7.5）
                'balance': 11.5,
                'discount_bank': 9.0,
                'discount_branch': 9.0,
                'remarks': 7.0,         # 摘要 -1pt
            }
            if row_idx == 0:
                center_y = natural_center
                baseline0 = baseline0_from_center(center_y, fs['balance'])
            else:
                eff_step = 23.8  # uniform row spacing between all rows (pt)
                center_y = center_from_baseline((baseline0 if baseline0 is not None else baseline0_from_center(ROW1_CENTER, fs['balance'])), eff_step, row_idx, fs['balance'])

            def left(page: int, x: float, w: float, text: str, size: float):
                append_left(texts, page=page, x=x, w=w, center_y=center_y, text=text, font_name="NotoSansJP", font_size=size)

            def right(page: int, x: float, w: float, text: str, size: float):
                append_right(texts, page=page, x=x, w=w, center_y=center_y, text=text, font_name="NotoSansJP", font_size=size, right_margin=right_margin)
                # debug guideline
                try:
                    if has_request_context() and request.args.get('debug_y') == '1':
                        y_dbg = center_y - size / 2.0
                        rectangles.append((page, 50.0, y_dbg, 500.0, 0.6))
                        current_app.logger.info(f"row_idx={row_idx} y={y_dbg:.2f} size={size}")
                except Exception:
                    pass

            p = page_index
            acx, acw = col('account')
            left(p, acx, acw, '', fs['account'])
            rx, rw = col('reg_no')
            left(p, rx, rw, it.registration_number or "", fs['reg_no'])
            px, pw = col('partner')
            left(p, px, pw, it.drawer or "", fs['partner'])
            # date formatter (wareki YYMMDD, no era name and no kanji)
            def _wareki_ymd_no_era(value_any) -> str:
                try:
                    parts = wareki_numeric_parts(value_any)
                    if parts:
                        wy, mm, dd = parts
                        return f"{wy}   {mm}   {dd}"
                except Exception:
                    return ""
                return ""
            idx, idw = col('issue_date')
            # Prefer date columns when present; fallback to string
            issue_src = getattr(it, 'issue_date_date', None) or it.issue_date
            left(p, idx, idw, _wareki_ymd_no_era(issue_src), fs['issue_date'])
            ddx, ddw = col('due_date')
            due_src = getattr(it, 'due_date_date', None) or it.due_date
            left(p, ddx, ddw, _wareki_ymd_no_era(due_src), fs['due_date'])
            pbx, pbw = col('payer_bank')
            left(p, pbx, pbw, (it.payer_bank or ""), fs['payer_bank'])
            pbrx, pbrw = col('payer_branch')
            left(p, pbrx, pbrw, (it.payer_branch or ""), fs['payer_branch'])
            bx, bw = col('balance')
            right(p, bx, bw, _format_currency(it.amount), fs['balance'])
            # Render discount bank and branch stacked vertically within the same column
            dbx, dbw = col('discount_bank')
            try:
                delta = 4.6  # vertical offset for two-line stacking within one row (widened)
                # Render bank on top, branch below (PDF y increases upward)
                top_center = center_y + delta
                bottom_center = center_y - delta
                if (it.discount_bank or "").strip():
                    append_left(texts, page=p, x=dbx, w=dbw, center_y=top_center, text=(it.discount_bank or ""), font_name="NotoSansJP", font_size=fs['discount_bank'])
                if (it.discount_branch or "").strip():
                    append_left(texts, page=p, x=dbx, w=dbw, center_y=bottom_center, text=(it.discount_branch or ""), font_name="NotoSansJP", font_size=fs['discount_branch'])
            except Exception:
                # Fallback to single-line rendering in the unlikely event of an error
                left(p, dbx, dbw, (it.discount_bank or ""), fs['discount_bank'])
            mx, mw = col('remarks')
            left(p, mx, mw, (it.remarks or ""), fs['remarks'])

        # 合計行（そのページの内訳合計を金額列にのみ表示）
        page_sum = sum((it.amount or 0) for it in chunk)
        fs_balance = 11.5
        eff_step_sum = 23.8
        baseline0_sum = (baseline0 if baseline0 is not None else (ROW1_CENTER - fs_balance / 2.0))
        baseline_sum = baseline0_sum - eff_step_sum * sum_row_index
        center_y = baseline_sum + fs_balance / 2.0
        sum_text = _format_currency(page_sum)
        y = center_y - fs_balance / 2.0
        texts.append(TextSpec(page=page_index, x=(vx0 + vw0 - right_margin), y=y, text=sum_text, font_name="NotoSansJP", font_size=fs_balance, align="right"))

    overlay_pdf(
        base_pdf_path=base_pdf,
        output_pdf_path=output_path,
        texts=texts,
        grids=[],
        rectangles=rectangles,
        font_registrations={"NotoSansJP": font_map["NotoSansJP"]},
    )

    return output_path
