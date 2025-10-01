# app/constants package
# Compatibility shim + exports
from __future__ import annotations

# Re-export ui_options API
from .ui_options import (
    Option,  # type: ignore
    Options,  # type: ignore
    UIOptions,  # type: ignore
    get_ui_options,
)

# Backward compatibility for legacy app/constants.py module
# Some modules import: from app.constants import FLASH_SKIP, NAV_GROUP_SOA
# That module still exists as app/constants.py; load it explicitly and re-export.
try:
    import importlib.util as _ilu
    import os
    _pkg_dir = os.path.dirname(__file__)
    _legacy_path = os.path.abspath(os.path.join(_pkg_dir, '..', 'constants.py'))
    if os.path.exists(_legacy_path):
        _spec = _ilu.spec_from_file_location('app._constants_legacy', _legacy_path)
        if _spec and _spec.loader:
            _legacy = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_legacy)  # type: ignore
            FLASH_SKIP = getattr(_legacy, 'FLASH_SKIP', 'skip')
            NAV_GROUP_SOA = getattr(_legacy, 'NAV_GROUP_SOA', 'statement_of_accounts_group')
        else:
            FLASH_SKIP = 'skip'
            NAV_GROUP_SOA = 'statement_of_accounts_group'
    else:
        FLASH_SKIP = 'skip'
        NAV_GROUP_SOA = 'statement_of_accounts_group'
except Exception:
    FLASH_SKIP = 'skip'
    NAV_GROUP_SOA = 'statement_of_accounts_group'

__all__ = [
    'get_ui_options', 'UIOptions', 'Option', 'Options',
    'FLASH_SKIP', 'NAV_GROUP_SOA',
]
