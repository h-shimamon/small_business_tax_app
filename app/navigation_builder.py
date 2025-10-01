# app/navigation_builder.py
from __future__ import annotations

from collections.abc import Iterator, Sequence

from app.services.app_registry import get_navigation_structure

from .navigation_models import NavigationNode


def build_navigation_tree() -> list[NavigationNode]:
    """データ定義に基づき、NavigationNodeのツリーを構築して返す"""
    return [NavigationNode(**data) for data in get_navigation_structure()]


class _NavigationTreeProxy(Sequence[NavigationNode]):
    """Lazy proxy that builds the navigation tree only on first use."""

    def __init__(self) -> None:
        self._cache: list[NavigationNode] | None = None

    def _ensure(self) -> list[NavigationNode]:
        if self._cache is None:
            self._cache = build_navigation_tree()
        return self._cache

    def refresh(self) -> list[NavigationNode]:
        """Clear the cache and rebuild on next access."""
        self._cache = None
        return self._ensure()

    def __iter__(self) -> Iterator[NavigationNode]:
        return iter(self._ensure())

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._ensure())

    def __getitem__(self, index):  # pragma: no cover - trivial pass-through
        return self._ensure()[index]


def get_navigation_tree() -> Sequence[NavigationNode]:
    return navigation_tree


navigation_tree: Sequence[NavigationNode] = _NavigationTreeProxy()
