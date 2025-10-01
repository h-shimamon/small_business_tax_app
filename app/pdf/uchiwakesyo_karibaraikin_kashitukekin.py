from __future__ import annotations

from typing import Any, NamedTuple

from flask import current_app, has_request_context, request
from flask_login import current_user
from reportlab.pdfbase import pdfmetrics  # noqa: F401 (kept for parity)

from app.company.models import Company, LoansReceivable, TemporaryPayment
from app.extensions import db
from app.utils import format_number

from .layout_utils import (
    append_left,
    append_right,
    baseline0_from_center,
    build_overlay,
    center_from_baseline,
    prepare_pdf_assets,
)
from .pdf_fill import TextSpec


class TableLayout(NamedTuple):
    row1_center: float
    row_step: float
    rows_per_page: int
    data_rows_per_page: int
    right_margin: float
    columns: dict[str, tuple[float, float]]


class LoansLayout(NamedTuple):
    row1_center: float
    row_step: float
    rows_per_page: int
    data_rows_per_page: int
    right_margin: float
    columns: dict[str, tuple[float, float]]
    dx_rate: float
    gap: float
    interest_font_delta: float
    rate_anchor_x: float
    collateral_x: float


def _format_currency(n: int | None) -> str:
    return format_number(n)


def _resolve_company_id(company_id: int | None) -> int:
    if company_id is not None:
        return company_id
    if not has_request_context():
        raise RuntimeError("company_id is required outside a request context")
    company = Company.query.filter_by(user_id=current_user.id).first_or_404()
    return company.id


def _maybe_debug_rect(
    rectangles: list[tuple[int, float, float, float, float]],
    *,
    label: str,
    page: int,
    center_y: float,
    font_size: float,
    row_index: int,
) -> None:
    if not has_request_context() or request.args.get('debug_y') != '1':
        return
    y_dbg = center_y - font_size / 2.0
    rectangles.append((page, 50.0, y_dbg, 500.0, 0.6))
    try:
        current_app.logger.info(f"{label}={row_index} y={y_dbg:.2f} size={font_size}")
    except Exception:
        pass


def _column_spec(cols: dict[str, Any], name: str) -> tuple[float, float]:
    col = cols.get(name, {})
    return float(col.get('x', 0.0)), float(col.get('w', 0.0))


def _page_count(total_rows: int, rows_per_page: int) -> int:
    if total_rows <= 0:
        return 1
    return (total_rows + rows_per_page - 1) // rows_per_page


def _row_center(
    row_index: int,
    baseline0: float | None,
    *,
    row1_center: float,
    row_step: float,
    balance_font: float,
    eff_step: float | None = None,
) -> tuple[float, float]:
    natural_center = row1_center - row_step * row_index
    if baseline0 is None:
        baseline0 = baseline0_from_center(natural_center, balance_font)
        return natural_center, baseline0
    step = eff_step if eff_step is not None else row_step
    center_y = center_from_baseline(baseline0, step, row_index, balance_font)
    return center_y, baseline0


def _temporary_payment_layout(geom: dict[str, Any]) -> TableLayout:
    row = geom.get('row', {})
    rows = int(row.get('DETAIL_ROWS', 11))
    data_rows = int(row.get('DETAIL_ROWS_DATA', rows))
    default_cols = {
        'account': {'x': 75.5, 'w': 60.0},
        'reg_no': {'x': 120.0, 'w': 90.0},
        'partner': {'x': 205.0, 'w': 110.0},
        'address': {'x': 295.0, 'w': 110.0},
        'relationship': {'x': 408.0, 'w': 48.0},
        'balance': {'x': 407.0, 'w': 90.0},
        'remarks': {'x': 505.0, 'w': 60.0},
    }
    raw_cols = geom.get('cols') or {}
    merged_cols = {**default_cols, **raw_cols}
    columns = {name: _column_spec(merged_cols, name) for name in default_cols}
    right_margin = float(geom.get('margins', {}).get('right_margin', 0.0))
    return TableLayout(
        row1_center=float(row.get('ROW1_CENTER', 773.0)),
        row_step=float(row.get('ROW_STEP', 28.3)),
        rows_per_page=rows,
        data_rows_per_page=data_rows,
        right_margin=right_margin,
        columns=columns,
    )


def _temporary_payment_fonts() -> dict[str, float]:
    return {
        'account': 9.0,
        'reg_no': 8.0,
        'partner': 6.0,
        'address': 6.0,
        'relationship': 6.0,
        'balance': 12.0,
        'remarks': 6.5,
    }


def _collect_temporary_payments(company_id: int) -> list[TemporaryPayment]:
    return (
        db.session.query(TemporaryPayment)
        .filter_by(company_id=company_id)
        .order_by(TemporaryPayment.balance_at_eoy.desc(), TemporaryPayment.id.asc())
        .all()
    )


def _append_temporary_payment_row(
    texts: list[TextSpec],
    rectangles: list[tuple[int, float, float, float, float]],
    *,
    page_index: int,
    row_index: int,
    center_y: float,
    item: TemporaryPayment,
    layout: TableLayout,
    fonts: dict[str, float],
) -> None:
    def left(name: str, text: str, font_key: str) -> None:
        x, w = layout.columns[name]
        append_left(
            texts,
            page=page_index,
            x=x,
            w=w,
            center_y=center_y,
            text=text,
            font_name="NotoSansJP",
            font_size=fonts[font_key],
        )

    def right(name: str, text: str, font_key: str) -> None:
        x, w = layout.columns[name]
        append_right(
            texts,
            page=page_index,
            x=x,
            w=w,
            center_y=center_y,
            text=text,
            font_name="NotoSansJP",
            font_size=fonts[font_key],
            right_margin=layout.right_margin,
        )

    left('account', item.account_name or '仮払金', 'account')
    left('reg_no', item.registration_number or '', 'reg_no')
    left('partner', item.partner_name or '', 'partner')
    left('address', item.partner_address or '', 'address')
    left('relationship', item.relationship or '', 'relationship')
    right('balance', _format_currency(item.balance_at_eoy), 'balance')
    left('remarks', item.transaction_details or '', 'remarks')
    _maybe_debug_rect(
        rectangles,
        label='row_idx',
        page=page_index,
        center_y=center_y,
        font_size=fonts['balance'],
        row_index=row_index,
    )


def _render_temporary_payments(
    texts: list[TextSpec],
    rectangles: list[tuple[int, float, float, float, float]],
    items: list[TemporaryPayment],
    layout: TableLayout,
) -> None:
    if not items:
        return
    fonts = _temporary_payment_fonts()
    pages = _page_count(len(items), layout.data_rows_per_page)
    for page_index in range(pages):
        start = page_index * layout.data_rows_per_page
        chunk = items[start:start + layout.data_rows_per_page]
        baseline0: float | None = None
        for row_index, item in enumerate(chunk):
            center_y, baseline0 = _row_center(
                row_index,
                baseline0,
                row1_center=layout.row1_center,
                row_step=layout.row_step,
                balance_font=fonts['balance'],
            )
            _append_temporary_payment_row(
                texts,
                rectangles,
                page_index=page_index,
                row_index=row_index,
                center_y=center_y,
                item=item,
                layout=layout,
                fonts=fonts,
            )


def _loans_layout(geom: dict[str, Any]) -> LoansLayout:
    row = geom.get('row_kashitsuke', {})
    rows = int(row.get('DETAIL_ROWS', 10))
    data_rows = int(row.get('DETAIL_ROWS_DATA', rows))
    cols_raw = geom.get('cols_kashitsuke', {})
    columns = {
        'partner': _column_spec(cols_raw, 'partner'),
        'reg_no': _column_spec(cols_raw, 'reg_no'),
        'address': _column_spec(cols_raw, 'address'),
        'relationship': _column_spec(cols_raw, 'relationship'),
        'balance': _column_spec(cols_raw, 'balance'),
        'remarks': _column_spec(cols_raw, 'remarks'),
    }
    margins = geom.get('margins_kashitsuke', {})
    right_margin = float(margins.get('right_margin', 0.0))
    opts_raw = geom.get('remarks_kashitsuke', {})
    opts = opts_raw if isinstance(opts_raw, dict) else {}
    dx_rate = float(opts.get('rate_dx', 1.0))
    gap = float(opts.get('gap', 6.0))
    interest_font_delta = float(opts.get('interest_font_delta', -2.0))
    rate_anchor_x = float(opts.get('rate_anchor_x', 498.0))
    collateral_x = float(opts.get('collateral_x', 505.5))
    return LoansLayout(
        row1_center=float(row.get('ROW1_CENTER', 400.0)),
        row_step=float(row.get('ROW_STEP', 21.3)),
        rows_per_page=rows,
        data_rows_per_page=data_rows,
        right_margin=right_margin,
        columns=columns,
        dx_rate=dx_rate,
        gap=gap,
        interest_font_delta=interest_font_delta,
        rate_anchor_x=rate_anchor_x,
        collateral_x=collateral_x,
    )


def _loans_fonts() -> dict[str, float]:
    base = 6.5
    return {
        'partner': 8.0,
        'reg_no': 8.0,
        'address': 6.5,
        'relationship': 7.0,
        'balance': 12.0,
        'remarks': base,
        'rate': base + 1.0,
    }


def _collect_loans_receivable(company_id: int) -> list[LoansReceivable]:
    return (
        db.session.query(LoansReceivable)
        .filter_by(company_id=company_id)
        .order_by(LoansReceivable.id.asc())
        .all()
    )


def _append_loans_row(
    texts: list[TextSpec],
    rectangles: list[tuple[int, float, float, float, float]],
    *,
    page_index: int,
    row_index: int,
    center_y: float,
    item: LoansReceivable,
    layout: LoansLayout,
    fonts: dict[str, float],
) -> None:
    def left(name: str, text: str, font_key: str) -> None:
        x, w = layout.columns.get(name, (0.0, 0.0))
        append_left(
            texts,
            page=page_index,
            x=x,
            w=w,
            center_y=center_y,
            text=text,
            font_name="NotoSansJP",
            font_size=fonts[font_key],
        )

    def right(name: str, text: str, font_key: str) -> None:
        x, w = layout.columns.get(name, (0.0, 0.0))
        append_right(
            texts,
            page=page_index,
            x=x,
            w=w,
            center_y=center_y,
            text=text,
            font_name="NotoSansJP",
            font_size=fonts[font_key],
            right_margin=layout.right_margin,
        )

    left('partner', getattr(item, 'borrower_name', '') or '', 'partner')
    left('reg_no', getattr(item, 'registration_number', '') or '', 'reg_no')
    left('address', getattr(item, 'borrower_address', '') or '', 'address')
    left('relationship', getattr(item, 'relationship', '') or '', 'relationship')
    right('balance', _format_currency(getattr(item, 'balance_at_eoy', None)), 'balance')
    _maybe_debug_rect(
        rectangles,
        label='k_row_idx',
        page=page_index,
        center_y=center_y,
        font_size=fonts['balance'],
        row_index=row_index,
    )

    remarks_x, remarks_w = layout.columns.get('remarks', (0.0, 0.0))
    interest_anchor_x = remarks_x + layout.dx_rate - layout.gap
    interest_font_size = fonts['balance'] + layout.interest_font_delta

    received_interest = getattr(item, 'received_interest', None)
    interest_text = _format_currency(received_interest) if received_interest else ''
    if interest_text:
        append_right(
            texts,
            page=page_index,
            x=interest_anchor_x,
            w=0.0,
            center_y=center_y,
            text=interest_text,
            font_name="NotoSansJP",
            font_size=interest_font_size,
            right_margin=0.0,
        )

    interest_rate = getattr(item, 'interest_rate', None)
    if interest_rate is not None:
        try:
            rate_text = f"{float(str(interest_rate).rstrip('%')):.1f}"
        except Exception:
            raw = str(interest_rate)
            rate_text = raw[:-1] if raw.endswith('%') else raw
    else:
        rate_text = ''
    if rate_text:
        append_right(
            texts,
            page=page_index,
            x=layout.rate_anchor_x,
            w=0.0,
            center_y=center_y,
            text=rate_text,
            font_name="NotoSansJP",
            font_size=fonts['rate'],
            right_margin=0.0,
        )

    collateral_text = getattr(item, 'collateral_details', '') or ''
    if collateral_text:
        append_left(
            texts,
            page=page_index,
            x=layout.collateral_x,
            w=remarks_w,
            center_y=center_y,
            text=collateral_text,
            font_name="NotoSansJP",
            font_size=fonts['remarks'],
        )


def _append_loans_page_total(
    texts: list[TextSpec],
    chunk: list[LoansReceivable],
    *,
    page_index: int,
    baseline0: float | None,
    layout: LoansLayout,
    fonts: dict[str, float],
) -> None:
    if not chunk:
        return
    sum_balance = sum((getattr(item, 'balance_at_eoy', 0) or 0) for item in chunk)
    sum_interest = sum((getattr(item, 'received_interest', 0) or 0) for item in chunk)
    baseline_ref = baseline0 if baseline0 is not None else baseline0_from_center(layout.row1_center, fonts['balance'])
    sum_center_y = center_from_baseline(
        baseline_ref,
        layout.row_step,
        layout.data_rows_per_page,
        fonts['balance'],
    )
    balance_x, balance_w = layout.columns.get('balance', (0.0, 0.0))
    append_right(
        texts,
        page=page_index,
        x=balance_x,
        w=balance_w,
        center_y=sum_center_y,
        text=_format_currency(sum_balance),
        font_name="NotoSansJP",
        font_size=fonts['balance'],
        right_margin=layout.right_margin,
    )
    if sum_interest:
        remarks_x, _ = layout.columns.get('remarks', (0.0, 0.0))
        interest_anchor_x = remarks_x + layout.dx_rate - layout.gap
        append_right(
            texts,
            page=page_index,
            x=interest_anchor_x,
            w=0.0,
            center_y=sum_center_y,
            text=_format_currency(sum_interest),
            font_name="NotoSansJP",
            font_size=fonts['balance'] + layout.interest_font_delta,
            right_margin=0.0,
        )


def _render_loans_receivables(
    texts: list[TextSpec],
    rectangles: list[tuple[int, float, float, float, float]],
    items: list[LoansReceivable],
    layout: LoansLayout,
) -> None:
    if not items:
        return
    fonts = _loans_fonts()
    pages = _page_count(len(items), layout.data_rows_per_page)
    for page_index in range(pages):
        start = page_index * layout.data_rows_per_page
        chunk = items[start:start + layout.data_rows_per_page]
        baseline0: float | None = None
        for row_index, item in enumerate(chunk):
            center_y, baseline0 = _row_center(
                row_index,
                baseline0,
                row1_center=layout.row1_center,
                row_step=layout.row_step,
                balance_font=fonts['balance'],
            )
            _append_loans_row(
                texts,
                rectangles,
                page_index=page_index,
                row_index=row_index,
                center_y=center_y,
                item=item,
                layout=layout,
                fonts=fonts,
            )
        _append_loans_page_total(
            texts,
            chunk,
            page_index=page_index,
            baseline0=baseline0,
            layout=layout,
            fonts=fonts,
        )


def generate_uchiwakesyo_karibaraikin_kashitukekin(
    company_id: int | None,
    year: str = "2025",
    *,
    output_path: str,
) -> str:
    """
    Generate '仮払金（前渡金・貸付金）内訳書' PDF overlay for the given company.
    Upper zone: TemporaryPayment / Lower zone: LoansReceivable
    Writes to output_path and returns it.
    """
    company_id = _resolve_company_id(company_id)
    assets = prepare_pdf_assets(
        form_subdir="uchiwakesyo_karibaraikin-kashitukekin",
        geometry_key="uchiwakesyo_karibaraikin-kashitukekin",
        year=year,
    )

    texts: list[TextSpec] = []
    rectangles: list[tuple[int, float, float, float, float]] = []

    tp_items = _collect_temporary_payments(company_id)
    tp_layout = _temporary_payment_layout(assets.geometry)
    _render_temporary_payments(texts, rectangles, tp_items, tp_layout)

    loan_items = _collect_loans_receivable(company_id)
    loans_layout = _loans_layout(assets.geometry)
    _render_loans_receivables(texts, rectangles, loan_items, loans_layout)

    return build_overlay(
        base_pdf_path=assets.base_pdf,
        output_pdf_path=output_path,
        texts=texts,
        rectangles=rectangles,
        font_registrations={"NotoSansJP": assets.font_map["NotoSansJP"]},
    )
