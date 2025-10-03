from __future__ import annotations

from typing import Any

from flask import current_app


def log_navigation_issue(event: str, **details: Any) -> None:
    """Safely記録する。ナビゲーション周りの例外を共通化。"""
    try:
        safe_details = {key: str(value) for key, value in details.items()}
        current_app.logger.warning("navigation.%s", event, extra={"navigation_error": safe_details})
    except Exception:
        pass
