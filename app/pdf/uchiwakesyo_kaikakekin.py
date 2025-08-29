from __future__ import annotations

from typing import List, Tuple, Optional
import os

from flask import has_request_context, request, current_app
from flask_login import current_user

from app import db
from app.company.models import Company, AccountsPayable

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


def generate_uchiwakesyo_kaikakekin(company_id: Optional[int], year: str = "2025", *, output_path: str) -> str:
    """
    買掛金（未払金・未払費用）の内訳書 PDF オーバレイを生成して output_path に書き込み、そのパスを返す。
    """
    if company_id is None:
        if not has_request_context():
            raise RuntimeError("company_id is required outside a request context")
        company = Company.query.filter_by(user_id=current_user.id).first_or_404()
        company_id = company.id

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    base_pdf = os.path.join(repo_root, f"resources/pdf_forms/uchiwakesyo_kaikakekin/{year}/source.pdf")
    font_map = default_font_map(repo_root)

    try:
        ensure_font_registered("NotoSansJP", font_map["NotoSansJP"])  # best-effort for width/align
    except Exception:
        pass

    geom = load_geometry("uchiwakesyo_kaikakekin", year, repo_root=repo_root, required=True, validate=True)

    ROW1_CENTER = float(geom.get('row', {}).get('ROW1_CENTER', 773.0))
    ROW_STEP = float(geom.get('row', {}).get('ROW_STEP', 28.3))
    rows_per_page = int(geom.get('row', {}).get('DETAIL_ROWS_DATA', geom.get('row', {}).get('DETAIL_ROWS', 20)))

    cols = geom.get('cols', {})

    def col(name: str) -> Tuple[float, float]:
        c = cols.get(name, {})
        return float(c.get('x', 0.0)), float(c.get('w', 0.0))

    vx0, vw0 = col('balance')
    right_margin = float(geom.get('margins', {}).get('right_margin', 0.0))

    texts: List[TextSpec] = []
    rectangles: List[Tuple[int, float, float, float, float]] = []

    items: List[AccountsPayable] = (
        db.session.query(AccountsPayable)
        .filter_by(company_id=company_id)
        .order_by(AccountsPayable.balance_at_eoy.desc(), AccountsPayable.id.asc())
        .all()
    )

    total = len(items)
    pages = (total + rows_per_page - 1) // rows_per_page if total > 0 else 1

    for page_index in range(pages):
        start = page_index * rows_per_page
        end = min(start + rows_per_page, total)
        chunk = items[start:end]

        baseline0 = None

        for i, it in enumerate(chunk):
            row_idx = i
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
                center_y = center_from_baseline((baseline0 if baseline0 is not None else baseline0_from_center(ROW1_CENTER, fs['balance'])), ROW_STEP, row_idx, fs['balance'])

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
            acx, acw = col('account')
            left(p, acx, acw, it.account_name or "", fs['account'])
            rx, rw = col('reg_no')
            left(p, rx, rw, (getattr(it, 'registration_number', '') or ''), fs['reg_no'])  # 登録番号
            px, pw = col('partner')
            left(p, px, pw, it.partner_name or "", fs['partner'])
            ax, aw = col('address')
            left(p, ax, aw, (it.partner_address or ""), fs['address'])
            bx, bw = col('balance')
            right(p, bx, bw, _format_currency(it.balance_at_eoy), fs['balance'])
            mx, mw = col('remarks')
            left(p, mx, mw, (it.remarks or ""), fs['remarks'])

        # Page total (24th row): sum of amounts in this page
        page_sum = sum((getattr(it, 'balance_at_eoy', 0) or 0) for it in chunk)
        fs_balance = 13.0
        base_b0 = baseline0 if baseline0 is not None else baseline0_from_center(ROW1_CENTER, fs_balance)
        sum_center_y = center_from_baseline(base_b0, ROW_STEP, rows_per_page, fs_balance)
        append_right(texts, page=p, x=vx0, w=vw0, center_y=sum_center_y, text=_format_currency(page_sum), font_name="NotoSansJP", font_size=fs_balance, right_margin=right_margin)

    overlay_pdf(
        base_pdf_path=base_pdf,
        output_pdf_path=output_path,
        texts=texts,
        grids=[],
        rectangles=rectangles,
        font_registrations={"NotoSansJP": font_map["NotoSansJP"]},
    )

    return output_path
