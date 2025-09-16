
from app.services.soa_registry import (
    PL_PAGE_ACCOUNTS,
    STATEMENT_PAGES_CONFIG,
    SUMMARY_PAGE_MAP,
)


def test_all_config_pages_exist_in_summary_map():
    missing = [page for page in STATEMENT_PAGES_CONFIG.keys() if page not in SUMMARY_PAGE_MAP]
    assert not missing, f"Pages missing in SUMMARY_PAGE_MAP: {missing}"


def test_pl_pages_have_accounts_mapping_or_are_special_case():
    # PLに分類されるページのうち、設定に存在するものを対象
    pl_pages = [page for page, (mtype, _) in SUMMARY_PAGE_MAP.items() if mtype == 'PL']
    targets = [p for p in pl_pages if p in STATEMENT_PAGES_CONFIG]
    # 'miscellaneous' はサービス層で特別扱い（雑収入+雑損失を合算）
    special_cases = {'miscellaneous'}
    missing = [p for p in targets if p not in PL_PAGE_ACCOUNTS and p not in special_cases]
    assert not missing, f"PL pages missing in PL_PAGE_ACCOUNTS: {missing}"
