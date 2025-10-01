from __future__ import annotations

from typing import Callable

from flask import current_app

from app.company.filings_registry import (
    FilingRegistryError,
    get_preview_pdf,
    get_template,
    get_title,
)

from .protocols import FilingsServiceProtocol


class FilingsService(FilingsServiceProtocol):
    def _lookup(self, func: Callable[[str, bool], str | None], page: str) -> str | None:
        try:
            return func(page, strict=True)
        except FilingRegistryError as exc:
            try:
                current_app.logger.warning("Unknown filings page requested: %s", exc.page_key)
            except RuntimeError:
                pass
            return None

    def get_title(self, page: str) -> str | None:
        return self._lookup(get_title, page)

    def get_template(self, page: str) -> str | None:
        return self._lookup(get_template, page)

    def get_preview_pdf(self, page: str) -> str | None:
        return self._lookup(get_preview_pdf, page)
