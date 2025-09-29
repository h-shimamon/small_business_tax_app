from app.services.soa_registry import (
    STATEMENT_PAGES_CONFIG,
    SUMMARY_PAGE_MAP,
    PL_PAGE_ACCOUNTS,
)


def test_soa_registry_summary_alignment():
    # すべてのページが summary 情報を持ち、モデル・フォームの解決に成功していること
    for key, cfg in STATEMENT_PAGES_CONFIG.items():
        assert 'model' in cfg and cfg['model'] is not None
        assert 'form' in cfg and cfg['form'] is not None
        assert key in SUMMARY_PAGE_MAP
        summary = cfg.get('summary')
        assert isinstance(summary, dict)
        assert summary.get('type') in {'BS', 'PL'}
        assert isinstance(summary.get('label'), str) and summary['label']

    # PL ページのターゲットは配列で管理されていること
    for key, targets in PL_PAGE_ACCOUNTS.items():
        assert isinstance(targets, list)
        assert all(isinstance(t, str) and t for t in targets)
        assert key in STATEMENT_PAGES_CONFIG

    # 借入金は B/S 側として扱われ、PL の支払利息ターゲットを持つ
    summary_type, summary_label = SUMMARY_PAGE_MAP['borrowings']
    assert summary_type == 'BS'
    assert summary_label == '借入金'
    assert PL_PAGE_ACCOUNTS['borrowings'] == ['支払利息']
