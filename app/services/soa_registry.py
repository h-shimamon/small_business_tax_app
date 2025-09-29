"""Centralized registry for Statement of Accounts configuration and mappings."""
from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict


class StatementPageConfig(TypedDict, total=False):
    model: Any
    form: Any
    title: str
    total_field: str
    template: str
    query_filter: Callable[[Any], Any]
    form_fields: List[Dict[str, Any]]
    summary: Dict[str, str]
    pl_targets: List[str]


@dataclass(frozen=True)
class StatementPageDefinition:
    key: str
    model: str
    form: str
    title: str
    total_field: str
    template: str
    summary_type: str
    summary_label: str
    form_fields: List[Dict[str, Any]] = field(default_factory=list)
    query_filter: Optional[Dict[str, Any]] = None
    pl_targets: List[str] = field(default_factory=list)


_ALLOWED_SUMMARY_TYPES = {'BS', 'PL'}
_ALLOWED_QUERY_TYPES = {'equals'}
_CONFIG_PATH = Path(__file__).resolve().parents[2] / 'resources' / 'config' / 'soa_pages.json'


@lru_cache(maxsize=1)
def _load_page_definitions() -> Tuple[StatementPageDefinition, ...]:
    with _CONFIG_PATH.open('r', encoding='utf-8') as fh:
        raw = json.load(fh)

    definitions: List[StatementPageDefinition] = []
    seen_keys: set[str] = set()
    for item in raw.get('pages', []):
        summary = item.get('summary') or {}
        if 'type' not in summary or 'label' not in summary:
            raise ValueError(f"SoA page '{item.get('key')}' requires a summary definition")

        definition = StatementPageDefinition(
            key=item['key'],
            model=item['model'],
            form=item['form'],
            title=item['title'],
            total_field=item['total_field'],
            template=item['template'],
            summary_type=summary['type'],
            summary_label=summary['label'],
            form_fields=item.get('form_fields', []),
            query_filter=item.get('query_filter'),
            pl_targets=item.get('pl_targets', []),
        )
        _validate_definition(definition, seen_keys)
        definitions.append(definition)
    return tuple(definitions)


def _validate_definition(definition: StatementPageDefinition, seen_keys: set[str]) -> None:
    if definition.key in seen_keys:
        raise ValueError(f"Duplicate SoA page key detected: {definition.key}")
    seen_keys.add(definition.key)

    if definition.summary_type not in _ALLOWED_SUMMARY_TYPES:
        raise ValueError(
            f"Unsupported summary_type '{definition.summary_type}' for SoA page '{definition.key}'"
        )

    if definition.query_filter is not None:
        if definition.query_filter.get('type') not in _ALLOWED_QUERY_TYPES:
            raise ValueError(
                f"Unsupported query_filter type '{definition.query_filter.get('type')}' for '{definition.key}'"
            )
        if 'field' not in definition.query_filter or 'value' not in definition.query_filter:
            raise ValueError(f"Incomplete query_filter definition for '{definition.key}'")

    if not isinstance(definition.form_fields, list):
        raise ValueError(f"form_fields must be a list for '{definition.key}'")
    for field_def in definition.form_fields:
        if 'name' not in field_def:
            raise ValueError(f"form_fields entries must include 'name' for '{definition.key}'")

    if not isinstance(definition.pl_targets, list):
        raise ValueError(f"pl_targets must be a list for '{definition.key}'")


def _resolve_attribute(import_path: str) -> Any:
    module_path, attr = import_path.rsplit('.', 1)
    module = import_module(module_path)
    return getattr(module, attr)


def _build_query_filter(model: Any, spec: Dict[str, Any]) -> Callable[[Any], Any]:
    filter_type = spec.get('type')
    if filter_type == 'equals':
        field_name = spec['field']
        value = spec['value']
        target = getattr(model, field_name)

        def _apply(query):
            return query.filter(target == value)

        return _apply
    raise ValueError(f"Unsupported query_filter type: {filter_type}")


@lru_cache(maxsize=1)
def _build_statement_pages_config() -> Dict[str, StatementPageConfig]:
    configs: Dict[str, StatementPageConfig] = {}
    for definition in _load_page_definitions():
        model = _resolve_attribute(definition.model)
        form = _resolve_attribute(definition.form)

        entry: StatementPageConfig = {
            'model': model,
            'form': form,
            'title': definition.title,
            'total_field': definition.total_field,
            'template': definition.template,
            'summary': {
                'type': definition.summary_type,
                'label': definition.summary_label,
            },
        }
        if definition.form_fields:
            entry['form_fields'] = definition.form_fields
        if definition.pl_targets:
            entry['pl_targets'] = definition.pl_targets
        if definition.query_filter:
            entry['query_filter'] = _build_query_filter(model, definition.query_filter)
        configs[definition.key] = entry
    return configs


class _StatementPagesProxy(Mapping[str, StatementPageConfig]):
    """Lazily materialise the statement page configurations."""

    def __init__(self) -> None:
        self._cache: Optional[Dict[str, StatementPageConfig]] = None

    def _ensure(self) -> Dict[str, StatementPageConfig]:
        if self._cache is None:
            self._cache = _build_statement_pages_config()
        return self._cache

    def refresh(self) -> Dict[str, StatementPageConfig]:
        self._cache = None
        return self._ensure()

    def __getitem__(self, key):  # type: ignore[override]
        return self._ensure()[key]

    def __iter__(self):  # type: ignore[override]
        return iter(self._ensure())

    def __len__(self):  # type: ignore[override]
        return len(self._ensure())

    def get(self, key, default=None):  # type: ignore[override]
        return self._ensure().get(key, default)


STATEMENT_PAGES_CONFIG: Mapping[str, StatementPageConfig] = _StatementPagesProxy()
SUMMARY_PAGE_MAP: Dict[str, Tuple[str, str]] = {
    definition.key: (definition.summary_type, definition.summary_label)
    for definition in _load_page_definitions()
}
PL_PAGE_ACCOUNTS: Dict[str, List[str]] = {
    definition.key: definition.pl_targets
    for definition in _load_page_definitions()
    if definition.pl_targets
}


__all__ = [
    'STATEMENT_PAGES_CONFIG',
    'SUMMARY_PAGE_MAP',
    'PL_PAGE_ACCOUNTS',
    'StatementPageConfig',
]
