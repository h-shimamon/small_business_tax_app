from __future__ import annotations

import os
from typing import Any

from flask import current_app, has_request_context, request
from flask_login import current_user

from app.company.models import AccountsPayable, Company
from app.extensions import db
from app.utils import format_number

from .fonts import default_font_map, ensure_font_registered
from .layout_utils import (
    append_left,
    append_right,
    baseline0_from_center,
    build_overlay,
    center_from_baseline,
    load_geometry,
)
from .pdf_fill import TextSpec


def _format_currency(n: int | None) -> str:
    return format_number(n)




def _resolve_company_id(company_id: int | None) -> int:
    if company_id is not None:
        return company_id
    if not has_request_context():
        raise RuntimeError("company_id is required outside a request context")
    company = Company.query.filter_by(user_id=current_user.id).first_or_404()
    return company.id


def _resolve_repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _load_geometry_context(template_key: str, year: str, repo_root: str) -> tuple[dict[str, Any], dict[str, float]]:
    geom = load_geometry(template_key, year, repo_root=repo_root, required=True, validate=True)
    defaults = {
        'row1_center': float(geom.get('row', {}).get('ROW1_CENTER', 773.0)),
        'row_step': float(geom.get('row', {}).get('ROW_STEP', 28.3)),
        'rows_per_page': int(geom.get('row', {}).get('DETAIL_ROWS_DATA', geom.get('row', {}).get('DETAIL_ROWS', 20))),
        'right_margin': float(geom.get('margins', {}).get('right_margin', 0.0)),
    }
    return geom, defaults


def _column_spec(cols: dict[str, Any], name: str) -> tuple[float, float]:
    col = cols.get(name, {})
    return float(col.get('x', 0.0)), float(col.get('w', 0.0))


def _collect_accounts_payable(company_id: int) -> list[AccountsPayable]:
    return (
        db.session.query(AccountsPayable)
        .filter_by(company_id=company_id)
        .order_by(AccountsPayable.balance_at_eoy.desc(), AccountsPayable.id.asc())
        .all()
    )


def _prepare_page_chunk(items: list[AccountsPayable], start: int, rows_per_page: int) -> list[AccountsPayable]:
    end = min(start + rows_per_page, len(items))
    return items[start:end]


def _append_row_texts(
    texts: list[TextSpec],
    rectangles: list[tuple[int, float, float, float, float]],
    page_index: int,
    row_index: int,
    item: AccountsPayable,
    centers: dict[str, float],
    col_specs: dict[str, tuple[float, float]],
    fonts: dict[str, float],
    right_margin: float,
) -> None:
    natural_center = centers['row1_center'] - centers['row_step'] * row_index
    baseline0 = centers.get('baseline0')
    if baseline0 is None:
        baseline0 = baseline0_from_center(natural_center, fonts['balance'])
        centers['baseline0'] = baseline0
        center_y = natural_center
    else:
        center_y = center_from_baseline(baseline0, centers['row_step'], row_index, fonts['balance'])

    def left(column: str, text: str, size_key: str) -> None:
        x, w = col_specs[column]
        append_left(texts, page=page_index, x=x, w=w, center_y=center_y, text=text, font_name="NotoSansJP", font_size=fonts[size_key])

    def right(column: str, text: str, size_key: str) -> None:
        x, w = col_specs[column]
        append_right(
            texts,
            page=page_index,
            x=x,
            w=w,
            center_y=center_y,
            text=text,
            font_name="NotoSansJP",
            font_size=fonts[size_key],
            right_margin=right_margin,
        )

    left('account', item.account_name or "", 'account')
    left('reg_no', getattr(item, 'registration_number', '') or '', 'reg_no')
    left('partner', item.partner_name or "", 'partner')
    left('address', item.partner_address or "", 'address')
    right('balance', _format_currency(item.balance_at_eoy), 'balance')
    left('remarks', item.remarks or "", 'remarks')

    if has_request_context() and request.args.get('debug_y') == '1':
        y_dbg = center_y - fonts['balance'] / 2.0
        rectangles.append((page_index, 50.0, y_dbg, 500.0, 0.6))
        try:
            current_app.logger.info(f"row_idx={row_index} y={y_dbg:.2f} size={fonts['balance']}")
        except Exception:
            pass


def _append_page_total(
    texts: list[TextSpec],
    page_index: int,
    rows_per_page: int,
    fonts: dict[str, float],
    centers: dict[str, float],
    col_specs: dict[str, tuple[float, float]],
    total_amount: int,
    right_margin: float,
) -> None:
    baseline0 = centers.get('baseline0', baseline0_from_center(centers['row1_center'], fonts['balance']))
    sum_center_y = center_from_baseline(baseline0, centers['row_step'], rows_per_page, fonts['balance'])
    x, w = col_specs['balance']
    append_right(
        texts,
        page=page_index,
        x=x,
        w=w,
        center_y=sum_center_y,
        text=_format_currency(total_amount),
        font_name="NotoSansJP",
        font_size=fonts['balance'],
        right_margin=right_margin,
    )

def generate_uchiwakesyo_kaikakekin(company_id: int | None, year: str = "2025", *, output_path: str) -> str:
    """買掛金（未払金・未払費用）内訳書 PDF を生成する。"""
    company_id = _resolve_company_id(company_id)
    repo_root = _resolve_repo_root()
    base_pdf = os.path.join(repo_root, f"resources/pdf_forms/uchiwakesyo_kaikakekin/{year}/source.pdf")
    font_map = default_font_map(repo_root)
    try:
        ensure_font_registered("NotoSansJP", font_map["NotoSansJP"])
    except Exception:
        pass

    geometry, defaults = _load_geometry_context("uchiwakesyo_kaikakekin", year, repo_root)
    cols = geometry.get('cols', {})
    col_specs = {
        'account': _column_spec(cols, 'account'),
        'reg_no': _column_spec(cols, 'reg_no'),
        'partner': _column_spec(cols, 'partner'),
        'address': _column_spec(cols, 'address'),
        'balance': _column_spec(cols, 'balance'),
        'remarks': _column_spec(cols, 'remarks'),
    }

    fonts = {
        'account': 9.0,
        'partner': 7.0,
        'reg_no': 9.0,
        'address': 7.0,
        'balance': 13.0,
        'remarks': 7.5,
    }

    items = _collect_accounts_payable(company_id)
    rows_per_page = defaults['rows_per_page']
    centers = {
        'row1_center': defaults['row1_center'],
        'row_step': defaults['row_step'],
    }

    texts: list[TextSpec] = []
    rectangles: list[tuple[int, float, float, float, float]] = []
    total_items = len(items)
    pages = (total_items + rows_per_page - 1) // rows_per_page if total_items else 1

    for page_index in range(pages):
        chunk = _prepare_page_chunk(items, page_index * rows_per_page, rows_per_page)
        for row_index, item in enumerate(chunk):
            _append_row_texts(
                texts,
                rectangles,
                page_index,
                row_index,
                item,
                centers,
                col_specs,
                fonts,
                defaults['right_margin'],
            )
        page_sum = sum(getattr(item, 'balance_at_eoy', 0) or 0 for item in chunk)
        _append_page_total(
            texts,
            page_index,
            rows_per_page,
            fonts,
            centers,
            col_specs,
            page_sum,
            defaults['right_margin'],
        )

    return build_overlay(
        base_pdf_path=base_pdf,
        output_pdf_path=output_path,
        texts=texts,
        rectangles=rectangles,
        font_registrations={"NotoSansJP": font_map["NotoSansJP"]},
    )
