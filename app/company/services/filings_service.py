from __future__ import annotations

from typing import Optional

from app.company.filings_registry import get_title, get_template, get_preview_pdf
from .protocols import FilingsServiceProtocol


class FilingsService(FilingsServiceProtocol):
    def get_title(self, page: str) -> Optional[str]:
        return get_title(page)

    def get_template(self, page: str) -> Optional[str]:
        return get_template(page)

    def get_preview_pdf(self, page: str) -> Optional[str]:
        return get_preview_pdf(page)
