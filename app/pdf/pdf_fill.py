from __future__ import annotations

from dataclasses import dataclass
import os
from io import BytesIO
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import __init__  # noqa: F401  # ensure package is recognized


def _import_pypdf():
    try:
        import pypdf  # type: ignore
        from pypdf import PdfReader, PdfWriter
        return pypdf, PdfReader, PdfWriter
    except Exception as e:  # pragma: no cover - optional dep
        raise RuntimeError(
            "pypdf is required for PDF reading/writing. Please install it: pip install pypdf"
        ) from e


def _import_reportlab():
    try:
        from reportlab.pdfgen import canvas  # type: ignore
        from reportlab.lib.pagesizes import letter  # noqa: F401
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        return canvas, pdfmetrics, TTFont
    except Exception as e:  # pragma: no cover - optional dep
        raise RuntimeError(
            "reportlab is required for PDF overlay. Please install it: pip install reportlab"
        ) from e


def detect_acroform_fields(pdf_path: str) -> Dict[str, Any]:
    _, PdfReader, _ = _import_pypdf()
    reader = PdfReader(pdf_path)
    try:
        return reader.get_form_text_fields() or {}
    except Exception:
        return {}


def fill_acroform_fields(pdf_path: str, output_path: str, values: Dict[str, Any]) -> None:
    _, PdfReader, PdfWriter = _import_pypdf()
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    import logging
    log = logging.getLogger(__name__)
    for page in reader.pages:
        try:
            reader.update_page_form_field_values(page, values)
        except Exception as e:
            log.warning("Failed to update form field values on a page: %s", e)
        writer.add_page(page)

    try:
        writer.update_page_form_field_values(writer.pages[0], {})
    except Exception as e:
        log.warning("Failed to finalize form field values: %s", e)

    with open(output_path, "wb") as f:
        writer.write(f)


@dataclass
class GridSpec:
    page: int
    x0: float
    y0: float
    box_width: float
    box_count: int
    font_name: str = "Helvetica"
    font_size: float = 10.0
    y_offset: float = 0.0
    rtl: bool = True
    thousand_separators: bool = False
    fill_char: Optional[str] = None
    negative_mark: Optional[str] = None


@dataclass
class TextSpec:
    page: int
    x: float
    y: float
    text: str
    font_name: str = "Helvetica"
    font_size: float = 10.0
    align: str = "left"  # "left" or "right"


def _register_font_if_needed(font_name: str, font_path: Optional[str]) -> None:
    _, pdfmetrics, TTFont = _import_reportlab()
    if font_path and font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, font_path))


def _number_to_digits(value: int, *, thousand_separators: bool = False) -> Tuple[str, bool]:
    if value is None:
        return "", False
    neg = value < 0
    n = abs(int(value))
    if thousand_separators:
        return f"{n:,}", neg
    else:
        return str(n), neg


def overlay_pdf(
    base_pdf_path: str,
    output_pdf_path: str,
    texts: Iterable[TextSpec] = (),
    grids: Iterable[GridSpec] = (),
    rectangles: Iterable[Tuple[int, float, float, float, float]] = (),
    *,
    font_registrations: Optional[Dict[str, str]] = None,
) -> None:
    """Overlay texts/grids on a base PDF.

    Development-friendly: If base_pdf_path does not exist and it follows the
    pattern resources/pdf_forms/<template>/<year>/source.pdf, fall back to the
    latest available year or default/source.pdf under the same template dir.
    """
    # Resolve fallback for missing base PDF
    used_base = base_pdf_path
    if not os.path.exists(used_base):
        # Try to infer template dir and search siblings
        try:
            src_name = os.path.basename(used_base)
            year_dir = os.path.dirname(used_base)
            template_dir = os.path.dirname(year_dir)
            candidates: List[Tuple[int, str]] = []
            if src_name == 'source.pdf' and os.path.isdir(template_dir):
                for entry in os.listdir(template_dir):
                    full = os.path.join(template_dir, entry, 'source.pdf')
                    if os.path.exists(full):
                        if entry.isdigit():
                            try:
                                candidates.append((int(entry), full))
                            except Exception:
                                pass
                if candidates:
                    candidates.sort(key=lambda t: t[0], reverse=True)
                    used_base = candidates[0][1]
                else:
                    # default/source.pdf
                    default_path = os.path.join(template_dir, 'default', 'source.pdf')
                    if os.path.exists(default_path):
                        used_base = default_path
        except Exception:
            pass
    # If still missing, let pypdf raise a clear error

    pypdf, PdfReader, PdfWriter = _import_pypdf()
    canvas, pdfmetrics, TTFont = _import_reportlab()

    reader = PdfReader(used_base)
    writer = PdfWriter()

    texts_by_page: Dict[int, List[TextSpec]] = {}
    grids_by_page: Dict[int, List[GridSpec]] = {}
    rects_by_page: Dict[int, List[Tuple[float, float, float, float]]] = {}
    for t in texts:
        texts_by_page.setdefault(t.page, []).append(t)
    for g in grids:
        grids_by_page.setdefault(g.page, []).append(g)
    for r in rectangles:
        p, x, y, w, h = r
        rects_by_page.setdefault(p, []).append((x, y, w, h))

    font_registrations = font_registrations or {}
    for name, path in font_registrations.items():
        _register_font_if_needed(name, path)

    # Determine total pages to render (support repeating last base page for overflow)
    max_index = -1
    if texts_by_page:
        max_index = max(max_index, max(texts_by_page.keys()))
    if grids_by_page:
        max_index = max(max_index, max(grids_by_page.keys()))
    if rects_by_page:
        max_index = max(max_index, max(rects_by_page.keys()))
    total_pages = max(len(reader.pages), max_index + 1)

    for i in range(total_pages):
        base_idx = min(i, len(reader.pages) - 1)
        base_page = reader.pages[base_idx]

        media = base_page.mediabox
        width = float(media.width)
        height = float(media.height)

        # Create overlay canvas
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=(width, height))

        for spec in texts_by_page.get(i, []):
            c.setFont(spec.font_name, spec.font_size)
            if getattr(spec, 'align', 'left') == 'right':
                try:
                    c.drawRightString(spec.x, spec.y, spec.text)
                except Exception:
                    c.drawString(spec.x, spec.y, spec.text)
            else:
                c.drawString(spec.x, spec.y, spec.text)

        for gspec in grids_by_page.get(i, []):
            c.setFont(gspec.font_name, gspec.font_size)
            digits: str = getattr(gspec, 'digits', '')
            is_negative: bool = getattr(gspec, 'is_negative', False)

            x_cursor = gspec.x0
            if gspec.rtl:
                x_right = gspec.x0 + (gspec.box_width * (gspec.box_count - 1))
                x_cursor = x_right

            chars = list(digits)
            if gspec.rtl:
                chars = chars[::-1]

            if gspec.fill_char and len(chars) < gspec.box_count:
                pad_len = gspec.box_count - len(chars)
                chars.extend([gspec.fill_char] * pad_len)

            for ch in chars[: gspec.box_count]:
                c.drawString(x_cursor, gspec.y0 + gspec.y_offset, ch)
                x_cursor += (-gspec.box_width if gspec.rtl else gspec.box_width)

            if is_negative and gspec.negative_mark:
                mark_x = gspec.x0 - (gspec.box_width if gspec.rtl else 0) - 2
                c.drawString(mark_x, gspec.y0 + gspec.y_offset, gspec.negative_mark)

        # simple rectangle strokes
        for (rx, ry, rw, rh) in rects_by_page.get(i, []):
            c.setLineWidth(1)
            c.rect(rx, ry, rw, rh, stroke=1, fill=0)

        c.save()
        packet.seek(0)

        overlay_reader = PdfReader(packet)
        overlay_page = overlay_reader.pages[0]

        # Duplicate base page when needed by merging base onto a blank page first
        blank = pypdf.PageObject.create_blank_page(None, width, height)
        blank.merge_page(base_page)
        blank.merge_page(overlay_page)
        writer.add_page(blank)

    with open(output_pdf_path, 'wb') as f:
        writer.write(f)


def make_digits_for_grid(
    value: Optional[int],
    *,
    thousand_separators: bool = False,
) -> Tuple[str, bool]:
    if value is None:
        return "", False
    return _number_to_digits(value, thousand_separators=thousand_separators)


def overlay_with_template(
    base_pdf_path: str,
    output_pdf_path: str,
    template: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    fonts = template.get("fonts", {})
    font_registrations: Dict[str, str] = {}
    for fname, fpath in fonts.items():
        font_registrations[fname] = fpath

    dx = float(template.get("global_offset", {}).get("dx", 0.0))
    dy = float(template.get("global_offset", {}).get("dy", 0.0))

    # Optional: open PDF with PyMuPDF for anchor-based coordinate resolution
    fitz_doc = None
    def _ensure_fitz():
        nonlocal fitz_doc
        if fitz_doc is None:
            try:
                import fitz  # PyMuPDF
            except Exception as e:  # pragma: no cover
                raise RuntimeError(
                    "PyMuPDF (fitz) is required for anchor-based positioning. Install with: pip install PyMuPDF"
                ) from e
            fitz_doc = fitz.open(base_pdf_path)
        return fitz_doc

    def _resolve_anchor(item: Dict[str, Any]) -> Optional[Tuple[int, float, float]]:
        """
        Resolve anchor to overlay coordinates.
        Returns (page_index, x, y) in overlay coord system (origin bottom-left) or None if cannot resolve.
        """
        anchor = item.get("anchor")
        if not anchor:
            return None
        doc = _ensure_fitz()
        page_index = int(anchor.get("page", item.get("page", 0)))
        if page_index < 0 or page_index >= len(doc):
            return None
        page = doc[page_index]
        text = str(anchor.get("text", "")).strip()
        if not text:
            return None
        rects = page.search_for(text)
        if not rects:
            return None
        occ = max(1, int(anchor.get("occurrence", 1)))
        if occ > len(rects):
            occ = len(rects)
        r = rects[occ - 1]
        # PyMuPDF uses origin at top-left; overlay uses bottom-left
        page_height = float(page.rect.height)
        x_anchor = float(r.x0)
        y_anchor_overlay = page_height - float(r.y0)
        x = x_anchor + float(anchor.get("dx", 0.0)) + dx
        y = y_anchor_overlay + float(anchor.get("dy", 0.0)) + dy
        return page_index, x, y

    text_specs: List[TextSpec] = []
    for t in template.get("texts", []):
        txt = _resolve_value(t.get("text", ""), context)
        font_name = t.get("font", "Helvetica")
        font_size = float(t.get("size", 10))
        anchor_pos = _resolve_anchor(t)
        if anchor_pos is not None:
            page_index, x_res, y_res = anchor_pos
            text_specs.append(
                TextSpec(page=page_index, x=x_res, y=y_res, text=str(txt), font_name=font_name, font_size=font_size)
            )
        else:
            text_specs.append(
                TextSpec(page=int(t.get("page", 0)), x=float(t.get("x", 0.0)) + dx, y=float(t.get("y", 0.0)) + dy, text=str(txt), font_name=font_name, font_size=font_size)
            )

    grid_specs: List[GridSpec] = []
    for g in template.get("grids", []):
        val_raw = _resolve_value(g.get("value"), context)
        try:
            val_int = int(val_raw) if val_raw is not None and str(val_raw) != "" else None
        except Exception:
            val_int = None
        digits, is_neg = make_digits_for_grid(val_int, thousand_separators=bool(g.get("thousand_separators", False)))
        anchor_pos = _resolve_anchor(g)
        if anchor_pos is not None:
            page_index, x_res, y_res = anchor_pos
            x0_val = x_res
            y0_val = y_res
            page_val = page_index
        else:
            x0_val = float(g.get("x0", 0.0)) + dx
            y0_val = float(g.get("y0", 0.0)) + dy
            page_val = int(g.get("page", 0))

        spec = GridSpec(
            page=page_val,
            x0=x0_val,
            y0=y0_val,
            box_width=float(g["box_width"]),
            box_count=int(g["box_count"]),
            font_name=g.get("font", "Helvetica"),
            font_size=float(g.get("size", 10)),
            y_offset=float(g.get("y_offset", 0.0)),
            rtl=bool(g.get("rtl", True)),
            thousand_separators=bool(g.get("thousand_separators", False)),
            fill_char=g.get("fill_char"),
            negative_mark=g.get("neg_mark"),
        )
        setattr(spec, "digits", digits)
        setattr(spec, "is_negative", is_neg)
        grid_specs.append(spec)

    overlay_pdf(
        base_pdf_path,
        output_pdf_path,
        texts=text_specs,
        grids=grid_specs,
        font_registrations=font_registrations,
    )


def _resolve_value(expr: Any, ctx: Dict[str, Any]) -> Any:
    if expr is None:
        return None
    if isinstance(expr, (int, float)):
        return expr
    s = str(expr).strip()
    if s.startswith("{{") and s.endswith("}}"):  # mustache-ish
        path = s[2:-2].strip()
        return _dig(ctx, path)
    return expr


def _dig(obj: Any, path: str) -> Any:
    parts = [p for p in path.split(".") if p]
    cur = obj
    for p in parts:
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            cur = getattr(cur, p, None)
        if cur is None:
            break
    return cur
