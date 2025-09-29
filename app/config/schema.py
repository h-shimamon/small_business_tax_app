# app/config/schema.py
from __future__ import annotations

import os
from typing import Dict, Optional

try:
    # pydantic v2 style (recommended)
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore
    from pydantic import AliasChoices, Field  # type: ignore

    class AppSettings(BaseSettings):
        """Application settings (single source of truth).
        Falls back to dataclass defaults if pydantic-settings is not available.
        """
        model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

        LOCALE: str = Field(
            default="ja_JP",
            validation_alias=AliasChoices("APP_LOCALE", "LOCALE"),
        )
        UI_PROFILE: str = Field(
            default="default",
            validation_alias=AliasChoices("APP_UI_PROFILE", "UI_PROFILE"),
        )
        UI_OPTIONS_VERSION: str = Field(
            default="v1",
            validation_alias=AliasChoices("APP_UI_OPTIONS_VERSION", "UI_OPTIONS_VERSION"),
        )
        # Feature flags (generic), e.g., {"enable_ui_options_di": true}
        FEATURE_FLAGS: Dict[str, bool] = Field(default_factory=dict)
        # Dedicated flag for UI options DI path (can be toggled if needed)
        ENABLE_UI_OPTIONS_DI: bool = Field(
            default=True,
            validation_alias=AliasChoices("APP_ENABLE_UI_OPTIONS_DI", "ENABLE_UI_OPTIONS_DI"),
        )
        ENABLE_NEW_AUTH: bool = Field(
            default=False,
            validation_alias=AliasChoices("APP_ENABLE_NEW_AUTH", "ENABLE_NEW_AUTH"),
        )
        ENABLE_SIGNUP_EMAIL_FIRST: bool = Field(
            default=False,
            validation_alias=AliasChoices("APP_ENABLE_SIGNUP_EMAIL_FIRST", "ENABLE_SIGNUP_EMAIL_FIRST"),
        )
        ENABLE_CORP_TAX_MANUAL_EDIT: bool = Field(
            default=False,
            validation_alias=AliasChoices("APP_ENABLE_CORP_TAX_MANUAL_EDIT", "ENABLE_CORP_TAX_MANUAL_EDIT"),
        )
        NEW_AUTH_EMAIL_BACKEND: str = Field(
            default="dummy",
            validation_alias=AliasChoices("APP_NEW_AUTH_EMAIL_BACKEND", "NEW_AUTH_EMAIL_BACKEND"),
        )
        NEW_AUTH_EMAIL_HOST: str = Field(
            default="",
            validation_alias=AliasChoices("APP_NEW_AUTH_EMAIL_HOST", "NEW_AUTH_EMAIL_HOST"),
        )
        NEW_AUTH_EMAIL_PORT: int = Field(
            default=587,
            validation_alias=AliasChoices("APP_NEW_AUTH_EMAIL_PORT", "NEW_AUTH_EMAIL_PORT"),
        )
        NEW_AUTH_EMAIL_USERNAME: Optional[str] = Field(
            default=None,
            validation_alias=AliasChoices("APP_NEW_AUTH_EMAIL_USERNAME", "NEW_AUTH_EMAIL_USERNAME"),
        )
        NEW_AUTH_EMAIL_PASSWORD: Optional[str] = Field(
            default=None,
            validation_alias=AliasChoices("APP_NEW_AUTH_EMAIL_PASSWORD", "NEW_AUTH_EMAIL_PASSWORD"),
        )
        NEW_AUTH_EMAIL_USE_TLS: bool = Field(
            default=True,
            validation_alias=AliasChoices("APP_NEW_AUTH_EMAIL_USE_TLS", "NEW_AUTH_EMAIL_USE_TLS"),
        )
        NEW_AUTH_EMAIL_FROM: str = Field(
            default="no-reply@example.com",
            validation_alias=AliasChoices("APP_NEW_AUTH_EMAIL_FROM", "NEW_AUTH_EMAIL_FROM"),
        )

except Exception:
    # Safe fallback without pydantic-settings
    from dataclasses import dataclass, field

    def _env_str(default: str, *keys: str) -> str:
        for key in keys:
            value = os.getenv(key)
            if value:
                return value
        return default

    def _env_bool(default: bool, *keys: str) -> bool:
        for key in keys:
            value = os.getenv(key)
            if value is not None:
                return value.lower() in ("1", "true", "yes", "on")
        return default

    @dataclass
    class AppSettings:  # type: ignore
        LOCALE: str = field(default_factory=lambda: _env_str("ja_JP", "APP_LOCALE", "LOCALE"))
        UI_PROFILE: str = field(default_factory=lambda: _env_str("default", "APP_UI_PROFILE", "UI_PROFILE"))
        UI_OPTIONS_VERSION: str = field(default_factory=lambda: _env_str("v1", "APP_UI_OPTIONS_VERSION", "UI_OPTIONS_VERSION"))
        FEATURE_FLAGS: Dict[str, bool] = field(default_factory=dict)
        ENABLE_UI_OPTIONS_DI: bool = field(default_factory=lambda: _env_bool(True, "APP_ENABLE_UI_OPTIONS_DI", "ENABLE_UI_OPTIONS_DI"))
        ENABLE_NEW_AUTH: bool = field(default_factory=lambda: _env_bool(False, "APP_ENABLE_NEW_AUTH", "ENABLE_NEW_AUTH"))
        ENABLE_SIGNUP_EMAIL_FIRST: bool = field(default_factory=lambda: _env_bool(False, "APP_ENABLE_SIGNUP_EMAIL_FIRST", "ENABLE_SIGNUP_EMAIL_FIRST"))
        ENABLE_CORP_TAX_MANUAL_EDIT: bool = field(default_factory=lambda: _env_bool(False, "APP_ENABLE_CORP_TAX_MANUAL_EDIT", "ENABLE_CORP_TAX_MANUAL_EDIT"))
        NEW_AUTH_EMAIL_BACKEND: str = field(default_factory=lambda: _env_str("dummy", "APP_NEW_AUTH_EMAIL_BACKEND", "NEW_AUTH_EMAIL_BACKEND"))
        NEW_AUTH_EMAIL_HOST: str = field(default_factory=lambda: _env_str("", "APP_NEW_AUTH_EMAIL_HOST", "NEW_AUTH_EMAIL_HOST"))
        NEW_AUTH_EMAIL_PORT: int = field(default_factory=lambda: int(_env_str("587", "APP_NEW_AUTH_EMAIL_PORT", "NEW_AUTH_EMAIL_PORT")))
        NEW_AUTH_EMAIL_USERNAME: Optional[str] = field(default_factory=lambda: _env_str("", "APP_NEW_AUTH_EMAIL_USERNAME", "NEW_AUTH_EMAIL_USERNAME") or None)
        NEW_AUTH_EMAIL_PASSWORD: Optional[str] = field(default_factory=lambda: _env_str("", "APP_NEW_AUTH_EMAIL_PASSWORD", "NEW_AUTH_EMAIL_PASSWORD") or None)
        NEW_AUTH_EMAIL_USE_TLS: bool = field(default_factory=lambda: _env_bool(True, "APP_NEW_AUTH_EMAIL_USE_TLS", "NEW_AUTH_EMAIL_USE_TLS"))
        NEW_AUTH_EMAIL_FROM: str = field(default_factory=lambda: _env_str("no-reply@example.com", "APP_NEW_AUTH_EMAIL_FROM", "NEW_AUTH_EMAIL_FROM"))
