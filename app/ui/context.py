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
        ui_opts = get_ui_options(profile)
        # fallback判定: 要求profileと実profileが異なる場合は警告
        try:
            real_profile = ui_opts.get('profile')  # type: ignore
            if real_profile and real_profile != profile:
                current_app.logger.warning('ui_options profile fallback: requested=%s, used=%s', profile, real_profile)
        except Exception:
            pass
        # minimal guard rails: check required keys exist
        required = ('staff_roles', 'pc_os', 'pc_usage', 'ecommerce', 'data_storage')
        missing = [k for k in required if k not in ui_opts]
        if missing:
            try:
                current_app.logger.warning('ui_options missing keys: %s', ','.join(missing))
            except Exception:
                pass
        return {
            'ui_options': ui_opts
        }
    except Exception:
        return {}


def attach_company_ui_context(company_bp) -> None:
    """(Kept for compatibility) Attach a context processor to the given blueprint.
    Current code uses app-level injector; this remains as no-op safety.
    """
    try:
        @company_bp.context_processor
        def _inject_ui_options():  # type: ignore
            settings = None
            try:
                settings = current_app.extensions.get('settings')  # type: ignore
            except Exception:
                pass
            return build_ui_context(settings)
    except Exception:
        pass


def attach_app_ui_context(app) -> None:
    """Register app-level context + template globals.
    Works for render_template_string under app/app_request context.
    """
    try:
        @app.context_processor
        def _inject_ui_options_app():  # type: ignore
            settings = None
            try:
                settings = app.extensions.get('settings')  # type: ignore
            except Exception:
                pass
            return build_ui_context(settings)

        @app.template_global(name='get_ui_options')
        def _get_ui_options_global(profile: str | None = None):  # type: ignore
            if profile:
                return get_ui_options(profile)
            try:
                settings = app.extensions.get('settings')  # type: ignore
                prof = getattr(settings, 'UI_PROFILE', 'default') if settings else 'default'
            except Exception:
                prof = 'default'
            return get_ui_options(prof)
    except Exception:
        pass
