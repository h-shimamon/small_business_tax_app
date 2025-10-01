# app/ui/context.py
from __future__ import annotations

from flask import current_app, has_app_context

from app.config.schema import AppSettings
from app.constants.ui_options import get_ui_options


def _log_ui_context_issue(event: str, exc: Exception | None = None, **details) -> None:
    if not has_app_context():
        return
    try:
        payload = {key: str(value) for key, value in details.items()}
        logger = current_app.logger
        if exc is not None:
            logger.warning("ui_context.%s", event, exc_info=exc, extra={"ui_context_error": payload})
        else:
            logger.warning("ui_context.%s", event, extra={"ui_context_error": payload})
    except Exception:
        pass


def build_ui_context(settings: AppSettings | None) -> dict:
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
        real_profile = None
        try:
            real_profile = ui_opts.get('profile')  # type: ignore
        except Exception as exc:
            _log_ui_context_issue('profile_lookup_failed', exc=exc, requested=profile)
        if real_profile and real_profile != profile:
            _log_ui_context_issue('profile_fallback', requested=profile, used=real_profile)
        # minimal guard rails: check required keys exist
        required = ('staff_roles', 'pc_os', 'pc_usage', 'ecommerce', 'data_storage')
        try:
            missing = [k for k in required if k not in ui_opts]
        except Exception as exc:
            _log_ui_context_issue('missing_key_check_failed', exc=exc, requested=profile)
            missing = []
        if missing:
            _log_ui_context_issue('missing_keys', requested=profile, missing=missing)
        return {
            'ui_options': ui_opts
        }
    except Exception as exc:
        _log_ui_context_issue('build', exc=exc)
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
            except Exception as exc:
                _log_ui_context_issue('read_settings.company', exc=exc)
                settings = None
            return build_ui_context(settings)
    except Exception as exc:
        _log_ui_context_issue('attach_company', exc=exc)


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
            except Exception as exc:
                _log_ui_context_issue('read_settings.app', exc=exc)
                settings = None
            return build_ui_context(settings)

        @app.template_global(name='get_ui_options')
        def _get_ui_options_global(profile: str | None = None):  # type: ignore
            if profile:
                return get_ui_options(profile)
            try:
                settings = app.extensions.get('settings')  # type: ignore
                prof = getattr(settings, 'UI_PROFILE', 'default') if settings else 'default'
            except Exception as exc:
                _log_ui_context_issue('read_settings.app_global', exc=exc)
                prof = 'default'
            return get_ui_options(prof)
    except Exception as exc:
        _log_ui_context_issue('attach_app', exc=exc)
