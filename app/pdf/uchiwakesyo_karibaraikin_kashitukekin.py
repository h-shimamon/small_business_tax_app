from __future__ import annotations

from typing import List, Tuple, Optional

from flask import has_request_context, request, current_app
from flask_login import current_user

from app import db
from app.company.models import Company, TemporaryPayment, LoansReceivable

from reportlab.pdfbase import pdfmetrics  # noqa: F401 (kept for parity)
from .pdf_fill import overlay_pdf, TextSpec
from .layout_utils import (
    prepare_pdf_assets,
    baseline0_from_center,
    center_from_baseline,
    append_left,
    append_right,
)
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

    assets = prepare_pdf_assets(
        form_subdir="uchiwakesyo_karibaraikin-kashitukekin",
        geometry_key="uchiwakesyo_karibaraikin-kashitukekin",
        year=year,
    )
    base_pdf = assets.base_pdf
    font_map = assets.font_map
    geom = assets.geometry

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

    _tp_rows_per_page = int(geom.get('row', {}).get('DETAIL_ROWS', 11))
    tp_data_rows_per_page = int(geom.get('row', {}).get('DETAIL_ROWS_DATA', 11))
    tp_total = len(tp_items)
    tp_pages = (tp_total + tp_data_rows_per_page - 1) // tp_data_rows_per_page if tp_total > 0 else 1

    for page_index in range(tp_pages):
        start = page_index * tp_data_rows_per_page
        end = min(start + tp_data_rows_per_page, tp_total)
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
    _k_rows_per_page = int(row_k.get('DETAIL_ROWS', 10))
    k_data_rows_per_page = int(row_k.get('DETAIL_ROWS_DATA', 7))

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
        k_pages = (k_total + k_data_rows_per_page - 1) // k_data_rows_per_page
        for page_index in range(k_pages):
            start = page_index * k_data_rows_per_page
            end = min(start + k_data_rows_per_page, k_total)
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
                base_font = 6.5
                rate_font = base_font + 1.0
                ri_val = getattr(it, 'received_interest', None)
                ir_val = getattr(it, 'interest_rate', None)
                cd_val = (getattr(it, 'collateral_details', '') or '')

                ri_text = _format_currency(ri_val) if ri_val else ''
                if ir_val is not None:
                    try:
                        rate_text = f"{float(str(ir_val).rstrip('%')):.1f}"
                    except Exception:
                        _s = str(ir_val)
                        rate_text = _s[:-1] if _s.endswith('%') else _s
                else:
                    rate_text = ''

                _parts = [t for t in [ri_text, rate_text, cd_val] if t]
                # Precise placement for remarks
                # Optional geometry overrides (no-op if absent)
                opts = geom.get('remarks_kashitsuke', {}) if isinstance(geom.get('remarks_kashitsuke', {}), dict) else {}
                _dx_interest = float(opts.get('interest_dx', -30.0))
                dx_rate = float(opts.get('rate_dx', 1.0))
                gap = float(opts.get('gap', 6.0))
                interest_font_delta = float(opts.get('interest_font_delta', -2.0))

                # Interest amount near balance, slightly smaller than balance font
                if ri_text:
                    anchor_x = mx + dx_rate - gap
                    append_right(texts, page=p, x=anchor_x, w=0.0, center_y=center_y, text=ri_text, font_name="NotoSansJP", font_size=(fs['balance'] + interest_font_delta), right_margin=0.0)

                # Helper for width (best-effort)
                def _w(t: str) -> float:
                    try:
                        return float(pdfmetrics.stringWidth(t, "NotoSansJP", base_font))
                    except Exception:
                        return float(len(t)) * 6.0

                def _w_rate(t: str) -> float:
                    try:
                        return float(pdfmetrics.stringWidth(t, "NotoSansJP", rate_font))
                    except Exception:
                        return float(len(t)) * 6.0 * (rate_font / base_font)

                # Rate and collateral laid out from remarks baseline
                _anchor_const = mx + dx_rate + 10.0 - 4.0
                rate_anchor_x = 498.0
                if rate_text:
                    append_right(texts, page=p, x=rate_anchor_x, w=0.0, center_y=center_y, text=rate_text, font_name="NotoSansJP", font_size=rate_font, right_margin=0.0)
                cur_x = 505.5
                if cd_val:
                    k_left(p, cur_x, mw, cd_val, base_font)

                # Page subtotal row (this page only)
                if row_idx == len(chunk) - 1:
                        sum_balance = sum((getattr(x, 'balance_at_eoy', 0) or 0) for x in chunk)
                        sum_interest = sum((getattr(x, 'received_interest', 0) or 0) for x in chunk)
                        sum_center_y = center_from_baseline((k_baseline0 if k_baseline0 is not None else baseline0_from_center(k_ROW1_CENTER, fs['balance'])), k_ROW_STEP, k_data_rows_per_page, fs['balance'])
                        append_right(texts, page=p, x=bx, w=bw, center_y=sum_center_y, text=_format_currency(sum_balance), font_name="NotoSansJP", font_size=fs['balance'], right_margin=right_margin_k)
                        if sum_interest:
                            append_right(texts, page=p, x=(mx + dx_rate - gap), w=0.0, center_y=sum_center_y, text=_format_currency(sum_interest), font_name="NotoSansJP", font_size=(fs['balance'] + interest_font_delta), right_margin=0.0)


    overlay_pdf(
        base_pdf_path=base_pdf,
        output_pdf_path=output_path,
        texts=texts,
        grids=[],
        font_registrations={"NotoSansJP": font_map["NotoSansJP"]},
    )

    return output_path
