from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from app.navigation_builder import navigation_tree

if TYPE_CHECKING:
    from app.navigation_models import NavigationNode


def _soa_children() -> Iterable[NavigationNode]:
    """Return the navigation nodes registered under the statement of accounts group."""
    for node in navigation_tree:
        if node.key == 'statement_of_accounts_group':
            return node.children
    return ()


def get_soa_child_key(page: str) -> str | None:
    """Translate a statement-of-accounts page id into its navigation key."""
    for child in _soa_children():
        params_page = (child.params or {}).get('page')
        if params_page == page or child.key == page:
            return child.key
    return None


def get_next_soa_page(current_page: str, *, skipped_keys: set[str] | None = None) -> tuple[str | None, str | None]:
    """Return the next statement-of-accounts page and its display name.

    Skips any navigation entries whose key is listed in ``skipped_keys``.
    """
    skipped_keys = skipped_keys or set()
    soa_children = list(_soa_children())

    current_index = None
    for idx, child in enumerate(soa_children):
        params_page = (child.params or {}).get('page')
        if params_page == current_page or child.key == current_page:
            current_index = idx
            break

    if current_index is None:
        return None, None

    for child in soa_children[current_index + 1:]:
        if child.key in skipped_keys:
            continue
        params_page = (child.params or {}).get('page')
        target_page = params_page or child.key
        return target_page, child.name

    return None, None
