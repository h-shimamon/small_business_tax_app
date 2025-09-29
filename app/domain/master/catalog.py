from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.company.services.master_data_service import MasterDataService


@dataclass(frozen=True)
class AccountCatalog:
    """勘定科目マスタと同義語辞書をカプセル化する。"""

    canonical_names: Set[str]
    aliases: Dict[str, str]
    normalized_lookup: Dict[str, str]
    bs_accounts: List[str]
    pl_accounts: List[str]

    def normalize(self, value: str) -> str:
        return _normalize(value)

    def resolve(self, value: str) -> Optional[str]:
        key = self.normalize(value)
        return self.aliases.get(key) or self.normalized_lookup.get(key)


def load_catalog(master_service: Optional[MasterDataService] = None) -> AccountCatalog:
    master_service = master_service or MasterDataService()

    try:
        bs_df = master_service.get_bs_master_df()
    except (SQLAlchemyError, Exception):
        bs_df = None
    try:
        pl_df = master_service.get_pl_master_df()
    except (SQLAlchemyError, Exception):
        pl_df = None

    bs_accounts = _extract_account_names(bs_df)
    pl_accounts = _extract_account_names(pl_df)
    canonical_names = set(bs_accounts) | set(pl_accounts)

    aliases = _load_alias_map(canonical_names)
    if not canonical_names and aliases:
        canonical_names = set(aliases.values())

    normalized_lookup = {_normalize(name): name for name in canonical_names}

    return AccountCatalog(
        canonical_names=canonical_names,
        aliases=aliases,
        normalized_lookup=normalized_lookup,
        bs_accounts=bs_accounts,
        pl_accounts=pl_accounts,
    )


def _extract_account_names(df) -> List[str]:
    if df is None:
        return []
    try:
        if hasattr(df, 'index') and getattr(df.index, 'name', None) == 'name':
            return [str(idx) for idx in df.index.tolist() if idx]
        if 'name' in df.columns:
            return [str(value) for value in df['name'].tolist() if value]
    except Exception:
        return []
    return []


def _load_alias_map(canonical_names: Iterable[str]) -> Dict[str, str]:
    try:
        app = current_app._get_current_object()
        cfg = app.config
        default_root = Path(app.root_path).parent
    except RuntimeError:
        cfg = {}
        default_root = Path('.')

    base_dir = cfg.get('MASTER_DATA_BASE_DIR')
    candidates: List[Path] = []
    if base_dir:
        candidates.append(Path(base_dir) / 'resources' / 'masters' / 'account_aliases.json')
    candidates.append(default_root / 'resources' / 'masters' / 'account_aliases.json')

    alias_map: Dict[str, str] = {}
    for path in candidates:
        if path.exists():
            try:
                with path.open(encoding='utf-8') as fh:
                    raw = json.load(fh)
                for alias, target in raw.items():
                    normalized_alias = _normalize(alias)
                    if not normalized_alias:
                        continue
                    alias_map[normalized_alias] = str(target)
            except Exception:
                continue
            break

    canonical_normalized = {_normalize(name): name for name in canonical_names}
    has_canonical = bool(canonical_normalized)

    filtered_aliases: Dict[str, str] = {}
    for alias_norm, target in alias_map.items():
        canonical = canonical_normalized.get(_normalize(target))
        if canonical:
            filtered_aliases[alias_norm] = canonical
        elif not has_canonical:
            filtered_aliases[alias_norm] = target
    return filtered_aliases


def _normalize(value: str) -> str:
    if value is None:
        return ''
    text = str(value)
    return text.replace('　', '').replace(' ', '').strip().lower()
