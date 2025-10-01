from __future__ import annotations

from app.company.filings_registry import get_preview_pdf, get_template, get_title

from .protocols import FilingsServiceProtocol


class FilingsService(FilingsServiceProtocol):
    def get_title(self, page: str) -> str | None:
        return get_title(page)

    def get_template(self, page: str) -> str | None:
        return get_template(page)

    def get_preview_pdf(self, page: str) -> str | None:
        return get_preview_pdf(page)
