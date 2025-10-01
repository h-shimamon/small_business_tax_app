from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app.company.services.master_data_service import MasterDataService


@dataclass(frozen=True)
class AccountCatalog:
    """勘定科目マスタと同義語辞書をカプセル化する。"""

    canonical_names: set[str]
    aliases: dict[str, str]
    normalized_lookup: dict[str, str]
    bs_accounts: list[str]
    pl_accounts: list[str]

    def normalize(self, value: str) -> str:
        return _normalize(value)

    def resolve(self, value: str) -> str | None:
        key = self.normalize(value)
        return self.aliases.get(key) or self.normalized_lookup.get(key)


def load_catalog(master_service: MasterDataService | None = None) -> AccountCatalog:
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


def _extract_account_names(df) -> list[str]:
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


def _resolve_alias_file(cfg: dict, default_root: Path) -> Path | None:
    base_dir = cfg.get('MASTER_DATA_BASE_DIR')
    candidates: list[Path] = []
    if base_dir:
        candidates.append(Path(base_dir) / 'resources' / 'masters' / 'account_aliases.json')
    candidates.append(default_root / 'resources' / 'masters' / 'account_aliases.json')
    for path in candidates:
        if path.exists():
            return path
    return None


def _read_alias_json(path: Path) -> dict[str, str]:
    try:
        with path.open(encoding='utf-8') as fh:
            raw = json.load(fh)
        if isinstance(raw, dict):
            return {str(k): str(v) for k, v in raw.items()}
    except Exception:
        pass
    return {}


def _normalize_alias_entries(alias_entries: dict[str, str]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for alias, target in alias_entries.items():
        alias_norm = _normalize(alias)
        if alias_norm:
            normalized[alias_norm] = target
    return normalized


def _filter_aliases(alias_map: dict[str, str], canonical_names: Iterable[str]) -> dict[str, str]:
    canonical_lookup = {_normalize(name): name for name in canonical_names}
    has_canonical = bool(canonical_lookup)
    filtered: dict[str, str] = {}
    for alias_norm, target in alias_map.items():
        canonical = canonical_lookup.get(_normalize(target))
        if canonical:
            filtered[alias_norm] = canonical
        elif not has_canonical:
            filtered[alias_norm] = target
    return filtered


def _load_alias_map(canonical_names: Iterable[str]) -> dict[str, str]:
    try:
        app = current_app._get_current_object()
        cfg = app.config
        default_root = Path(app.root_path).parent
    except RuntimeError:
        cfg = {}
        default_root = Path('.')

    alias_path = _resolve_alias_file(cfg, default_root)
    if not alias_path:
        return {}

    raw_aliases = _read_alias_json(alias_path)
    normalized_aliases = _normalize_alias_entries(raw_aliases)
    return _filter_aliases(normalized_aliases, canonical_names)


def _normalize(value: str) -> str:
    if value is None:
        return ''
    text = str(value)
    return text.replace('　', '').replace(' ', '').strip().lower()
