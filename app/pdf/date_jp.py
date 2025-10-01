"""Compatibility facade for wareki functions.

The implementation now lives in app.primitives.wareki; this module re-exports
the same API names to avoid breaking existing imports.
"""

from app.primitives.wareki import (
    era_name as wareki_era_name,  # noqa: F401
)
from app.primitives.wareki import (
    numeric_parts as wareki_numeric_parts,  # noqa: F401
)
from app.primitives.wareki import (
    to_wareki,  # noqa: F401
)
from app.primitives.wareki import (
    with_spaces as wareki_with_spaces,  # noqa: F401
)

__all__ = [
    "wareki_era_name",
    "wareki_numeric_parts",
    "to_wareki",
    "wareki_with_spaces",
]
