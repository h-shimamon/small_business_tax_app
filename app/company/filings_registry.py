# app/company/filings_registry.py
"""
Single source of truth for filings pages.
- Maps page keys to: title, template(optional), preview_pdf(optional)
- Keeps routing and preview logic simple and consistent.
- UI is not changed by this module itself.
"""
from __future__ import annotations
from typing import Dict, Optional, TypedDict


class FilingPage(TypedDict, total=False):
    title: str
    template: str       # Jinja template path, if a dedicated template exists
    preview_pdf: str    # Relative path from repo root to a static PDF for preview


REGISTRY: Dict[str, FilingPage] = {
    # --- 別表・概況等（既存TITLE_MAPを移設） ---
    'beppyo_2': {'title': '別表2'},
    'beppyo_16_2': {'title': '別表16(2)'},
    'beppyo_15': {'title': '別表15'},
    'tax_payment_status_beppyo_5_2': {'title': '法人税等の納付状況（別表５(2))', 'template': 'company/filings/tax_payment_status_beppyo_5_2.html'},
    'beppyo_7': {'title': '別表７', 'template': 'company/filings/beppyo_7.html'},
    'corporate_tax_calculation': {'title': '法人税の計算', 'template': 'company/filings/corporate_tax_calculation.html'},
    'beppyo_4': {'title': '別表４', 'template': 'company/filings/beppyo_4.html'},
    'beppyo_5_1': {'title': '別表５(1)'},
    'appropriation_calc_beppyo_5_2': {'title': '納税充当金の計算（別表５(2))', 'template': 'company/filings/appropriation_calc_beppyo_5_2.html'},
    'local_tax_rates': {'title': '地方税税率登録'},
    # 事業概況説明書: 1のみ専用テンプレ/プレビューPDFを現時点で登録
    'business_overview_1': {
        'title': '事業概況説明書１',
        'template': 'company/filings/business_overview_1.html',
        'preview_pdf': 'resources/pdf_forms/jigyogaikyo/2025/source.pdf',
    },
    'business_overview_2': {'title': '事業概況説明書２', 'template': 'company/filings/business_overview_2.html', 'preview_pdf': 'resources/pdf_forms/jigyogaikyo/2025/source.pdf'},
    'business_overview_3': {'title': '事業概況説明書３'},
    'journal_entries_cit': {'title': '法人税等に関する仕訳の表示'},
    'financial_statements': {'title': '決算書'},
}


def get_page_entry(page_key: str) -> Optional[FilingPage]:
    """Return registry entry for the page key, or None if not found."""
    return REGISTRY.get(page_key)


def get_title(page_key: str) -> Optional[str]:
    """Return the title for the page key, or None if not registered."""
    entry = REGISTRY.get(page_key)
    return entry['title'] if entry else None


def get_template(page_key: str) -> Optional[str]:
    """Return the dedicated template path if registered."""
    entry = REGISTRY.get(page_key)
    return entry.get('template') if entry else None


def get_preview_pdf(page_key: str) -> Optional[str]:
    """Return the relative PDF path for preview if available."""
    entry = REGISTRY.get(page_key)
    return entry.get('preview_pdf') if entry else None


__all__ = [
    'FilingPage',
    'REGISTRY',
    'get_page_entry',
    'get_title',
    'get_template',
    'get_preview_pdf',
]
