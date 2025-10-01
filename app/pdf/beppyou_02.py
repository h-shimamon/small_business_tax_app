from __future__ import annotations

import os
from flask import has_request_context
from flask_login import current_user
from reportlab.pdfbase import pdfmetrics
from sqlalchemy import func

import app.company.services.company_classification_service as company_classification_service
from app.company.models import Company, Shareholder
from app.company.services.shareholder_service import shareholder_service as shs
from app.extensions import db
from app.primitives import wareki as _w
from app.primitives.dates import get_company_period, to_iso

from .geom import get_row_metrics, merge_rects
from .pdf_fill import TextSpec
from .layout_utils import build_overlay, prepare_pdf_assets, baseline0_from_center


def _string_width(text: str, font_name: str, font_size: float) -> float:
    try:
        return pdfmetrics.stringWidth(text, font_name, font_size)
    except Exception:
        # Fallback to a safe heuristic when font is not registered yet
        return len(text) * font_size * 0.55


def _ellipsize(text: str, font_name: str, font_size: float, max_width: float) -> str:
    if _string_width(text, font_name, font_size) <= max_width:
        return text
    ell = "…"
    if _string_width(ell, font_name, font_size) > max_width:
        return ""
    out = []
    for ch in text:
        cand = "".join(out) + ch + ell
        if _string_width(cand, font_name, font_size) <= max_width:
            out.append(ch)
        else:
            break
    return "".join(out) + ell


def _fit_text(text: str, font_name: str, start_size: float, min_size: float, max_width: float) -> tuple[str, float]:
    size = start_size
    while size >= min_size:
        if _string_width(text, font_name, size) <= max_width:
            return text, size
        size -= 1.0
    # Ellipsize at min size
    return _ellipsize(text, font_name, min_size, max_width), min_size


def _vcenter_single(rect_y: float, rect_h: float, font_size: float) -> float:
    """Return baseline y to vertically center a single line within a rect."""
    return rect_y + (rect_h - font_size) / 2.0


def _vcenter_multiline(rect_y: float, rect_h: float, line_sizes: list[float], gap: float) -> list[float]:
    """Return baseline y positions (top to bottom) to center multiple lines within a rect.
    Uses simple line-height = font_size approximation.
    """
    if not line_sizes:
        return []
    total = sum(line_sizes) + gap * (len(line_sizes) - 1)
    top_y = rect_y + (rect_h + total) / 2.0
    ys: list[float] = []
    for sz in line_sizes:
        baseline = top_y - sz
        ys.append(baseline)
        top_y -= (sz + gap)
    return ys

def _baseline_center(center_y: float, font_size: float) -> float:
    """Baseline for a single line centered around a target center_y."""
    return center_y - font_size / 2.0

def _multiline_center(center_y: float, line_sizes: list[float], gap: float) -> list[float]:
    """Baselines for multiple lines centered around a target center_y (top to bottom)."""
    if not line_sizes:
        return []
    total = sum(line_sizes) + gap * (len(line_sizes) - 1)
    top_y = center_y + total / 2.0
    ys: list[float] = []
    for sz in line_sizes:
        baseline = top_y - sz
        ys.append(baseline)
        top_y -= (sz + gap)
    return ys


def _format_number(n: int | None) -> str:
    if n is None:
        return ""
    try:
        return f"{int(n):,}"
    except Exception:
        return ""


def _load_geometry(repo_root: str, year: str):
    """Load optional geometry constants from JSON; return dict or {} on failure.
    Adds schema validation (rects/cols) with safe defaults; silently falls back on error.
    """
    import json
    path = os.path.join(repo_root, f"resources/pdf_templates/beppyou_02/{year}_geometry.json")
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f) or {}
        # Try strict validation + defaults (rects-mode supported); ignore validation errors to keep behavior
        try:
            from . import geom_loader as _geom
            data = _geom.validate_and_apply_defaults(data)
        except Exception:
            pass
        return data
    except Exception:
        return {}


 


def _collect_rows(company_id: int, limit: int = 12) -> list[dict]:
    # すべての主たる株主を取得
    mains: list[Shareholder] = (
        Shareholder.query.filter_by(company_id=company_id, parent_id=None).order_by(Shareholder.id.asc()).all()
    )

    # 上位3グループに限定（議決権/出資金の合計で降順）
    try:
        totals_map = shs.compute_group_totals_map(company_id)
    except Exception:
        totals_map = {}
    if totals_map:
        mains = sorted(mains, key=lambda m: (totals_map.get(m.id, 0), -m.id), reverse=True)[:3]
    else:
        mains = mains[:3]

    rows: list[dict] = []
    group_num = 0
    for main in mains:
        group_num += 1
        # main row
        rows.append({
            "group": group_num,
            "person": main,
            "is_main": True,
            "relation": "本人",
            "main": main,
        })
        if len(rows) >= limit:
            break

        # related sorted by shares_held desc (None treated as 0)
        children = list(main.children or [])
        children.sort(key=lambda c: (c.shares_held or 0), reverse=True)
        for rel in children:
            rows.append({
                "group": group_num,
                "person": rel,
                "is_main": False,
                "relation": rel.relationship or "",
                "main": main,
            })
            if len(rows) >= limit:
                break

        if len(rows) >= limit:
            break

    return rows[:limit]


# ===== Header metrics/geometry (modularized, shares-based) =====
# Rects: (x0, y0, width, height) in points on page 0
RECT_TOTAL_SHARES = (250.66, 785.61, 50.00, 28.65)  # (1)
RECT_TOP3_SHARES = (251.33, 752.96, 49.33, 27.99)   # (2)
RECT_RATIO_RAW   = (251.33, 721.64, 47.33, 27.99)   # (3)
RECT_RATIO_PCT   = (247.99, 495.09, 50.00, 28.65)   # (4)

BOX_DOUZOKU      = (465.99, 519.08, 88.66, 12.66)   # (5)
BOX_HI_DOUZOKU   = (467.99, 506.42, 86.00, 12.66)   # (6)


def _right_edge(x0: float, y0: float, w: float, h: float) -> float:
    return x0 + w - 2.0


def _compute_total_shares(company_id: int) -> int:
    return int(db.session.query(func.sum(Shareholder.shares_held)).filter(
        Shareholder.company_id == company_id
    ).scalar() or 0)


def _compute_top3_shares(company_id: int) -> int:
    group_key = func.coalesce(Shareholder.parent_id, Shareholder.id)
    rows = db.session.query(group_key.label('gid'), func.sum(Shareholder.shares_held)).filter(
        Shareholder.company_id == company_id
    ).group_by('gid').all()
    totals = sorted([int(v or 0) for _, v in rows], reverse=True)
    return sum(totals[:3]) if totals else 0


# ===== Declaration header (dates/company) =====
# Period start/end (wareki) and company name
RECT_PERIOD_START = (329.32, 833.59, 64.66, 10.00)
RECT_PERIOD_END   = (329.32, 822.26, 62.00, 11.33)
RECT_COMPANY_NAME = (438.66, 822.93, 115.33, 20.66)

# New specific rects for period start split (era, YY, MM, DD)
RECT_START_ERA = (327.32, 834.26, 14.00, 13.33)
RECT_START_YY  = (340.66, 834.92, 8.67, 13.33)
RECT_START_MM  = (360.66, 834.92, 6.67, 13.33)
RECT_START_DD  = (383.99, 835.59, 10.67, 13.33)

# 和暦処理は app/utils/date_jp.py に集約（関数名の互換性維持のため import で別名化）


def _place_ymd_triplet(page: int, x0: float, y0: float, w: float, h: float, date_str: str | None, texts_list: list[TextSpec], *, font: str = "NotoSansJP", size: float = 8.0) -> None:
    parts = _w.numeric_parts(date_str)
    if not parts:
        return
    yy, mm, dd = parts
    # Baseline centered vertically
    y = _baseline_center(y0 + h / 2.0, size)
    # Widths
    _w_yy = _string_width(yy, font, size)
    w_mm = _string_width(mm, font, size)
    w_dd = _string_width(dd, font, size)
    # Positions
    x_yy = x0
    x_dd = x0 + w - w_dd - 2.0
    x_mm_center = (x_yy + x_dd) / 2.0
    x_mm = x_mm_center - (w_mm / 2.0)
    # Draw
    texts_list.append(TextSpec(page=page, x=x_yy, y=y, text=yy, font_name=font, font_size=size))
    texts_list.append(TextSpec(page=page, x=x_mm, y=y, text=mm, font_name=font, font_size=size))
    texts_list.append(TextSpec(page=page, x=x_dd, y=y, text=dd, font_name=font, font_size=size))


def _place_text_rect_left(page: int, x0: float, y0: float, w: float, h: float, text: str, texts_list: list[TextSpec], *, start_size: float = 10.0, min_size: float = 8.0, font: str = "NotoSansJP") -> None:
    if not text:
        return
    fit_text, used_size = _fit_text(text, font, start_size, min_size, w - 2.0)
    y = _baseline_center(y0 + h / 2.0, used_size)
    texts_list.append(TextSpec(page=page, x=x0, y=y, text=fit_text, font_name=font, font_size=used_size))


def _place_center_left_fit(page: int, x0: float, y0: float, w: float, h: float, text: str, texts_list: list[TextSpec], *, start_size: float = 8.0, min_size: float = 6.0, font: str = "NotoSansJP") -> None:
    if not text:
        return
    # No fitting: draw at requested size, allow overflow to the right if needed.
    used_size = start_size
    y = _baseline_center(y0 + h / 2.0, used_size)  # vertical center
    texts_list.append(TextSpec(page=page, x=x0, y=y, text=text, font_name=font, font_size=used_size))


def _place_center_right_fit(page: int, x0: float, y0: float, w: float, h: float, text: str, texts_list: list[TextSpec], *, start_size: float = 8.0, min_size: float = 6.0, font: str = "NotoSansJP") -> None:
    if not text:
        return
    # No fitting: draw at requested size; align right edge at x0+w, allow extending to the left if wider.
    used_size = start_size
    sw = _string_width(text, font, used_size)
    x = x0 + (w - sw)
    y = _baseline_center(y0 + h / 2.0, used_size)  # vertical center
    texts_list.append(TextSpec(page=page, x=x, y=y, text=text, font_name=font, font_size=used_size))


def _place_at_left(page: int, x: float, y: float, text: str, texts_list: list[TextSpec], *, size: float, font: str = "NotoSansJP") -> None:
    if not text:
        return
    texts_list.append(TextSpec(page=page, x=x, y=y, text=text, font_name=font, font_size=size))


def _place_at_right(page: int, x_right: float, y: float, text: str, texts_list: list[TextSpec], *, size: float, font: str = "NotoSansJP") -> None:
    if not text:
        return
    sw = _string_width(text, font, size)
    x = x_right - sw
    texts_list.append(TextSpec(page=page, x=x, y=y, text=text, font_name=font, font_size=size))

def _wrap_text_to_width(text: str, font_name: str, font_size: float, max_width: float) -> list[str]:
    lines: list[str] = []
    cur = ""
    for ch in text:
        if _string_width(cur + ch, font_name, font_size) <= max_width:
            cur += ch
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines

def _place_wrapped_text_rect_left(page: int, x0: float, y0: float, w: float, h: float, text: str, texts_list: list[TextSpec], *, start_size: float = 10.0, min_size: float = 8.0, line_gap: float = 0.0, font: str = "NotoSansJP") -> None:
    if not text:
        return
    max_w = w - 2.0
    size = start_size
    while size >= min_size:
        lines = _wrap_text_to_width(text, font, size, max_w)
        total_h = len(lines) * size + (len(lines) - 1) * line_gap if lines else 0
        if lines and total_h <= h:
            y_bases = _multiline_center(y0 + h / 2.0, [size] * len(lines), line_gap)
            for ln, yb in zip(lines, y_bases):
                texts_list.append(TextSpec(page=page, x=x0, y=yb, text=ln, font_name=font, font_size=size))
            return
        size -= 1.0
    # 最小サイズでも収まらない場合、行数制限して末尾を省略
    size = max(min_size, 1.0)
    lines = _wrap_text_to_width(text, font, size, max_w)
    if size > 0:
        max_lines = max(1, int(h // size))
    else:
        max_lines = 1
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = _ellipsize(lines[-1], font, size, max_w)
    y_bases = _multiline_center(y0 + h / 2.0, [size] * len(lines), line_gap)
    for ln, yb in zip(lines, y_bases):
        texts_list.append(TextSpec(page=page, x=x0, y=yb, text=ln, font_name=font, font_size=size))




def _resolve_company_id(company_id: int | None) -> int:
    if company_id is not None:
        return company_id
    if not has_request_context():
        raise RuntimeError("company_id is required outside a request context")
    company = Company.query.filter_by(user_id=current_user.id).first_or_404()
    return company.id


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def _load_geometry_overrides(repo_root: str, year: str) -> dict:
    overrides = _load_geometry(repo_root, year)
    rect_defaults = {
        "NUM_RECT": (64.00, 377.15, 16.66, 18.66),
        "ADDR_RECT": (106.00, 375.15, 100.66, 21.32),
        "NAME_RECT": (209.99, 374.48, 100.66, 21.99),
        "REL_RECT": (312.66, 374.48, 48.00, 21.99),
        "SHARES_RECT": (459.99, 374.48, 46.00, 22.66),
        "RECT_TOTAL_SHARES": RECT_TOTAL_SHARES,
        "RECT_TOP3_SHARES": RECT_TOP3_SHARES,
        "RECT_RATIO_RAW": RECT_RATIO_RAW,
        "RECT_RATIO_PCT": RECT_RATIO_PCT,
        "BOX_DOUZOKU": BOX_DOUZOKU,
        "BOX_HI_DOUZOKU": BOX_HI_DOUZOKU,
        "RECT_PERIOD_START": RECT_PERIOD_START,
        "RECT_PERIOD_END": RECT_PERIOD_END,
        "RECT_COMPANY_NAME": RECT_COMPANY_NAME,
        "RECT_START_ERA": RECT_START_ERA,
        "RECT_START_YY": RECT_START_YY,
        "RECT_START_MM": RECT_START_MM,
        "RECT_START_DD": RECT_START_DD,
    }
    rects = merge_rects(rect_defaults, overrides.get('rects', {}))
    metrics = get_row_metrics(overrides, default_row1_center=387.0, default_row_step=24.5, default_step_y=27.32, default_padding_x=2.0)
    return {"rects": rects, "metrics": metrics}


def _company_period(company: Company) -> tuple[str | None, str | None]:
    period = get_company_period(company)
    return to_iso(period.start), to_iso(period.end)


def _place_company_period(texts: list[TextSpec], company: Company, rects: dict[str, tuple[float, float, float, float]]):
    start_iso, end_iso = _company_period(company)
    y_base_start = rects["RECT_START_DD"][1]
    _place_at_left(0, rects["RECT_START_ERA"][0], y_base_start, _w.era_name(start_iso), texts, size=6.0)
    _place_at_right(0, rects["RECT_START_YY"][0] + rects["RECT_START_YY"][2], y_base_start, (_w.numeric_parts(start_iso) or ("", "", ""))[0], texts, size=9.0)
    _place_at_right(0, rects["RECT_START_MM"][0] + rects["RECT_START_MM"][2], y_base_start, (_w.numeric_parts(start_iso) or ("", "", ""))[1], texts, size=9.0)
    _place_at_right(0, rects["RECT_START_DD"][0] + rects["RECT_START_DD"][2] - 10.0, y_base_start, (_w.numeric_parts(start_iso) or ("", "", ""))[2], texts, size=9.0)

    y_base_end = rects["RECT_PERIOD_END"][1]
    _place_at_left(0, rects["RECT_START_ERA"][0], y_base_end, _w.era_name(end_iso), texts, size=6.0)
    _place_at_right(0, rects["RECT_START_YY"][0] + rects["RECT_START_YY"][2], y_base_end, (_w.numeric_parts(end_iso) or ("", "", ""))[0], texts, size=9.0)
    _place_at_right(0, rects["RECT_START_MM"][0] + rects["RECT_START_MM"][2], y_base_end, (_w.numeric_parts(end_iso) or ("", "", ""))[1], texts, size=9.0)
    _place_at_right(0, rects["RECT_START_DD"][0] + rects["RECT_START_DD"][2] - 10.0, y_base_end, (_w.numeric_parts(end_iso) or ("", "", ""))[2], texts, size=9.0)

    name_rect = rects["RECT_COMPANY_NAME"]
    _place_wrapped_text_rect_left(0, *name_rect, company.company_name or "", texts, start_size=8.0, min_size=7.0, line_gap=0.0)


def _place_totals(texts: list[TextSpec], rects: dict[str, tuple[float, float, float, float]], totals: dict[str, str]):
    common_right = min(_right_edge(*rects[name]) for name in ("RECT_TOTAL_SHARES", "RECT_TOP3_SHARES", "RECT_RATIO_RAW", "RECT_RATIO_PCT"))
    def _place(name: str, value: str):
        x0, y0, w, h = rects[name]
        sw = _string_width(value, "NotoSansJP", 10.0)
        x = common_right - sw
        y = _baseline_center(y0 + h / 2.0, 10.0)
        texts.append(TextSpec(page=0, x=x, y=y, text=value, font_name="NotoSansJP", font_size=10.0))
    _place("RECT_TOTAL_SHARES", totals["total"])
    _place("RECT_TOP3_SHARES", totals["top3"])
    _place("RECT_RATIO_RAW", totals["ratio_raw"])
    _place("RECT_RATIO_PCT", totals["ratio_pct"])


def _place_classification(rectangles: list[tuple[int, float, float, float, float]], rects: dict[str, tuple[float, float, float, float]], classification: str | None):
    if classification == '同族会社':
        rectangles.append((0, *rects["BOX_DOUZOKU"]))
    elif classification == '非同族会社':
        rectangles.append((0, *rects["BOX_HI_DOUZOKU"]))


def _compute_totals(company_id: int) -> dict[str, str]:
    total_shares = _compute_total_shares(company_id)
    top3_total = _compute_top3_shares(company_id)
    ratio_pct = round((top3_total / total_shares) * 100, 2) if total_shares else 0.0
    return {
        "total": f"{_format_number(total_shares)}株",
        "top3": f"{_format_number(top3_total)}株",
        "ratio_raw": f"{ratio_pct}",
        "ratio_pct": f"{ratio_pct}%",
    }

def generate_beppyou_02(company_id: int | None, year: str = "2025", *, output_path: str) -> str:
    company_id = _resolve_company_id(company_id)
    repo_root = _repo_root()
    assets = prepare_pdf_assets(
        form_subdir="beppyou_02",
        geometry_key="beppyou_02",
        year=year,
        repo_root=repo_root,
        ensure_font_name="NotoSansJP",
    )

    overrides = _load_geometry_overrides(repo_root, year)
    rects = overrides["rects"]
    metrics = overrides["metrics"]

    rows = _collect_rows(company_id, limit=12)
    texts: list[TextSpec] = []
    rectangles: list[tuple[int, float, float, float, float]] = []

    for idx, row in enumerate(rows):
        row_center = metrics["ROW1_CENTER"] - metrics["ROW_STEP"] * idx
        baseline0 = metrics.get("baseline0")
        if baseline0 is None:
            baseline0 = baseline0_from_center(row_center, 13.0)
            metrics["baseline0"] = baseline0

        gnum = str(row["group"]) if row.get("group") else ""
        gx, gy, gw, gh = rects["NUM_RECT"]
        gw -= metrics["PADDING_X"] * 2
        num_fit, num_size = _fit_text(gnum, "NotoSansJP", 10.0, 9.0, gw)
        num_x = gx + metrics["PADDING_X"]
        num_y = _baseline_center(row_center, num_size)
        texts.append(TextSpec(page=0, x=num_x, y=num_y, text=num_fit, font_name="NotoSansJP", font_size=num_size))

        person: Shareholder = row["person"]
        main: Shareholder = row["main"]

        # Address
        ax, ay, aw, ah = rects["ADDR_RECT"]
        ax += metrics["PADDING_X"]
        width_addr = aw - metrics["PADDING_X"] * 2
        if not row["is_main"] and shs.is_same_address(person, main):
            addr_lines = ["同上"]
        else:
            addr_lines = [person.prefecture_city or "", person.address or ""]
        addr_lines = [ln for ln in addr_lines if ln]
        if not addr_lines:
            addr_lines = [""]
        addr_font = "NotoSansJP"
        addr_sizes = []
        for ln in addr_lines:
            fit, size = _fit_text(ln, addr_font, 8.0, 7.0, width_addr)
            addr_sizes.append((fit, size))
        y_bases = _multiline_center(row_center, [sz for _, sz in addr_sizes], 2.0 if len(addr_sizes) > 1 else 0.0)
        for (text, size), yb in zip(addr_sizes, y_bases):
            texts.append(TextSpec(page=0, x=ax, y=yb, text=text, font_name=addr_font, font_size=size))

        # Name
        nx, ny, nw, nh = rects["NAME_RECT"]
        nx += metrics["PADDING_X"]
        name_fit, name_size = _fit_text(person.last_name or "", "NotoSansJP", 10.0, 8.0, nw - metrics["PADDING_X"] * 2)
        texts.append(TextSpec(page=0, x=nx, y=_baseline_center(row_center, name_size), text=name_fit, font_name="NotoSansJP", font_size=name_size))

        # Relation
        rel_text = row.get("relation") or ""
        if idx == 0 and row.get("is_main") and rel_text == "本人":
            rel_text = ""
        rx, ry, rw, rh = rects["REL_RECT"]
        rx += metrics["PADDING_X"]
        rel_fit, rel_size = _fit_text(rel_text, "NotoSansJP", 9.0, 8.0, rw - metrics["PADDING_X"] * 2)
        texts.append(TextSpec(page=0, x=rx, y=_baseline_center(row_center, rel_size), text=rel_fit, font_name="NotoSansJP", font_size=rel_size))

        # Shares
        sx, sy, sw, sh = rects["SHARES_RECT"]
        shares_text = _format_number(person.shares_held)
        shares_w = _string_width(shares_text, "NotoSansJP", 10.0)
        shares_x = sx + sw - shares_w - 2.0
        texts.append(TextSpec(page=0, x=shares_x, y=_baseline_center(row_center, 10.0), text=shares_text, font_name="NotoSansJP", font_size=10.0))

    # Header summary
    totals = _compute_totals(company_id)
    _place_totals(texts, rects, totals)

    try:
        classification = company_classification_service.classify_company(company_id)
        _place_classification(rectangles, rects, (classification or {}).get('classification'))
    except Exception:
        pass

    company = db.session.get(Company, company_id)
    if company:
        _place_company_period(texts, company, rects)

    return build_overlay(
        base_pdf_path=assets.base_pdf,
        output_pdf_path=output_path,
        texts=texts,
        rectangles=rectangles,
        font_registrations=assets.font_map,
    )
