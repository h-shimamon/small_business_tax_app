from __future__ import annotations

from typing import Any, NamedTuple

from flask import current_app, has_request_context, request
from flask_login import current_user

from app.company.models import Company, NotesPayable
from app.extensions import db
from app.utils import format_number

from .date_jp import wareki_numeric_parts
from .layout_utils import (
    append_left,
    append_right,
    baseline0_from_center,
    build_overlay,
    center_from_baseline,
    prepare_pdf_assets,
)
from .pdf_fill import TextSpec


class NotesLayout(NamedTuple):
    row1_center: float
    row_step: float
    data_rows_per_page: int
    sum_row_index: int
    right_margin: float
    columns: dict[str, tuple[float, float]]


def _format_currency(n: int | None) -> str:
    return format_number(n)


def _wareki_ymd_no_era(value_any) -> str:
    try:
        parts = wareki_numeric_parts(value_any)
        if parts:
            wy, mm, dd = parts
            return f"{wy}   {mm}   {dd}"
    except Exception:
        return ""
    return ""


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
        current_app.logger.info(f"row_idx={row_index} y={y_dbg:.2f} size={font_size}")
    except Exception:
        pass


def _column_spec(cols: dict[str, Any], name: str) -> tuple[float, float]:
    col = cols.get(name, {})
    return float(col.get('x', 0.0)), float(col.get('w', 0.0))


def _page_count(total_rows: int, rows_per_page: int) -> int:
    if total_rows <= 0:
        return 1
    return (total_rows + rows_per_page - 1) // rows_per_page


def _notes_layout(geom: dict[str, Any]) -> NotesLayout:
    row = geom.get('row', {})
    detail_rows = int(row.get('DETAIL_ROWS', 20))
    data_rows = int(row.get('DETAIL_ROWS_DATA', detail_rows))
    cols = geom.get('cols', {})
    columns = {
        'reg_no': _column_spec(cols, 'reg_no'),
        'partner': _column_spec(cols, 'partner'),
        'issue_date': _column_spec(cols, 'issue_date'),
        'due_date': _column_spec(cols, 'due_date'),
        'payer_bank': _column_spec(cols, 'payer_bank'),
        'payer_branch': _column_spec(cols, 'payer_branch'),
        'balance': _column_spec(cols, 'balance'),
        'remarks': _column_spec(cols, 'remarks'),
    }
    right_margin = float(geom.get('margins', {}).get('right_margin', 0.0))
    return NotesLayout(
        row1_center=float(row.get('ROW1_CENTER', 770.9)),
        row_step=float(row.get('ROW_STEP', 28.3)),
        data_rows_per_page=data_rows,
        sum_row_index=data_rows,
        right_margin=right_margin,
        columns=columns,
    )


def _notes_fonts() -> dict[str, float]:
    return {
        'reg_no': 7.5,
        'partner': 7.5,
        'payer_bank': 6.5,
        'payer_branch': 6.5,
        'issue_date': 8.5,
        'due_date': 8.5,
        'balance': 13.0,
        'remarks': 7.0,
    }


def _collect_notes_payable(company_id: int) -> list[NotesPayable]:
    return (
        db.session.query(NotesPayable)
        .filter_by(company_id=company_id)
        .order_by(NotesPayable.id.asc())
        .all()
    )


def _row_center(
    row_index: int,
    baseline0: float | None,
    *,
    layout: NotesLayout,
    balance_font: float,
) -> tuple[float, float]:
    natural_center = layout.row1_center - layout.row_step * row_index
    if baseline0 is None:
        baseline0 = baseline0_from_center(natural_center, balance_font)
        return natural_center, baseline0
    center_y = center_from_baseline(baseline0, layout.row_step, row_index, balance_font)
    return center_y, baseline0


def _append_note_row(
    texts: list[TextSpec],
    rectangles: list[tuple[int, float, float, float, float]],
    *,
    page_index: int,
    row_index: int,
    center_y: float,
    item: NotesPayable,
    layout: NotesLayout,
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

    left('reg_no', getattr(item, 'registration_number', '') or '', 'reg_no')
    left('partner', item.payee or '', 'partner')
    left('issue_date', _wareki_ymd_no_era(getattr(item, 'issue_date', None)), 'issue_date')
    left('due_date', _wareki_ymd_no_era(getattr(item, 'due_date', None)), 'due_date')
    left('payer_bank', getattr(item, 'payer_bank', '') or '', 'payer_bank')
    left('payer_branch', getattr(item, 'payer_branch', '') or '', 'payer_branch')
    right('balance', _format_currency(item.amount), 'balance')
    left('remarks', item.remarks or '', 'remarks')
    _maybe_debug_rect(
        rectangles,
        page=page_index,
        center_y=center_y,
        font_size=fonts['balance'],
        row_index=row_index,
    )


def _append_page_total(
    texts: list[TextSpec],
    *,
    page_index: int,
    chunk: list[NotesPayable],
    baseline0: float | None,
    layout: NotesLayout,
    fonts: dict[str, float],
) -> None:
    page_sum = sum((getattr(item, 'amount', 0) or 0) for item in chunk)
    baseline_ref = baseline0 if baseline0 is not None else baseline0_from_center(layout.row1_center, fonts['balance'])
    sum_center_y = center_from_baseline(
        baseline_ref,
        layout.row_step,
        layout.sum_row_index,
        fonts['balance'],
    )
    balance_x, balance_w = layout.columns.get('balance', (0.0, 0.0))
    append_right(
        texts,
        page=page_index,
        x=balance_x,
        w=balance_w,
        center_y=sum_center_y,
        text=_format_currency(page_sum),
        font_name="NotoSansJP",
        font_size=fonts['balance'],
        right_margin=layout.right_margin,
    )


def _render_notes_payable(
    texts: list[TextSpec],
    rectangles: list[tuple[int, float, float, float, float]],
    items: list[NotesPayable],
    layout: NotesLayout,
) -> None:
    fonts = _notes_fonts()
    pages = _page_count(len(items), layout.data_rows_per_page)
    for page_index in range(pages):
        start = page_index * layout.data_rows_per_page
        end = start + layout.data_rows_per_page
        chunk = items[start:end]
        baseline0: float | None = None
        for row_index, item in enumerate(chunk):
            center_y, baseline0 = _row_center(
                row_index,
                baseline0,
                layout=layout,
                balance_font=fonts['balance'],
            )
            _append_note_row(
                texts,
                rectangles,
                page_index=page_index,
                row_index=row_index,
                center_y=center_y,
                item=item,
                layout=layout,
                fonts=fonts,
            )
        _append_page_total(
            texts,
            page_index=page_index,
            chunk=chunk,
            baseline0=baseline0,
            layout=layout,
            fonts=fonts,
        )


def generate_uchiwakesyo_shiharaitegata(
    company_id: int | None,
    year: str = "2025",
    *,
    output_path: str,
) -> str:
    """
    支払手形の内訳書 PDF オーバレイを生成して output_path に書き込み、そのパスを返す。
    """
    company_id = _resolve_company_id(company_id)
    assets = prepare_pdf_assets(
        form_subdir="uchiwakesyo_shiharaitegata",
        geometry_key="uchiwakesyo_shiharaitegata",
        year=year,
    )

    texts: list[TextSpec] = []
    rectangles: list[tuple[int, float, float, float, float]] = []

    items = _collect_notes_payable(company_id)
    layout = _notes_layout(assets.geometry)
    _render_notes_payable(texts, rectangles, items, layout)

    return build_overlay(
        base_pdf_path=assets.base_pdf,
        output_pdf_path=output_path,
        texts=texts,
        rectangles=rectangles,
        font_registrations={"NotoSansJP": assets.font_map["NotoSansJP"]},
    )
