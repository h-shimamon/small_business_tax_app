from __future__ import annotations

from typing import List, Tuple, Optional
import os

from flask import has_request_context, request, current_app
from flask_login import current_user

from app import db
from app.company.models import Company, TemporaryPayment, LoansReceivable

from reportlab.pdfbase import pdfmetrics  # noqa: F401 (kept for parity)
from .pdf_fill import overlay_pdf, TextSpec
from .layout_utils import (
    load_geometry,
    baseline0_from_center,
    center_from_baseline,
    append_left,
    append_right,
)
from .fonts import default_font_map, ensure_font_registered
from app.utils import format_number


def _format_currency(n: Optional[int]) -> str:
    return format_number(n)


def generate_uchiwakesyo_karibaraikin_kashitukekin(company_id: Optional[int], year: str = "2025", *, output_path: str) -> str:
    """
    Generate '仮払金（前渡金・貸付金）内訳書' PDF overlay for the given company.
    Upper zone: TemporaryPayment / Lower zone: LoansReceivable
    Writes to output_path and returns it.
    """
    if company_id is None:
        if not has_request_context():
            raise RuntimeError("company_id is required outside a request context")
        company = Company.query.filter_by(user_id=current_user.id).first_or_404()
        company_id = company.id

    # Resolve paths
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    base_pdf = os.path.join(repo_root, f"resources/pdf_forms/uchiwakesyo_karibaraikin-kashitukekin/{year}/source.pdf")
    font_map = default_font_map(repo_root)

    # Ensure font is registered before measuring string widths
    try:
        ensure_font_registered("NotoSansJP", font_map["NotoSansJP"])  # best-effort
    except Exception:
        pass

    # Geometry (fail-fast if missing)
    geom = load_geometry("uchiwakesyo_karibaraikin-kashitukekin", year, repo_root=repo_root, required=True, validate=True)

    texts: List[TextSpec] = []
    rectangles: List[Tuple[int, float, float, float, float]] = []

    # ----------------------
    # Upper zone: TemporaryPayment (仮払金)
    # ----------------------
    ROW1_CENTER = float(geom.get('row', {}).get('ROW1_CENTER', 773.0))
    ROW_STEP = float(geom.get('row', {}).get('ROW_STEP', 28.3))

    cols = geom.get('cols', {
        'account':  {'x': 75.5,  'w': 60.0},
        'reg_no':   {'x': 120.0, 'w': 90.0},
        'partner':  {'x': 205.0, 'w': 110.0},
        'address':  {'x': 295.0, 'w': 110.0},
        'relationship': {'x': 408.0, 'w': 48.0},
        'balance':  {'x': 407.0, 'w': 90.0},
        'remarks':  {'x': 505.0, 'w': 60.0},
    })

    def col(name: str) -> Tuple[float, float]:
        c = cols.get(name, {})
        return float(c.get('x', 0.0)), float(c.get('w', 0.0))

    vx0, vw0 = col('balance')
    right_margin = float(geom.get('margins', {}).get('right_margin', 0.0))

    tp_items: List[TemporaryPayment] = (
        db.session.query(TemporaryPayment)
        .filter_by(company_id=company_id)
        .order_by(TemporaryPayment.balance_at_eoy.desc(), TemporaryPayment.id.asc())
        .all()
    )

    tp_rows_per_page = int(geom.get('row', {}).get('DETAIL_ROWS', 11))
    tp_total = len(tp_items)
    tp_pages = (tp_total + tp_rows_per_page - 1) // tp_rows_per_page if tp_total > 0 else 1

    for page_index in range(tp_pages):
        start = page_index * tp_rows_per_page
        end = min(start + tp_rows_per_page, tp_total)
        chunk = tp_items[start:end]

        baseline0 = None
        for i, it in enumerate(chunk):
            row_idx = i
            natural_center = ROW1_CENTER - ROW_STEP * row_idx
            fs = {
                'account': 9.0,
                'reg_no': 8.0,
                'partner': 6.0,
                'address': 6.0,
                'relationship': 6.0,
                'balance': 12.0,
                'remarks': 6.5,
            }
            if row_idx == 0:
                center_y = natural_center
                baseline0 = baseline0_from_center(center_y, fs['balance'])
            else:
                eff_step = ROW_STEP
                center_y = center_from_baseline((baseline0 if baseline0 is not None else baseline0_from_center(ROW1_CENTER, fs['balance'])), eff_step, row_idx, fs['balance'])

            def left(page: int, x: float, w: float, text: str, size: float):
                append_left(texts, page=page, x=x, w=w, center_y=center_y, text=text, font_name="NotoSansJP", font_size=size)

            def right(page: int, x: float, w: float, text: str, size: float):
                append_right(texts, page=page, x=x, w=w, center_y=center_y, text=text, font_name="NotoSansJP", font_size=size, right_margin=right_margin)
                try:
                    if has_request_context() and request.args.get('debug_y') == '1':
                        y_dbg = center_y - size / 2.0
                        rectangles.append((page, 50.0, y_dbg, 500.0, 0.6))
                        current_app.logger.info(f"row_idx={row_idx} y={y_dbg:.2f} size={size}")
                except Exception:
                    pass

            p = page_index
            ax, aw = col('account')
            left(p, ax, aw, (it.account_name or '仮払金'), fs['account'])
            rx, rw = col('reg_no')
            left(p, rx, rw, (it.registration_number or ''), fs['reg_no'])
            px, pw = col('partner')
            left(p, px, pw, (it.partner_name or ''), fs['partner'])
            ox, ow = col('address')
            left(p, ox, ow, (it.partner_address or ''), fs['address'])
            relx, relw = col('relationship')
            left(p, relx, relw, (it.relationship or ''), fs['relationship'])
            bx, bw = col('balance')
            right(p, bx, bw, _format_currency(it.balance_at_eoy), fs['balance'])
            mx, mw = col('remarks')
            left(p, mx, mw, (it.transaction_details or ''), fs['remarks'])

    # ----------------------
    # Lower zone: LoansReceivable (貸付金)
    # ----------------------
    row_k = geom.get('row_kashitsuke', {})
    k_ROW1_CENTER = float(row_k.get('ROW1_CENTER', 400.0))
    k_ROW_STEP = float(row_k.get('ROW_STEP', 21.3))
    k_rows_per_page = int(row_k.get('DETAIL_ROWS', 10))

    cols_k = geom.get('cols_kashitsuke', {})

    def k_col(name: str) -> Tuple[float, float]:
        c = cols_k.get(name, {})
        return float(c.get('x', 0.0)), float(c.get('w', 0.0))

    right_margin_k = float(geom.get('margins_kashitsuke', {}).get('right_margin', 0.0))

    k_items: List[LoansReceivable] = (
        db.session.query(LoansReceivable)
        .filter_by(company_id=company_id)
        .order_by(LoansReceivable.id.asc())
        .all()
    )

    k_total = len(k_items)
    if k_total > 0:
        k_pages = (k_total + k_rows_per_page - 1) // k_rows_per_page
        for page_index in range(k_pages):
            start = page_index * k_rows_per_page
            end = min(start + k_rows_per_page, k_total)
            chunk = k_items[start:end]

            k_baseline0 = None
            for i, it in enumerate(chunk):
                row_idx = i
                natural_center = k_ROW1_CENTER - k_ROW_STEP * row_idx
                fs = {
                    'partner': 8.0,      # 指定: +1pt
                    'reg_no': 8.0,       # 指定: +1pt
                    'address': 6.5,
                    'relationship': 7.0,
                    'balance': 12.0,
                    'remarks': 6.5,
                }
                if row_idx == 0:
                    center_y = natural_center
                    k_baseline0 = baseline0_from_center(center_y, fs['balance'])
                else:
                    center_y = center_from_baseline((k_baseline0 if k_baseline0 is not None else baseline0_from_center(k_ROW1_CENTER, fs['balance'])), k_ROW_STEP, row_idx, fs['balance'])

                def k_left(page: int, x: float, w: float, text: str, size: float):
                    append_left(texts, page=page, x=x, w=w, center_y=center_y, text=text, font_name="NotoSansJP", font_size=size)

                def k_right(page: int, x: float, w: float, text: str, size: float):
                    append_right(texts, page=page, x=x, w=w, center_y=center_y, text=text, font_name="NotoSansJP", font_size=size, right_margin=right_margin_k)
                    try:
                        if has_request_context() and request.args.get('debug_y') == '1':
                            y_dbg = center_y - size / 2.0
                            rectangles.append((page, 50.0, y_dbg, 500.0, 0.6))
                            current_app.logger.info(f"k_row_idx={row_idx} y={y_dbg:.2f} size={size}")
                    except Exception:
                        pass

                p = page_index
                # Columns for lower zone
                px, pw = k_col('partner')
                k_left(p, px, pw, (getattr(it, 'borrower_name', '') or ''), fs['partner'])
                rx, rw = k_col('reg_no')
                k_left(p, rx, rw, (getattr(it, 'registration_number', '') or ''), fs['reg_no'])
                ax, aw = k_col('address')
                k_left(p, ax, aw, (getattr(it, 'borrower_address', '') or ''), fs['address'])
                relx, relw = k_col('relationship')
                k_left(p, relx, relw, (getattr(it, 'relationship', '') or ''), fs['relationship'])
                bx, bw = k_col('balance')
                k_right(p, bx, bw, _format_currency(getattr(it, 'balance_at_eoy', None)), fs['balance'])

                # Remarks: 横並び [受取利息] [利率%] [担保]
                mx, mw = k_col('remarks')
                try:
                    base_font = 6.5
                    ri_val = getattr(it, 'received_interest', None)
                    ir_val = getattr(it, 'interest_rate', None)
                    cd_val = (getattr(it, 'collateral_details', '') or '')

                    ri_text = _format_currency(ri_val) if ri_val else ''
                    if ir_val is not None:
                        try:
                            rate_text = f"{float(ir_val):.2f}%"
                        except Exception:
                            rate_text = str(ir_val)
                    else:
                        rate_text = ''
                    collateral_text = cd_val

                    # X offsets per instruction
                    x_ri = mx - 30.0
                    cur_x = mx + 1.0

                    # width measurement (best-effort)
                    try:
                        def _w(t: str) -> float:
                            return pdfmetrics.stringWidth(t, "NotoSansJP", base_font)
                    except Exception:
                        def _w(t: str) -> float:
                            return float(len(t)) * 6.0

                    gap = 6.0
                    if ri_text:
                        # 期中の受取利息額のフォントを期末現在高に揃える（12pt）
                        append_left(texts, page=p, x=x_ri, w=mw, center_y=center_y, text=ri_text, font_name="NotoSansJP", font_size=(fs['balance'] - 2.0))
                    if rate_text:
                        append_left(texts, page=p, x=cur_x, w=mw, center_y=center_y, text=rate_text, font_name="NotoSansJP", font_size=base_font)
                        cur_x += _w(rate_text) + gap
                    if collateral_text:
                        append_left(texts, page=p, x=cur_x, w=mw, center_y=center_y, text=collateral_text, font_name="NotoSansJP", font_size=base_font)
                except Exception:
                    pass

    overlay_pdf(
        base_pdf_path=base_pdf,
        output_pdf_path=output_path,
        texts=texts,
        grids=[],
        font_registrations={"NotoSansJP": font_map["NotoSansJP"]},
    )

    return output_path
