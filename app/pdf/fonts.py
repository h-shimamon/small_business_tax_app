from __future__ import annotations

import os
from reportlab.pdfbase import pdfmetrics


def default_font_map(repo_root: str) -> dict[str, str]:
    return {
        "NotoSansJP": os.path.join(repo_root, "resources/fonts/NotoSansJP-Regular.ttf"),
    }


def ensure_font_registered(name: str, path: str) -> None:
    try:
        from reportlab.pdfbase.ttfonts import TTFont  # type: ignore
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, path))
    except Exception:
        # Leave registration best-effort; calling code may still attempt to draw strings
        pass

