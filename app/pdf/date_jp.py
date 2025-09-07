from __future__ import annotations

"""
Compatibility facade for wareki functions.

The implementation now lives in app.primitives.wareki; this module re-exports
the same API names to avoid breaking existing imports.
"""

from app.primitives.wareki import (  # noqa: E402
    to_wareki,                    # noqa: F401
    with_spaces as wareki_with_spaces,  # noqa: F401
    era_name as wareki_era_name,        # noqa: F401
    numeric_parts as wareki_numeric_parts,  # noqa: F401
)
