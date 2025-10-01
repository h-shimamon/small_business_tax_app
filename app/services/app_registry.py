"""Central registries for navigation, PDF exports, CTA messages, and reusable constants."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

from app.services.soa_registry import STATEMENT_PAGES_CONFIG


class NavigationNodeDef(TypedDict, total=False):
    key: str
    name: str
    node_type: str
    endpoint: str
    params: dict[str, str]
    children: list[NavigationNodeDef]


class PDFExportEntry(TypedDict, total=False):
    endpoint: str
    label: str
    page_key: str


@dataclass(frozen=True)
class StatementCTAConfig:
    header_label: str
    header_class: str
    add_label: str
    add_class: str
    back_label: str
    back_class: str

    def __post_init__(self) -> None:
        missing = [
            name
            for name, value in (
                ('header_label', self.header_label),
                ('header_class', self.header_class),
                ('add_label', self.add_label),
                ('add_class', self.add_class),
                ('back_label', self.back_label),
                ('back_class', self.back_class),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"CTA config missing required values: {', '.join(missing)}")


class StatementEmptyState(TypedDict, total=False):
    headline: str
    description: str
    action_label: str






SOA_NAV_ORDER: list[tuple[str, str]] = [
    ("deposits", "deposits"),
    ("notes_receivable", "notes_receivable"),
    ("accounts_receivable", "accounts_receivable"),
    ("temporary_payments", "temporary_payments"),
    ("loans_receivable", "loans_receivable"),
    ("inventories", "inventories"),
    ("securities", "securities"),
    ("fixed_assets_soa", "fixed_assets"),
    ("notes_payable", "notes_payable"),
    ("accounts_payable", "accounts_payable"),
    ("temporary_receipts", "temporary_receipts"),
    ("borrowings", "borrowings"),
    ("executive_compensations", "executive_compensations"),
    ("land_rents", "land_rents"),
    ("misc_income", "misc_income"),
    ("misc_losses", "misc_losses"),
]

PDF_EXPORT_PAGES: tuple[str, ...] = (
    "deposits",
    "accounts_receivable",
    "notes_receivable",
    "temporary_payments",
    "loans_receivable",
    "notes_payable",
    "accounts_payable",
    "borrowings",
)

DEFAULT_PDF_YEAR = "2025"

def _build_soa_children() -> list[NavigationNodeDef]:
    children: list[NavigationNodeDef] = []
    for nav_key, page_key in SOA_NAV_ORDER:
        config = STATEMENT_PAGES_CONFIG.get(page_key)
        if not config:
            continue
        children.append({
            "key": nav_key,
            "name": config["title"],
            "endpoint": "company.statement_of_accounts",
            "params": {"page": page_key},
        })
    return children

NAVIGATION_STRUCTURE_DATA: list[NavigationNodeDef] = [
    {
        "key": "company_info_group",
        "name": "基本情報登録",
        "node_type": "menu",
        "children": [
            {"key": "company_info", "name": "基本情報", "endpoint": "company.info"},
            {"key": "shareholders", "name": "株主/社員情報", "endpoint": "company.shareholders"},
            {"key": "declaration", "name": "申告情報", "endpoint": "company.declaration"},
            {"key": "office_list", "name": "事業所一覧", "endpoint": "company.office_list"},
        ],
    },
    {
        "key": "import_data_group",
        "name": "会計データ選択",
        "node_type": "wizard",
        "children": [
            {"key": "select_software", "name": "会計ソフト選択", "endpoint": "company.select_software"},
            {"key": "journals", "name": "仕訳帳データ取込", "endpoint": "company.upload_data", "params": {"datatype": "journals"}},
            {"key": "data_mapping", "name": "勘定科目マッピング", "endpoint": "company.data_mapping"},
            {"key": "confirm_trial_balance", "name": "残高試算表の確認", "endpoint": "company.confirm_trial_balance"},
        ],
    },
    {
        "key": "fixed_assets_group",
        "name": "固定資産台帳",
        "node_type": "menu",
        "children": [
            {"key": "fixed_assets_import", "name": "固定資産データ取込", "endpoint": "company.fixed_assets_import"},
            {"key": "fixed_assets_ledger", "name": "固定資産台帳", "endpoint": "company.fixed_assets_ledger"},
            {"key": "small_assets", "name": "少額資産明細", "endpoint": "company.small_assets_list"},
        ],
    },
    {
        "key": "statement_of_accounts_group",
        "name": "勘定科目内訳書",
        "node_type": "menu",
        "children": _build_soa_children(),
    },
    {
        "key": "filings_group",
        "name": "申告書",
        "node_type": "menu",
        "children": [
            {"key": "beppyo_15", "name": "別表15", "endpoint": "company.filings", "params": {"page": "beppyo_15"}},
            {"key": "business_overview_1", "name": "事業概況説明書１", "endpoint": "company.filings", "params": {"page": "business_overview_1"}},
            {"key": "business_overview_2", "name": "事業概況説明書２", "endpoint": "company.filings", "params": {"page": "business_overview_2"}},
            {"key": "business_overview_3", "name": "事業概況説明書３", "endpoint": "company.filings", "params": {"page": "business_overview_3"}},
            {"key": "tax_payment_status_beppyo_5_2", "name": "法人税等の納付状況（別表５(2))", "endpoint": "company.filings", "params": {"page": "tax_payment_status_beppyo_5_2"}},
            {"key": "beppyo_7", "name": "別表７", "endpoint": "company.filings", "params": {"page": "beppyo_7"}},
                        {"key": "corporate_tax_calc", "name": "法人税の計算", "endpoint": "company.filings", "params": {"page": "corporate_tax_calculation"}},
            {"key": "beppyo_4", "name": "別表４", "endpoint": "company.filings", "params": {"page": "beppyo_4"}},
            {"key": "beppyo_5_1", "name": "利益積立金額の計算（別表５(1)）", "endpoint": "company.filings", "params": {"page": "beppyo_5_1"}},
            {"key": "capital_calc_beppyo_5_1", "name": "資本金等の額の計算（別表５(1)）", "endpoint": "company.filings", "params": {"page": "capital_calc_beppyo_5_1"}},

            {"key": "appropriation_calc_beppyo_5_2", "name": "納税充当金の計算（別表５(2))", "endpoint": "company.filings", "params": {"page": "appropriation_calc_beppyo_5_2"}},
            {"key": "local_tax_rates", "name": "地方税税率登録", "endpoint": "company.filings", "params": {"page": "local_tax_rates"}},
            {"key": "journal_entries_cit", "name": "法人税等に関する仕訳の表示", "endpoint": "company.filings", "params": {"page": "journal_entries_cit"}},
            {"key": "financial_statements", "name": "決算書", "endpoint": "company.filings", "params": {"page": "financial_statements"}},
        ],
    },
]


PDF_EXPORTS: dict[str, PDFExportEntry] = {
    page_key: {
        "endpoint": "company.statement_pdf",
        "label": STATEMENT_PAGES_CONFIG[page_key]["title"],
        "page_key": page_key,
    }
    for page_key in PDF_EXPORT_PAGES
    if page_key in STATEMENT_PAGES_CONFIG
}

STATEMENT_POST_CREATE_CTA: dict[str, StatementCTAConfig] = {
    "default": StatementCTAConfig(
        header_label="＋ 新規登録",
        header_class="button-primary",
        add_label="続けて{title}を登録",
        add_class="button-primary",
        back_label="一覧へ戻る",
        back_class="button-secondary",
    )
}

STATEMENT_EMPTY_STATE: dict[str, StatementEmptyState] = {
    "default": {
        "headline": "最初の{title}情報を登録しましょう。",
        "description": "右上の「＋ 新規登録」ボタンから登録を開始してください。",
        "action_label": "最初の{title}を登録する",
    }
}


def get_navigation_structure() -> list[NavigationNodeDef]:
    """Return the raw navigation structure definition."""
    return NAVIGATION_STRUCTURE_DATA


def get_pdf_export_map() -> dict[str, PDFExportEntry]:
    """Return mapping of statement page key to PDF export configuration."""
    return PDF_EXPORTS


def get_pdf_export(page: str) -> PDFExportEntry | None:
    return PDF_EXPORTS.get(page)


def get_post_create_cta(page: str) -> StatementCTAConfig:
    return STATEMENT_POST_CREATE_CTA.get(page, STATEMENT_POST_CREATE_CTA["default"])


def get_empty_state(page: str) -> StatementEmptyState:
    return STATEMENT_EMPTY_STATE.get(page, STATEMENT_EMPTY_STATE["default"])


def get_default_pdf_year() -> str:
    return DEFAULT_PDF_YEAR
