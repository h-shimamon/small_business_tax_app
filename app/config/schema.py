# app/config/schema.py
from __future__ import annotations

import os
from typing import Dict

try:
    # pydantic v2 style (recommended)
    from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore
    from pydantic import Field  # type: ignore

    class AppSettings(BaseSettings):
        """Application settings (single source of truth).
        Falls back to dataclass defaults if pydantic-settings is not available.
        """
        model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

        LOCALE: str = "ja_JP"
        UI_PROFILE: str = "default"
        UI_OPTIONS_VERSION: str = "v1"
        # Feature flags (generic), e.g., {"enable_ui_options_di": true}
        FEATURE_FLAGS: Dict[str, bool] = Field(default_factory=dict)
        # Dedicated flag for UI options DI path (can be toggled if needed)
        ENABLE_UI_OPTIONS_DI: bool = True

except Exception:
    # Safe fallback without pydantic-settings
    from dataclasses import dataclass, field

    @dataclass
    class AppSettings:  # type: ignore
        LOCALE: str = os.getenv("APP_LOCALE", "ja_JP")
        UI_PROFILE: str = os.getenv("APP_UI_PROFILE", "default")
        UI_OPTIONS_VERSION: str = os.getenv("APP_UI_OPTIONS_VERSION", "v1")
        FEATURE_FLAGS: Dict[str, bool] = field(default_factory=dict)
        ENABLE_UI_OPTIONS_DI: bool = os.getenv("APP_ENABLE_UI_OPTIONS_DI", "1").lower() in ("1", "true", "yes", "on")
