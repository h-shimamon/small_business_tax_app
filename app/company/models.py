"""Companyモデル群の集約モジュール。"""
from __future__ import annotations

from . import model_parts as _model_parts
from .model_parts import *  # noqa: F401,F403

__all__ = _model_parts.__all__
