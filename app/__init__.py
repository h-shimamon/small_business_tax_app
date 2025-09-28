# app/__init__.py
import json
import os
import sys
from typing import Callable, Optional, Sequence, Set, Tuple, TypedDict

def _log_init_failure(context: str, exc: Exception) -> None:
    print(f"[init] {context} failed: {exc}", file=sys.stderr)

def _load_env() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv()
    except Exception as exc:
        _log_init_failure('load_dotenv', exc)


_load_env()
from flask import Flask
from .extensions import db, login_manager, migrate
from .company.models import User



def _register_template_globals(app: Flask) -> None:
    try:
        from .constants.ui_options import get_ui_options  # type: ignore
        from app.services.app_registry import get_pdf_export_map, get_default_pdf_year
        app.add_template_global(get_ui_options, name='get_ui_options')
        profile = os.getenv('APP_UI_PROFILE', 'default')
        app.add_template_global(get_ui_options(profile), name='ui_options')
        app.add_template_global(get_pdf_export_map, name='get_pdf_export_map')
        app.add_template_global(get_default_pdf_year(), name='default_pdf_year')
    except Exception as exc:
        _log_init_failure('template globals', exc)


def _apply_configuration(app: Flask, test_config) -> None:
    if test_config is None:
        env = (os.getenv('APP_ENV', 'development') or 'development').lower()
        env_map = {
            'development': 'config.DevConfig',
            'testing': 'config.TestingConfig',
            'production': 'config.ProductionConfig',
        }
        app.config.from_object(env_map.get(env, 'config.Config'))
    else:
        app.config.from_mapping(test_config)


def _ensure_instance_folder(app: Flask) -> None:
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


def _register_settings(app: Flask) -> None:
    try:
        from .config.schema import AppSettings
        app.extensions.setdefault('settings', AppSettings())
    except Exception as exc:
        _log_init_failure('config schema', exc)


def _attach_ui_context_safe(app: Flask) -> None:
    try:
        from .ui.context import attach_app_ui_context  # type: ignore
        attach_app_ui_context(app)
    except Exception as exc:
        _log_init_failure('attach_app_ui_context', exc)


def _register_pdf_registry(app: Flask) -> None:
    try:
        from app.services import pdf_registry_init  # noqa: F401
    except Exception as exc:
        _log_init_failure('pdf_registry_init', exc)


def _configure_logging(app: Flask) -> None:
    try:
        import logging as _logging
        lvl = str(app.config.get('LOG_LEVEL', 'INFO')).upper()
        level = getattr(_logging, lvl, _logging.INFO)
        app.logger.setLevel(level)
        _logging.getLogger('werkzeug').setLevel(level)
    except Exception as exc:
        _log_init_failure('logging setup', exc)


def _check_production_secret(app: Flask) -> None:
    try:
        if (os.getenv('APP_ENV', 'development').lower() == 'production'):
            sk = str(app.config.get('SECRET_KEY') or '')
            if (not sk) or sk.startswith('a_default_dev_'):
                app.logger.warning('SECRET_KEY is not securely set for production environment')
    except Exception as exc:
        _log_init_failure('production secret key check', exc)


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'company.login'


def _register_filters(app: Flask) -> None:
    from .utils import format_currency, format_number
    app.jinja_env.filters['format_currency'] = format_currency
    app.jinja_env.filters['format_number'] = format_number


def _register_company_blueprint(app: Flask) -> None:
    from .company import company_bp
    app.register_blueprint(company_bp)


def _register_newauth_blueprint(app: Flask) -> None:
    try:
        flag = str(app.config.get('ENABLE_NEW_AUTH') or os.getenv('ENABLE_NEW_AUTH', '0')).lower()
        if flag in ('1', 'true', 'yes', 'on'):
            from .newauth import newauth_bp
            app.register_blueprint(newauth_bp, url_prefix='/xauth')
    except Exception as exc:
        _log_init_failure('newauth blueprint', exc)


def _register_compat_blueprint(app: Flask) -> None:
    try:
        from app.compat.redirector import bp_redirector
        app.register_blueprint(bp_redirector)
    except Exception as exc:
        _log_init_failure('compat redirector', exc)


def _register_corporate_number_api(app: Flask) -> None:
    try:
        from app.integrations.houjinbangou.stub_client import StubHojinClient
        from app.services.corporate_number_service import CorporateNumberService
        from app.api.corporate_number import create_blueprint as create_corp_api
        hojin_client = StubHojinClient()
        corp_service = CorporateNumberService(hojin_client)
        app.register_blueprint(create_corp_api(corp_service))
    except Exception as exc:
        _log_init_failure('corporate number API setup', exc)


def _register_cli_commands(app: Flask) -> None:
    from . import commands
    commands.register_commands(app)



def _register_user_loader(app: Flask) -> None:
    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))



class InitFailure(TypedDict):
    step: str
    error: str
    severity: str
    dependencies: Tuple[str, ...]

class InitStep(TypedDict, total=False):
    key: str
    runner: Callable[[Flask], None]
    depends_on: Tuple[str, ...]
    optional: bool
    description: str
    severity: str


def _build_init_steps(test_config) -> Sequence[InitStep]:
    def _configuration_runner(app: Flask) -> None:
        _apply_configuration(app, test_config)

    return [
        {'key': 'template_globals', 'runner': _register_template_globals, 'optional': True, 'severity': 'soft'},
        {'key': 'configuration', 'runner': _configuration_runner, 'optional': False, 'severity': 'fatal'},
        {'key': 'pdf_registry', 'runner': _register_pdf_registry, 'depends_on': ('configuration',), 'optional': True, 'severity': 'soft'},
        {'key': 'instance_folder', 'runner': _ensure_instance_folder, 'depends_on': ('configuration',), 'optional': True, 'severity': 'soft'},
        {'key': 'settings', 'runner': _register_settings, 'depends_on': ('configuration',), 'optional': True, 'severity': 'soft'},
        {'key': 'ui_context', 'runner': _attach_ui_context_safe, 'depends_on': ('configuration',), 'optional': True, 'severity': 'soft'},
        {'key': 'logging', 'runner': _configure_logging, 'depends_on': ('configuration',), 'optional': True, 'severity': 'soft'},
        {'key': 'production_secret_check', 'runner': _check_production_secret, 'depends_on': ('configuration',), 'optional': True, 'severity': 'soft'},
        {'key': 'extensions', 'runner': _init_extensions, 'depends_on': ('configuration',), 'optional': False, 'severity': 'fatal'},
        {'key': 'user_loader', 'runner': _register_user_loader, 'depends_on': ('extensions',), 'optional': False, 'severity': 'fatal'},
        {'key': 'filters', 'runner': _register_filters, 'depends_on': ('extensions',), 'optional': False, 'severity': 'fatal'},
        {'key': 'company_blueprint', 'runner': _register_company_blueprint, 'depends_on': ('extensions',), 'optional': False, 'severity': 'fatal'},
        {'key': 'newauth_blueprint', 'runner': _register_newauth_blueprint, 'depends_on': ('extensions',), 'optional': True, 'severity': 'soft'},
        {'key': 'compat_blueprint', 'runner': _register_compat_blueprint, 'depends_on': ('extensions',), 'optional': True, 'severity': 'soft'},
        {'key': 'corporate_number_api', 'runner': _register_corporate_number_api, 'depends_on': ('extensions', 'company_blueprint'), 'optional': True, 'severity': 'soft'},
        {'key': 'cli_commands', 'runner': _register_cli_commands, 'depends_on': ('configuration',), 'optional': True, 'severity': 'soft'},
    ]


def _run_initialization_sequence(app: Flask, steps: Sequence[InitStep]) -> None:
    completed: Set[str] = set()
    failures: list[InitFailure] = []
    for step in steps:
        key = step['key']
        depends_on = step.get('depends_on', ())
        severity = step.get('severity', 'soft')
        missing = tuple(dep for dep in depends_on if dep not in completed)
        if missing:
            failure: InitFailure = {
                'step': key,
                'error': f"dependencies not met: {', '.join(missing)}",
                'severity': severity,
                'dependencies': missing,
            }
            try:
                app.logger.error(json.dumps({'init_failure': failure}))
            except Exception:
                _log_init_failure(key, RuntimeError(failure['error']))
            failures.append(failure)
            continue
        try:
            step['runner'](app)
            completed.add(key)
        except Exception as exc:
            failure = {
                'step': key,
                'error': str(exc),
                'severity': severity,
                'dependencies': depends_on,
            }
            try:
                app.logger.error(json.dumps({'init_failure': failure}))
            except Exception:
                _log_init_failure(key, exc)
            failures.append(failure)
            if not step.get('optional', True) or severity == 'fatal':
                raise
    if failures:
        registry = app.extensions.setdefault('init_failures', [])
        registry.extend(failures)


def create_app(test_config=None):
    """
    アプリケーションファクトリ: Flaskアプリケーションのインスタンスを作成・設定します。
    """
    app = Flask(__name__, instance_relative_config=True)

    steps = _build_init_steps(test_config)
    _run_initialization_sequence(app, steps)

    return app
