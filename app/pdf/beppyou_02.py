from __future__ import annotations

from typing import List, Tuple, Optional, Dict
import os

from flask_login import current_user
from flask import has_request_context
from app.company.models import Company, Shareholder
from app.company.services import shareholder_service as shs

from reportlab.pdfbase import pdfmetrics

from .pdf_fill import overlay_pdf, TextSpec


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


def _same_address(a: Shareholder, b: Shareholder) -> bool:
    return (a.zip_code or "") == (b.zip_code or "") and (a.prefecture_city or "") == (b.prefecture_city or "") and (a.address or "") == (b.address or "")


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

    # Geometry constants (row 1 baseline rects), and vertical step
    STEP_Y = 27.32
    PADDING_X = 2.0
    # Rects: (x0, y0, width, height)
    NUM_RECT = (64.00, 377.15, 16.66, 18.66)
    ADDR_RECT = (106.00, 375.15, 100.66, 21.32)
    NAME_RECT = (209.99, 374.48, 100.66, 21.99)
    REL_RECT = (312.66, 374.48, 48.00, 21.99)
    SHARES_RECT = (459.99, 374.48, 46.00, 22.66)

    rows = _collect_rows(company_id, limit=12)

    # Row center-line specification (pt): row1=386, each subsequent row −26pt
    ROW1_CENTER = 387.0
    ROW_STEP = 24.5

    texts: List[TextSpec] = []

    for idx, row in enumerate(rows):
        y_shift = STEP_Y * idx
        # Compute this row's center line (shared across columns)
        row_center = ROW1_CENTER - ROW_STEP * idx

        # group number centered (single-line around row_center)
        gx, gy, gw, gh = NUM_RECT
        gnum = str(row["group"]) if row.get("group") is not None else ""
        num_font = "Helvetica"
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
        if not row["is_main"] and _same_address(person, main):
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
        shares_font = "Helvetica"
        shares_size = 10.0
        shares_text = _format_number(person.shares_held)
        shares_w = _string_width(shares_text, shares_font, shares_size)
        shares_x = sx + sw - shares_w - 2.0
        shares_y = _baseline_center(row_center, shares_size)
        texts.append(TextSpec(page=0, x=shares_x, y=shares_y, text=shares_text, font_name=shares_font, font_size=shares_size))

    overlay_pdf(
        base_pdf_path=base_pdf,
        output_pdf_path=output_path,
        texts=texts,
        grids=[],
        font_registrations=font_map,
    )

    return output_path
