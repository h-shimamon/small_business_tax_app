"""Central registry for filings pages and their presentation metadata."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal, cast

FilingPageKey = Literal[
    'beppyo_2',
    'beppyo_16_2',
    'beppyo_15',
    'tax_payment_status_beppyo_5_2',
    'beppyo_7',
    'corporate_tax_calculation',
    'beppyo_4',
    'beppyo_5_1',
    'capital_calc_beppyo_5_1',
    'appropriation_calc_beppyo_5_2',
    'local_tax_rates',
    'business_overview_1',
    'business_overview_2',
    'business_overview_3',
    'journal_entries_cit',
    'financial_statements',
]


@dataclass(frozen=True, slots=True)
class FilingPage:
    """Immutable metadata for a filings page."""

    title: str
    template: str | None = None
    preview_pdf: str | None = None


class FilingRegistryError(KeyError):
    """Raised when an unknown filings page key is requested."""

    def __init__(self, page_key: str):
        self.page_key = page_key
        super().__init__(page_key)

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return f"Unknown filings page key: {self.page_key}"


_REGISTRY: dict[FilingPageKey, FilingPage] = {
    'beppyo_2': FilingPage(title='別表2'),
    'beppyo_16_2': FilingPage(title='別表16(2)'),
    'beppyo_15': FilingPage(
        title='別表15',
        template='company/filings/beppyo_15.html',
        preview_pdf='resources/pdf_forms/beppyou_15/2025/source.pdf',
    ),
    'tax_payment_status_beppyo_5_2': FilingPage(
        title='法人税等の納付状況（別表５(2))',
        template='company/filings/tax_payment_status_beppyo_5_2.html',
    ),
    'beppyo_7': FilingPage(title='別表７', template='company/filings/beppyo_7.html'),
    'corporate_tax_calculation': FilingPage(
        title='法人税の計算',
        template='company/filings/corporate_tax_calculation.html',
    ),
    'beppyo_4': FilingPage(title='別表４', template='company/filings/beppyo_4.html'),
    'beppyo_5_1': FilingPage(
        title='利益積立金額の計算（別表５(1)）',
        template='company/filings/beppyo_5_1.html',
    ),
    'capital_calc_beppyo_5_1': FilingPage(
        title='資本金等の額の計算（別表５(1)）',
        template='company/filings/capital_calc_beppyo_5_1.html',
    ),
    'appropriation_calc_beppyo_5_2': FilingPage(
        title='納税充当金の計算（別表５(2))',
        template='company/filings/appropriation_calc_beppyo_5_2.html',
    ),
    'local_tax_rates': FilingPage(title='地方税税率登録'),
    'business_overview_1': FilingPage(
        title='事業概況説明書１',
        template='company/filings/business_overview_1.html',
        preview_pdf='resources/pdf_forms/jigyogaikyo/2025/source.pdf',
    ),
    'business_overview_2': FilingPage(
        title='事業概況説明書２',
        template='company/filings/business_overview_2.html',
        preview_pdf='resources/pdf_forms/jigyogaikyo/2025/source.pdf',
    ),
    'business_overview_3': FilingPage(title='事業概況説明書３'),
    'journal_entries_cit': FilingPage(title='法人税等に関する仕訳の表示'),
    'financial_statements': FilingPage(title='決算書'),
}

REGISTRY: Mapping[FilingPageKey, FilingPage] = MappingProxyType(_REGISTRY)


def _coerce_key(page_key: str) -> FilingPageKey:
    if page_key in _REGISTRY:
        return cast(FilingPageKey, page_key)
    raise FilingRegistryError(page_key)


def get_page_entry(page_key: str, *, strict: bool = False) -> FilingPage | None:
    """Look up filings metadata for a page.

    When ``strict`` is True, :class:`FilingRegistryError` is raised on unknown keys.
    Otherwise ``None`` is returned to preserve legacy behaviour.
    """

    try:
        key = _coerce_key(page_key)
    except FilingRegistryError:
        if strict:
            raise
        return None
    return _REGISTRY[key]


def require_page_entry(page_key: str) -> FilingPage:
    """Return filings metadata or raise :class:`FilingRegistryError` if missing."""

    return _REGISTRY[_coerce_key(page_key)]


def get_title(page_key: str, *, strict: bool = False) -> str | None:
    entry = get_page_entry(page_key, strict=strict)
    return entry.title if entry else None


def get_template(page_key: str, *, strict: bool = False) -> str | None:
    entry = get_page_entry(page_key, strict=strict)
    return entry.template if entry else None


def get_preview_pdf(page_key: str, *, strict: bool = False) -> str | None:
    entry = get_page_entry(page_key, strict=strict)
    return entry.preview_pdf if entry else None


__all__ = [
    'FilingPage',
    'FilingPageKey',
    'FilingRegistryError',
    'REGISTRY',
    'get_page_entry',
    'get_title',
    'get_template',
    'get_preview_pdf',
    'require_page_entry',
]
