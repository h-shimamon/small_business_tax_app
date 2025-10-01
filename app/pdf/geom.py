from __future__ import annotations

from typing import Any


def merge_rects(defaults: dict[str, tuple[float, float, float, float]], overrides: dict[str, Any]) -> dict[str, tuple[float, float, float, float]]:
    """Return a new dict of rects by overlaying overrides onto defaults.

    - Ensures each value is a 4-tuple[float, float, float, float].
    - Ignores invalid override entries (keeps default).
    """
    result: dict[str, tuple[float, float, float, float]] = {}
    for key, default_val in defaults.items():
        ov = overrides.get(key, default_val)
        try:
            x0, y0, w, h = ov  # type: ignore[misc]
            result[key] = (float(x0), float(y0), float(w), float(h))
        except Exception:
            # Fallback to default if override malformed
            x0, y0, w, h = default_val
            result[key] = (float(x0), float(y0), float(w), float(h))
    return result


def get_row_metrics(overrides: dict[str, Any], *, default_row1_center: float, default_row_step: float, default_step_y: float, default_padding_x: float) -> dict[str, float]:
    """Extract numeric row/spacing metrics with fallbacks and typing guarantees."""
    row = overrides.get("row", {}) if isinstance(overrides, dict) else {}
    return {
        "ROW1_CENTER": float(row.get("ROW1_CENTER", default_row1_center)),
        "ROW_STEP": float(row.get("ROW_STEP", default_row_step)),
        "STEP_Y": float(row.get("STEP_Y", default_step_y)),
        "PADDING_X": float(row.get("PADDING_X", default_padding_x)),
    }

