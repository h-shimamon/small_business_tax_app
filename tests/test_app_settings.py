from importlib import reload


def test_app_settings_reads_environment(monkeypatch):
    monkeypatch.setenv("APP_ENABLE_NEW_AUTH", "1")
    monkeypatch.setenv("ENABLE_SIGNUP_EMAIL_FIRST", "1")
    from app.config.schema import AppSettings

    settings = AppSettings()

    assert settings.ENABLE_NEW_AUTH is True
    assert settings.ENABLE_SIGNUP_EMAIL_FIRST is True

    monkeypatch.delenv("APP_ENABLE_NEW_AUTH", raising=False)
    monkeypatch.delenv("ENABLE_SIGNUP_EMAIL_FIRST", raising=False)


def test_create_app_applies_settings(monkeypatch):
    monkeypatch.setenv("APP_ENABLE_NEW_AUTH", "1")
    monkeypatch.setenv("APP_ENABLE_SIGNUP_EMAIL_FIRST", "1")
    monkeypatch.setenv("APP_ENABLE_CORP_TAX_MANUAL_EDIT", "1")

    # Reload schema to ensure cached settings pick up patched environment
    import app.config.schema as schema
    reload(schema)

    from app import create_app

    app = create_app({"TESTING": True})

    assert app.config["ENABLE_NEW_AUTH"] is True
    assert app.config["ENABLE_SIGNUP_EMAIL_FIRST"] is True
    assert app.config["ENABLE_CORP_TAX_MANUAL_EDIT"] is True

    settings = app.extensions.get("settings")
    assert settings is not None
    assert settings.ENABLE_NEW_AUTH is True
    assert settings.NEW_AUTH_EMAIL_BACKEND == "dummy"
    assert app.config["NEW_AUTH_EMAIL_BACKEND"] == "dummy"

    monkeypatch.delenv("APP_ENABLE_NEW_AUTH", raising=False)
    monkeypatch.delenv("APP_ENABLE_SIGNUP_EMAIL_FIRST", raising=False)
    monkeypatch.delenv("APP_ENABLE_CORP_TAX_MANUAL_EDIT", raising=False)
    reload(schema)
