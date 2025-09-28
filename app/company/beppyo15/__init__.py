"""別表15（交際費等）のサービス実装パッケージ。"""
from __future__ import annotations

from .service import Beppyo15Service  # noqa: F401
from .view_models import (  # noqa: F401
    Beppyo15FieldDefinition,
    Beppyo15ItemViewModel,
    Beppyo15PageViewModel,
    Beppyo15SummaryViewModel,
)
