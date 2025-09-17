from __future__ import annotations

from typing import List, Tuple, Optional

from flask import has_request_context, request, current_app
from flask_login import current_user

from app import db
from app.company.models import Company, AccountsReceivable

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


def generate_uchiwakesyo_urikakekin(company_id: Optional[int], year: str = "2025", *, output_path: str) -> str:
    """
    Generate '売掛金（未収入金）の内訳書' PDF overlay for the given company.
    Writes to output_path and returns it.
    """
    if company_id is None:
        if not has_request_context():
            raise RuntimeError("company_id is required outside a request context")
        company = Company.query.filter_by(user_id=current_user.id).first_or_404()
        company_id = company.id

    assets = prepare_pdf_assets(
        form_subdir="uchiwakesyo_urikakekin",
        geometry_key="uchiwakesyo_urikakekin",
        year=year,
    )
    base_pdf = assets.base_pdf
    font_map = assets.font_map
    geom = assets.geometry

    # Row layout
    ROW1_CENTER = float(geom.get('row', {}).get('ROW1_CENTER', 760.0))
    ROW_STEP = float(geom.get('row', {}).get('ROW_STEP', 28.3))

    # Column rects (x, width); y is computed per-row center
    cols = geom.get('cols', {
        'account':  {'x': 60.0,  'w': 60.0},   # 科目（売掛金/未収入金）
        'partner':  {'x': 80.0,  'w': 110.0},  # 取引先名
        'reg_no':   {'x': 170.0, 'w': 90.0},   # 登録番号（法人番号）
        'address':  {'x': 265.0, 'w': 110.0},  # 取引先住所（狭め、必要ならJSONで拡張）
        'balance':  {'x': 377.5, 'w': 90.0},   # 期末現在高（右寄せ）
        'remarks':  {'x': 535.0, 'w': 60.0},   # 摘要
    })

    def col(name: str) -> Tuple[float, float]:
        c = cols.get(name, {})
        return float(c.get('x', 0.0)), float(c.get('w', 0.0))

    texts: List[TextSpec] = []
    rectangles: List[Tuple[int, float, float, float, float]] = []

    # Fetch items
    items: List[AccountsReceivable] = (
        db.session.query(AccountsReceivable)
        .filter_by(company_id=company_id)
        .order_by(AccountsReceivable.id.asc())
        .all()
    )

    # Paging: default 20明細/ページ + 合計行（JSONでrow.DETAIL_ROWSを上書き可能）
    rows_per_page = int(geom.get('row', {}).get('DETAIL_ROWS', 20))
    sum_row_index = rows_per_page  # 合計行の行インデックス

    # Shared alignment: compute common right edge for the balance column (geometry right edge minus small margin)
    vx0, vw0 = col('balance')
    right_margin = float(geom.get('margins', {}).get('right_margin', 0.0))
    _common_right = vx0 + vw0 - right_margin

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
                'account': 9.0,
                'partner': 7.0,
                'reg_no': 9.0,
                'address': 7.0,
                'balance': 13.0,
                'remarks': 7.5,
            }
            if row_idx == 0:
                center_y = natural_center
                baseline0 = baseline0_from_center(center_y, fs['balance'])
            else:
                eff_step = 20.3
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
                        current_app.logger.info(f"row_idx={row_idx} y={y:.2f} size={size}")
                except Exception:
                    pass

            p = page_index
            acx, acw = col('account')
            left(p, acx, acw, it.account_name or "", fs['account'])
            rx, rw = col('reg_no')
            left(p, rx, rw, it.registration_number or "", fs['reg_no'])
            px, pw = col('partner')
            left(p, px, pw, it.partner_name or "", fs['partner'])
            ax, aw = col('address')
            left(p, ax, aw, it.partner_address or "", fs['address'])
            bx, bw = col('balance')
            right(p, bx, bw, _format_currency(it.balance_at_eoy), fs['balance'])
            mx, mw = col('remarks')
            left(p, mx, mw, (it.remarks or ""), fs['remarks'])

        # 合計行（そのページの内訳合計を期末現在高列にのみ表示）
        page_sum = sum((it.balance_at_eoy or 0) for it in chunk)
        # 明細行と同じ等間隔（eff_step）で最終行を配置
        fs_balance = 13.0
        eff_step_sum = 20.3
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
