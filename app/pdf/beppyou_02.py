from __future__ import annotations

from typing import List, Tuple, Optional, Dict
import os

from flask_login import current_user
from flask import has_request_context
from app.company.models import Company, Shareholder
from app.company.services import shareholder_service as shs
from app.primitives.dates import get_company_period, to_iso

from reportlab.pdfbase import pdfmetrics

from .pdf_fill import overlay_pdf, TextSpec
from sqlalchemy import func
from app import db
from app.company.services import company_classification_service
from app.primitives import wareki as _w
from .geom import merge_rects, get_row_metrics


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


def _fit_text(text: str, font_name: str, start_size: float, min_size: float, max_width: float) -> Tuple[str, float]:
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


def _vcenter_multiline(rect_y: float, rect_h: float, line_sizes: List[float], gap: float) -> List[float]:
    """Return baseline y positions (top to bottom) to center multiple lines within a rect.
    Uses simple line-height = font_size approximation.
    """
    if not line_sizes:
        return []
    total = sum(line_sizes) + gap * (len(line_sizes) - 1)
    top_y = rect_y + (rect_h + total) / 2.0
    ys: List[float] = []
    for sz in line_sizes:
        baseline = top_y - sz
        ys.append(baseline)
        top_y -= (sz + gap)
    return ys

def _baseline_center(center_y: float, font_size: float) -> float:
    """Baseline for a single line centered around a target center_y."""
    return center_y - font_size / 2.0

def _multiline_center(center_y: float, line_sizes: List[float], gap: float) -> List[float]:
    """Baselines for multiple lines centered around a target center_y (top to bottom)."""
    if not line_sizes:
        return []
    total = sum(line_sizes) + gap * (len(line_sizes) - 1)
    top_y = center_y + total / 2.0
    ys: List[float] = []
    for sz in line_sizes:
        baseline = top_y - sz
        ys.append(baseline)
        top_y -= (sz + gap)
    return ys


def _format_number(n: Optional[int]) -> str:
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
        with open(path, 'r', encoding='utf-8') as f:
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


 


def _collect_rows(company_id: int, limit: int = 12) -> List[Dict]:
    # すべての主たる株主を取得
    mains: List[Shareholder] = (
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

    rows: List[Dict] = []
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
        if children:
            rel = children[0]
            rows.append({
                "group": group_num,
                "person": rel,
                "is_main": False,
                "relation": rel.relationship or "",
                "main": main,
            })
        else:
            # next group's main will occupy this row per spec; handled by loop naturally
            pass
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


def _place_ymd_triplet(page: int, x0: float, y0: float, w: float, h: float, date_str: Optional[str], texts_list: List[TextSpec], *, font: str = "NotoSansJP", size: float = 8.0) -> None:
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


def _place_text_rect_left(page: int, x0: float, y0: float, w: float, h: float, text: str, texts_list: List[TextSpec], *, start_size: float = 10.0, min_size: float = 8.0, font: str = "NotoSansJP") -> None:
    if not text:
        return
    fit_text, used_size = _fit_text(text, font, start_size, min_size, w - 2.0)
    y = _baseline_center(y0 + h / 2.0, used_size)
    texts_list.append(TextSpec(page=page, x=x0, y=y, text=fit_text, font_name=font, font_size=used_size))


def _place_center_left_fit(page: int, x0: float, y0: float, w: float, h: float, text: str, texts_list: List[TextSpec], *, start_size: float = 8.0, min_size: float = 6.0, font: str = "NotoSansJP") -> None:
    if not text:
        return
    # No fitting: draw at requested size, allow overflow to the right if needed.
    used_size = start_size
    y = _baseline_center(y0 + h / 2.0, used_size)  # vertical center
    texts_list.append(TextSpec(page=page, x=x0, y=y, text=text, font_name=font, font_size=used_size))


def _place_center_right_fit(page: int, x0: float, y0: float, w: float, h: float, text: str, texts_list: List[TextSpec], *, start_size: float = 8.0, min_size: float = 6.0, font: str = "NotoSansJP") -> None:
    if not text:
        return
    # No fitting: draw at requested size; align right edge at x0+w, allow extending to the left if wider.
    used_size = start_size
    sw = _string_width(text, font, used_size)
    x = x0 + (w - sw)
    y = _baseline_center(y0 + h / 2.0, used_size)  # vertical center
    texts_list.append(TextSpec(page=page, x=x, y=y, text=text, font_name=font, font_size=used_size))


def _place_at_left(page: int, x: float, y: float, text: str, texts_list: List[TextSpec], *, size: float, font: str = "NotoSansJP") -> None:
    if not text:
        return
    texts_list.append(TextSpec(page=page, x=x, y=y, text=text, font_name=font, font_size=size))


def _place_at_right(page: int, x_right: float, y: float, text: str, texts_list: List[TextSpec], *, size: float, font: str = "NotoSansJP") -> None:
    if not text:
        return
    sw = _string_width(text, font, size)
    x = x_right - sw
    texts_list.append(TextSpec(page=page, x=x, y=y, text=text, font_name=font, font_size=size))

def _wrap_text_to_width(text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
    lines: List[str] = []
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

def _place_wrapped_text_rect_left(page: int, x0: float, y0: float, w: float, h: float, text: str, texts_list: List[TextSpec], *, start_size: float = 10.0, min_size: float = 8.0, line_gap: float = 0.0, font: str = "NotoSansJP") -> None:
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


def generate_beppyou_02(company_id: Optional[int], year: str = "2025", *, output_path: str) -> str:
    """
    Generate 'beppyou_02' PDF overlay for the given company (current_user tenant).
    Writes to output_path and returns it.
    """
    if company_id is None:
        if not has_request_context():
            raise RuntimeError("company_id is required outside a request context")
        company = Company.query.filter_by(user_id=current_user.id).first_or_404()
        company_id = company.id

    # Resolve project root based on this file location: app/pdf/ -> project root
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    base_pdf = os.path.join(repo_root, f"resources/pdf_forms/beppyou_02/{year}/source.pdf")
    font_map = {"NotoSansJP": os.path.join(repo_root, "resources/fonts/NotoSansJP-Regular.ttf")}

    # Optional external geometry override (non-functional change; defaults preserved)
    _geom = _load_geometry(repo_root, year)

    # Geometry (row/spacing metrics)
    metrics = get_row_metrics(_geom, default_row1_center=387.0, default_row_step=24.5, default_step_y=27.32, default_padding_x=2.0)
    STEP_Y = metrics["STEP_Y"]
    PADDING_X = metrics["PADDING_X"]
    ROW1_CENTER = metrics["ROW1_CENTER"]
    ROW_STEP = metrics["ROW_STEP"]

    # Rects: (x0, y0, width, height) — merge overrides safely
    rect_defaults = {
        "NUM_RECT": (64.00, 377.15, 16.66, 18.66),
        "ADDR_RECT": (106.00, 375.15, 100.66, 21.32),
        "NAME_RECT": (209.99, 374.48, 100.66, 21.99),
        "REL_RECT": (312.66, 374.48, 48.00, 21.99),
        "SHARES_RECT": (459.99, 374.48, 46.00, 22.66),
        # header metrics
        "RECT_TOTAL_SHARES": RECT_TOTAL_SHARES,
        "RECT_TOP3_SHARES": RECT_TOP3_SHARES,
        "RECT_RATIO_RAW": RECT_RATIO_RAW,
        "RECT_RATIO_PCT": RECT_RATIO_PCT,
        # classification boxes
        "BOX_DOUZOKU": BOX_DOUZOKU,
        "BOX_HI_DOUZOKU": BOX_HI_DOUZOKU,
        # period/company rects
        "RECT_PERIOD_START": RECT_PERIOD_START,
        "RECT_PERIOD_END": RECT_PERIOD_END,
        "RECT_COMPANY_NAME": RECT_COMPANY_NAME,
        "RECT_START_ERA": RECT_START_ERA,
        "RECT_START_YY": RECT_START_YY,
        "RECT_START_MM": RECT_START_MM,
        "RECT_START_DD": RECT_START_DD,
    }
    rects_overridden = merge_rects(rect_defaults, _geom.get('rects', {}))

    NUM_RECT = rects_overridden["NUM_RECT"]
    ADDR_RECT = rects_overridden["ADDR_RECT"]
    NAME_RECT = rects_overridden["NAME_RECT"]
    REL_RECT = rects_overridden["REL_RECT"]
    SHARES_RECT = rects_overridden["SHARES_RECT"]

    rect_total_shares = rects_overridden["RECT_TOTAL_SHARES"]
    rect_top3_shares = rects_overridden["RECT_TOP3_SHARES"]
    rect_ratio_raw = rects_overridden["RECT_RATIO_RAW"]
    rect_ratio_pct = rects_overridden["RECT_RATIO_PCT"]

    box_douzoku = rects_overridden["BOX_DOUZOKU"]
    box_hi_douzoku = rects_overridden["BOX_HI_DOUZOKU"]

    _rect_period_start = rects_overridden["RECT_PERIOD_START"]
    rect_period_end = rects_overridden["RECT_PERIOD_END"]
    rect_company_name = rects_overridden["RECT_COMPANY_NAME"]
    rect_start_era = rects_overridden["RECT_START_ERA"]
    rect_start_yy = rects_overridden["RECT_START_YY"]
    rect_start_mm = rects_overridden["RECT_START_MM"]
    rect_start_dd = rects_overridden["RECT_START_DD"]
    rows = _collect_rows(company_id, limit=12)

    texts: List[TextSpec] = []
    rectangles: List[Tuple[int, float, float, float, float]] = []

    for idx, row in enumerate(rows):
        _y_shift = STEP_Y * idx
        # Compute this row's center line (shared across columns)
        row_center = ROW1_CENTER - ROW_STEP * idx

        # group number centered (single-line around row_center)
        gx, gy, gw, gh = NUM_RECT
        gnum = str(row["group"]) if row.get("group") is not None else ""
        num_font = "NotoSansJP"
        num_size = 10
        num_w = _string_width(gnum, num_font, num_size)
        num_x = gx + (gw - num_w) / 2.0
        num_y = _baseline_center(row_center, num_size)
        texts.append(TextSpec(page=0, x=num_x, y=num_y, text=gnum, font_name=num_font, font_size=num_size))

        person: Shareholder = row["person"]
        main: Shareholder = row["main"]

        # address two lines
        ax, ay, aw, ah = ADDR_RECT
        ax += PADDING_X
        addr_font = "NotoSansJP"
        addr_start = 8.0  # start 8pt (−1pt from previous)
        addr_min = 7.0    # allow down to 7pt
        if not row["is_main"] and shs.is_same_address(person, main):
            line1 = "同上"
            line2 = ""
        else:
            line1 = person.prefecture_city or ""
            line2 = person.address or ""
        line1_fit, line1_size = _fit_text(line1, addr_font, addr_start, addr_min, aw - PADDING_X * 2)
        line2_fit, line2_size = _fit_text(line2, addr_font, addr_start, addr_min, aw - PADDING_X * 2)
        # Vertical placement within rect: compute centered baselines for one or two lines
        lines: List[Tuple[str, float]] = []
        if line1_fit:
            lines.append((line1_fit, line1_size))
        if line2_fit:
            lines.append((line2_fit, line2_size))
        # If same address ("同上") or single line, center that line; if two lines, center block with small gap
        gap = 2.0 if len(lines) > 1 else 0.0
        y_bases = _multiline_center(row_center, [sz for _, sz in lines], gap)

        # name (shrink if needed)
        nx, ny, nw, nh = NAME_RECT
        nx += PADDING_X
        name_font = "NotoSansJP"
        name_start = 10.0
        name_min = 8.0
        name_text = person.last_name or ""
        name_fit, name_size = _fit_text(name_text, name_font, name_start, name_min, nw - PADDING_X * 2)
        # center name around row_center
        name_y = _baseline_center(row_center, name_size)
        texts.append(TextSpec(page=0, x=nx, y=name_y, text=name_fit, font_name=name_font, font_size=name_size))

        # now append address lines centered
        if lines:
            # Map baselines back to respective lines (top to bottom)
            for (txt, sz), yb in zip(lines, y_bases):
                texts.append(TextSpec(page=0, x=ax, y=yb, text=txt, font_name=addr_font, font_size=sz))


        # relation (for main -> 本人)
        rx, ry, rw, rh = REL_RECT
        rx += PADDING_X
        rel_font = "NotoSansJP"
        rel_size = 9.0
        rel_text = row.get("relation") or ""
        # first row only: suppress "本人" (pre-printed on the form)
        if idx == 0 and row.get("is_main") and rel_text == "本人":
            rel_text = ""
        rel_fit, rel_size = _fit_text(rel_text, rel_font, rel_size, 8.0, rw - PADDING_X * 2)
        rel_y = _baseline_center(row_center, rel_size)
        texts.append(TextSpec(page=0, x=rx, y=rel_y, text=rel_fit, font_name=rel_font, font_size=rel_size))

        # shares (right aligned, comma separated)
        sx, sy, sw, sh = SHARES_RECT
        shares_font = "NotoSansJP"
        shares_size = 10.0
        shares_text = _format_number(person.shares_held)
        shares_w = _string_width(shares_text, shares_font, shares_size)
        shares_x = sx + sw - shares_w - 2.0
        shares_y = _baseline_center(row_center, shares_size)
        texts.append(TextSpec(page=0, x=shares_x, y=shares_y, text=shares_text, font_name=shares_font, font_size=shares_size))

    # ---- Header totals and classification boxes ----
    total_shares = _compute_total_shares(company_id)
    top3_total = _compute_top3_shares(company_id)
    ratio = (top3_total / total_shares) if total_shares else 0.0
    ratio_pct = round(ratio * 100, 2)

    # Helpers to place number within a rect (right aligned, vertically centered)
    def _place_number_rect(page: int, x0: float, y0: float, w: float, h: float, value: str, *, font="Helvetica", size=10.0, right_edge: Optional[float] = None):
        sw = _string_width(value, font, size)
        if right_edge is not None:
            x = right_edge - sw
        else:
            x = x0 + (w - sw) - 2.0
        y = _baseline_center(y0 + h / 2.0, size)
        texts.append(TextSpec(page=page, x=x, y=y, text=value, font_name=font, font_size=size))

    # Coordinates provided in 1-based page notation; our pages are 0-indexed
    p = 0
    # Precompute a shared right edge (to keep all within their rects, use the minimum right edge among the four)
    rects = [rect_total_shares, rect_top3_shares, rect_ratio_raw, rect_ratio_pct]
    right_edges = [_right_edge(*r) for r in rects]
    common_right = min(right_edges)  # 最小の右端に合わせてはみ出し防止

    # (1) total shares with unit
    _place_number_rect(p, *rect_total_shares, f"{_format_number(total_shares)}株", right_edge=common_right, font="NotoSansJP")
    # (2) top3 total with unit
    _place_number_rect(p, *rect_top3_shares, f"{_format_number(top3_total)}株", right_edge=common_right, font="NotoSansJP")
    # (3) raw ratio number (no %)
    _place_number_rect(p, *rect_ratio_raw, f"{ratio_pct}", right_edge=common_right, font="NotoSansJP")
    # (4) percent with %
    _place_number_rect(p, *rect_ratio_pct, f"{ratio_pct}%", right_edge=common_right, font="NotoSansJP")

    # (5)(6) classification boxes (stroke only)
    try:
        classification = company_classification_service.classify_company(company_id)
        cls = (classification or {}).get('classification')
    except Exception:
        cls = None
    if cls == '同族会社':
        rectangles.append((p, *box_douzoku))
    elif cls == '非同族会社':
        rectangles.append((p, *box_hi_douzoku))

    # --- Period (wareki) and company name ---
    company = db.session.get(Company, company_id)
    if company:
        # 会計期間 開始: era/YY/MM/DD を分割し、それぞれ指定矩形に下寄せ配置
        period = get_company_period(company)
        iso_start = to_iso(period.start)
        era = _w.era_name(iso_start)
        parts = _w.numeric_parts(iso_start) or ("", "", "")
        yy, mm, dd = parts
        # Era 6pt (left), YY/MM/DD 9pt (right), all bottom-aligned to DD's baseline (y of RECT_START_DD)
        y_base = rect_start_dd[1]
        # Left align era at its x0
        _place_at_left(p, rect_start_era[0], y_base, era, texts, size=6.0)
        # Right align YY/MM/DD at their x-right = x0 + w
        _place_at_right(p, rect_start_yy[0] + rect_start_yy[2], y_base, yy, texts, size=9.0)
        _place_at_right(p, rect_start_mm[0] + rect_start_mm[2], y_base, mm, texts, size=9.0)
        _place_at_right(p, rect_start_dd[0] + rect_start_dd[2] - 10.0, y_base, dd, texts, size=9.0)

        # 会計期間 終了: 開始の設定を踏襲して分割配置（矩形幅は無視）
        iso_end = to_iso(period.end)
        era_e = _w.era_name(iso_end)
        yy_e, mm_e, dd_e = _w.numeric_parts(iso_end) or ("", "", "")
        y_base_e = rect_period_end[1]  # 終了DDのy座標を基準（下揃え）
        # X軸は開始と同一座標を使用
        _place_at_left(p, rect_start_era[0], y_base_e, era_e, texts, size=6.0)
        _place_at_right(p, rect_start_yy[0] + rect_start_yy[2], y_base_e, yy_e, texts, size=9.0)
        _place_at_right(p, rect_start_mm[0] + rect_start_mm[2], y_base_e, mm_e, texts, size=9.0)
        # DDは開始のXに合わせ、開始と同様の-10pt補正を適用
        _place_at_right(p, rect_start_dd[0] + rect_start_dd[2] - 10.0, y_base_e, dd_e, texts, size=9.0)
        name_text = company.company_name or ""
        # 法人名はフォント-2pt（start 8pt / min 7pt）、上下中央寄せ・折返し
        _place_wrapped_text_rect_left(p, *rect_company_name, name_text, texts, start_size=8.0, min_size=7.0, line_gap=0.0)

    overlay_pdf(
        base_pdf_path=base_pdf,
        output_pdf_path=output_path,
        texts=texts,
        grids=[],
        rectangles=rectangles,
        font_registrations=font_map,
    )

    return output_path
