# app/ui/context.py
from __future__ import annotations
from typing import Dict
from flask import current_app

from app.config.schema import AppSettings
from app.constants.ui_options import get_ui_options


def build_ui_context(settings: AppSettings | None) -> Dict:
    """Builds Jinja context fragment for UI options and related settings.
    Returns a dict suitable for context_processor: { 'ui_options': {...} }
    """
    try:
        enable = True if settings is None else bool(getattr(settings, 'ENABLE_UI_OPTIONS_DI', True))
        profile = 'default' if settings is None else getattr(settings, 'UI_PROFILE', 'default')
        if not enable:
            return {}
        return {
            'ui_options': get_ui_options(profile)
        }
    except Exception:
        return {}


def attach_company_ui_context(company_bp) -> None:
    """Attach a context processor to the given blueprint to inject ui_options.
    Safe no-op on errors.
    """
    try:
        @company_bp.app_context_processor
        def _inject_ui_options():  # type: ignore
            settings = None
            try:
                settings = current_app.extensions.get('settings')  # type: ignore
            except Exception:
                pass
            return build_ui_context(settings)
    except Exception:
        pass
