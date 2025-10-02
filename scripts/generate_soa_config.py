#!/usr/bin/env python3
"""Generate resources/config/soa_pages.json from code metadata."""
from __future__ import annotations

import json
from pathlib import Path

from app.services.soa_registry import STATEMENT_PAGES_CONFIG


def main() -> None:
    pages = []
    for key, cfg in STATEMENT_PAGES_CONFIG.items():
        page = {
            'key': key,
            'model': f"{cfg['model'].__module__}.{cfg['model'].__name__}",
            'form': f"{cfg['form'].__module__}.{cfg['form'].__name__}",
            'title': cfg['title'],
            'total_field': cfg['total_field'],
            'template': cfg['template'],
            'summary': cfg['summary'],
        }
        if cfg.get('pl_targets'):
            page['pl_targets'] = cfg['pl_targets']
        if cfg.get('query_filter'):
            # query_filterは関数になっているため生成スクリプトでは未対応
            raise ValueError(f"query_filter is not supported in generator (page={key})")
        pages.append(page)

    output = {
        'pages': pages,
    }
    config_path = Path('resources/config/soa_pages.json')
    config_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Updated {config_path} (pages={len(pages)})")


if __name__ == '__main__':
    main()
