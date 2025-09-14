from flask import render_template_string
from app import create_app


def make_app():
    return create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})


def test_ui_options_injected_via_context_or_global():
    app = make_app()
    with app.app_context():
        out = render_template_string("{{ ui_options.pc_os|length }}")
        assert out.isdigit() and int(out) >= 1


def test_get_ui_options_global_fallback():
    app = make_app()
    with app.app_context():
        out = render_template_string("{{ get_ui_options().pc_os|length }}")
        assert out.isdigit() and int(out) >= 1
