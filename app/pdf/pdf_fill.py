from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from . import __init__ as _package_init  # noqa: F401  # ensure package is recognized


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
        from reportlab.lib.pagesizes import letter  # noqa: F401
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas  # type: ignore
        return canvas, pdfmetrics, TTFont
    except Exception as e:  # pragma: no cover - optional dep
        raise RuntimeError(
            "reportlab is required for PDF overlay. Please install it: pip install reportlab"
        ) from e


def detect_acroform_fields(pdf_path: str) -> dict[str, Any]:
    _, PdfReader, _ = _import_pypdf()
    reader = PdfReader(pdf_path)
    try:
        return reader.get_form_text_fields() or {}
    except Exception:
        return {}


def fill_acroform_fields(pdf_path: str, output_path: str, values: dict[str, Any]) -> None:
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
    fill_char: str | None = None
    negative_mark: str | None = None


@dataclass
class TextSpec:
    page: int
    x: float
    y: float
    text: str
    font_name: str = "Helvetica"
    font_size: float = 10.0
    align: str = "left"  # "left" or "right"


def _register_font_if_needed(font_name: str, font_path: str | None) -> None:
    _, pdfmetrics, TTFont = _import_reportlab()
    if font_path and font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, font_path))


def _number_to_digits(value: int, *, thousand_separators: bool = False) -> tuple[str, bool]:
    if value is None:
        return "", False
    neg = value < 0
    n = abs(int(value))
    if thousand_separators:
        return f"{n:,}", neg
    else:
        return str(n), neg




def _resolve_base_pdf_path(base_pdf_path: str) -> str:
    if os.path.exists(base_pdf_path):
        return base_pdf_path
    used_base = base_pdf_path
    try:
        src_name = os.path.basename(base_pdf_path)
        year_dir = os.path.dirname(base_pdf_path)
        template_dir = os.path.dirname(year_dir)
        if src_name == 'source.pdf' and os.path.isdir(template_dir):
            candidates: list[tuple[int, str]] = []
            for entry in os.listdir(template_dir):
                candidate = os.path.join(template_dir, entry, 'source.pdf')
                if not os.path.exists(candidate):
                    continue
                if entry.isdigit():
                    try:
                        candidates.append((int(entry), candidate))
                    except ValueError:
                        continue
            if candidates:
                candidates.sort(key=lambda item: item[0], reverse=True)
                return candidates[0][1]
            fallback = os.path.join(template_dir, 'default', 'source.pdf')
            if os.path.exists(fallback):
                return fallback
    except Exception:
        return used_base
    return used_base


def _collect_overlay_specs(
    texts: Iterable[TextSpec],
    grids: Iterable[GridSpec],
    rectangles: Iterable[tuple[int, float, float, float, float]],
) -> tuple[
    dict[int, list[TextSpec]],
    dict[int, list[GridSpec]],
    dict[int, list[tuple[float, float, float, float]]],
]:
    texts_by_page: dict[int, list[TextSpec]] = {}
    for spec in texts:
        texts_by_page.setdefault(spec.page, []).append(spec)
    grids_by_page: dict[int, list[GridSpec]] = {}
    for spec in grids:
        grids_by_page.setdefault(spec.page, []).append(spec)
    rects_by_page: dict[int, list[tuple[float, float, float, float]]] = {}
    for page, x, y, width, height in rectangles:
        rects_by_page.setdefault(page, []).append((x, y, width, height))
    return texts_by_page, grids_by_page, rects_by_page


def _determine_total_pages(
    reader,
    texts_by_page: dict[int, list[TextSpec]],
    grids_by_page: dict[int, list[GridSpec]],
    rects_by_page: dict[int, list[tuple[float, float, float, float]]],
) -> int:
    max_index = -1
    if texts_by_page:
        max_index = max(max_index, max(texts_by_page))
    if grids_by_page:
        max_index = max(max_index, max(grids_by_page))
    if rects_by_page:
        max_index = max(max_index, max(rects_by_page))
    if max_index < 0:
        return len(reader.pages)
    return max(len(reader.pages), max_index + 1)


def _draw_texts(canvas_obj, specs: list[TextSpec]) -> None:
    for spec in specs:
        canvas_obj.setFont(spec.font_name, spec.font_size)
        if getattr(spec, 'align', 'left') == 'right':
            try:
                canvas_obj.drawRightString(spec.x, spec.y, spec.text)
            except Exception:
                canvas_obj.drawString(spec.x, spec.y, spec.text)
        else:
            canvas_obj.drawString(spec.x, spec.y, spec.text)


def _draw_grids(canvas_obj, specs: list[GridSpec]) -> None:
    for spec in specs:
        canvas_obj.setFont(spec.font_name, spec.font_size)
        digits: str = getattr(spec, 'digits', '')
        is_negative: bool = getattr(spec, 'is_negative', False)
        characters = list(digits)
        if spec.rtl:
            characters = characters[::-1]
        if spec.fill_char and len(characters) < spec.box_count:
            characters.extend([spec.fill_char] * (spec.box_count - len(characters)))
        step = -spec.box_width if spec.rtl else spec.box_width
        if spec.rtl:
            cursor = spec.x0 + (spec.box_width * (spec.box_count - 1))
        else:
            cursor = spec.x0
        for ch in characters[: spec.box_count]:
            canvas_obj.drawString(cursor, spec.y0 + spec.y_offset, ch)
            cursor += step
        if is_negative and spec.negative_mark:
            mark_x = spec.x0 - (spec.box_width if spec.rtl else 0) - 2
            canvas_obj.drawString(mark_x, spec.y0 + spec.y_offset, spec.negative_mark)


def _draw_rectangles(canvas_obj, specs: list[tuple[float, float, float, float]]) -> None:
    if not specs:
        return
    canvas_obj.setLineWidth(1)
    for x, y, width, height in specs:
        canvas_obj.rect(x, y, width, height, stroke=1, fill=0)


def _build_page_with_overlay(
    pypdf_module,
    canvas_module,
    pdf_reader_cls,
    base_page,
    page_index: int,
    texts_by_page: dict[int, list[TextSpec]],
    grids_by_page: dict[int, list[GridSpec]],
    rects_by_page: dict[int, list[tuple[float, float, float, float]]],
):
    media_box = base_page.mediabox
    width = float(media_box.width)
    height = float(media_box.height)
    packet = BytesIO()
    canvas_obj = canvas_module.Canvas(packet, pagesize=(width, height))
    _draw_texts(canvas_obj, texts_by_page.get(page_index, []))
    _draw_grids(canvas_obj, grids_by_page.get(page_index, []))
    _draw_rectangles(canvas_obj, rects_by_page.get(page_index, []))
    canvas_obj.save()
    packet.seek(0)
    overlay_reader = pdf_reader_cls(packet)
    overlay_page = overlay_reader.pages[0]
    merged = pypdf_module.PageObject.create_blank_page(None, width, height)
    merged.merge_page(base_page)
    merged.merge_page(overlay_page)
    return merged


def _register_fonts(font_registrations: dict[str, str] | None) -> None:
    if not font_registrations:
        return
    for name, path in font_registrations.items():
        _register_font_if_needed(name, path)


def _is_development_env() -> bool:
    try:
        return os.getenv('APP_ENV', 'development').lower() != 'production'
    except Exception:
        return False


def _log_base_pdf_usage(used_base: str) -> None:
    if not _is_development_env():
        return
    try:
        print(f"[pdf_fill] base_pdf used: {used_base}")
    except Exception:
        pass


def _log_overlay_counts(
    texts_by_page: dict[int, list[TextSpec]],
    grids_by_page: dict[int, list[GridSpec]],
    used_base: str,
) -> None:
    if not _is_development_env():
        return
    try:
        text_count = sum(len(items) for items in texts_by_page.values())
        grid_count = sum(len(items) for items in grids_by_page.values())
        if text_count == 0 and grid_count == 0:
            print(f"[pdf_fill] warning: no overlay content (texts=0, grids=0) for base={used_base}")
        else:
            print(f"[pdf_fill] overlay counts: texts={text_count}, grids={grid_count}")
    except Exception:
        pass

def overlay_pdf(
    base_pdf_path: str,
    output_pdf_path: str,
    texts: Iterable[TextSpec] = (),
    grids: Iterable[GridSpec] = (),
    rectangles: Iterable[tuple[int, float, float, float, float]] = (),
    *,
    font_registrations: dict[str, str] | None = None,
) -> None:
    """Overlay texts/grids on a base PDF.

    Development-friendly: If base_pdf_path does not exist and it follows the
    pattern resources/pdf_forms/<template>/<year>/source.pdf, fall back to the
    latest available year or default/source.pdf under the same template dir.
    """
    used_base = _resolve_base_pdf_path(base_pdf_path)
    pypdf_module, PdfReader, PdfWriter = _import_pypdf()
    canvas_module, _, _ = _import_reportlab()

    texts_by_page, grids_by_page, rects_by_page = _collect_overlay_specs(texts, grids, rectangles)
    _register_fonts(font_registrations)
    _log_base_pdf_usage(used_base)

    reader = PdfReader(used_base)
    writer = PdfWriter()
    total_pages = _determine_total_pages(reader, texts_by_page, grids_by_page, rects_by_page)

    for page_index in range(total_pages):
        base_idx = min(page_index, len(reader.pages) - 1)
        base_page = reader.pages[base_idx]
        merged_page = _build_page_with_overlay(
            pypdf_module,
            canvas_module,
            PdfReader,
            base_page,
            page_index,
            texts_by_page,
            grids_by_page,
            rects_by_page,
        )
        writer.add_page(merged_page)

    _log_overlay_counts(texts_by_page, grids_by_page, used_base)

    with open(output_pdf_path, 'wb') as f:
        writer.write(f)


def make_digits_for_grid(
    value: int | None,
    *,
    thousand_separators: bool = False,
) -> tuple[str, bool]:
    if value is None:
        return "", False
    return _number_to_digits(value, thousand_separators=thousand_separators)




class _AnchorResolver:
    def __init__(self, base_pdf_path: str, dx: float, dy: float) -> None:
        self._base_pdf_path = base_pdf_path
        self._dx = dx
        self._dy = dy
        self._doc = None

    def resolve(self, item: dict[str, Any]) -> tuple[int, float, float] | None:
        anchor = item.get("anchor")
        if not anchor:
            return None
        doc = self._ensure_document()
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
        occurrence = max(1, int(anchor.get("occurrence", 1)))
        if occurrence > len(rects):
            occurrence = len(rects)
        target_rect = rects[occurrence - 1]
        page_height = float(page.rect.height)
        x_anchor = float(target_rect.x0)
        y_anchor_overlay = page_height - float(target_rect.y0)
        x = x_anchor + float(anchor.get("dx", 0.0)) + self._dx
        y = y_anchor_overlay + float(anchor.get("dy", 0.0)) + self._dy
        return page_index, x, y

    def _ensure_document(self):
        if self._doc is None:
            try:
                import fitz  # PyMuPDF
            except Exception as exc:  # pragma: no cover
                raise RuntimeError(
                    "PyMuPDF (fitz) is required for anchor-based positioning. Install with: pip install PyMuPDF"
                ) from exc
            self._doc = fitz.open(self._base_pdf_path)
        return self._doc


def _extract_font_registrations(template: dict[str, Any]) -> dict[str, str]:
    fonts = template.get("fonts", {})
    return {name: path for name, path in fonts.items()}


def _resolve_offsets(template: dict[str, Any]) -> tuple[float, float]:
    global_offset = template.get("global_offset", {})
    dx = float(global_offset.get("dx", 0.0))
    dy = float(global_offset.get("dy", 0.0))
    return dx, dy


def _build_text_specs(
    template: dict[str, Any],
    context: dict[str, Any],
    resolver: _AnchorResolver,
    dx: float,
    dy: float,
) -> list[TextSpec]:
    specs: list[TextSpec] = []
    for config in template.get("texts", []):
        text_value = _resolve_value(config.get("text", ""), context)
        font_name = config.get("font", "Helvetica")
        font_size = float(config.get("size", 10))
        anchor = resolver.resolve(config)
        if anchor is not None:
            page_index, x_pos, y_pos = anchor
        else:
            page_index = int(config.get("page", 0))
            x_pos = float(config.get("x", 0.0)) + dx
            y_pos = float(config.get("y", 0.0)) + dy
        specs.append(
            TextSpec(
                page=page_index,
                x=x_pos,
                y=y_pos,
                text=str(text_value),
                font_name=font_name,
                font_size=font_size,
            )
        )
    return specs


def _build_grid_specs(
    template: dict[str, Any],
    context: dict[str, Any],
    resolver: _AnchorResolver,
    dx: float,
    dy: float,
) -> list[GridSpec]:
    specs: list[GridSpec] = []
    for config in template.get("grids", []):
        raw_value = _resolve_value(config.get("value"), context)
        try:
            normalized_value = int(raw_value) if raw_value is not None and str(raw_value) != "" else None
        except Exception:
            normalized_value = None
        digits, is_negative = make_digits_for_grid(
            normalized_value,
            thousand_separators=bool(config.get("thousand_separators", False)),
        )
        anchor = resolver.resolve(config)
        if anchor is not None:
            page_index, x0, y0 = anchor
        else:
            page_index = int(config.get("page", 0))
            x0 = float(config.get("x0", 0.0)) + dx
            y0 = float(config.get("y0", 0.0)) + dy
        spec = GridSpec(
            page=page_index,
            x0=x0,
            y0=y0,
            box_width=float(config["box_width"]),
            box_count=int(config["box_count"]),
            font_name=config.get("font", "Helvetica"),
            font_size=float(config.get("size", 10)),
            y_offset=float(config.get("y_offset", 0.0)),
            rtl=bool(config.get("rtl", True)),
            thousand_separators=bool(config.get("thousand_separators", False)),
            fill_char=config.get("fill_char"),
            negative_mark=config.get("neg_mark"),
        )
        spec.digits = digits
        spec.is_negative = is_negative
        specs.append(spec)
    return specs

def overlay_with_template(
    base_pdf_path: str,
    output_pdf_path: str,
    template: dict[str, Any],
    context: dict[str, Any],
) -> None:
    dx, dy = _resolve_offsets(template)
    font_registrations = _extract_font_registrations(template)
    resolver = _AnchorResolver(base_pdf_path, dx, dy)

    text_specs = _build_text_specs(template, context, resolver, dx, dy)
    grid_specs = _build_grid_specs(template, context, resolver, dx, dy)

    overlay_pdf(
        base_pdf_path,
        output_pdf_path,
        texts=text_specs,
        grids=grid_specs,
        font_registrations=font_registrations,
    )


def _resolve_value(expr: Any, ctx: dict[str, Any]) -> Any:
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
