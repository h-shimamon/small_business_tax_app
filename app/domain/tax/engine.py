from __future__ import annotations

"""Compatibility shim for legacy imports."""

from app.tax_engine.engine import calculate_tax  # noqa: F401

__all__ = ['calculate_tax']
