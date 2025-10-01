"""Companyモデル群の集約モジュール。

新しいモデルは `app/company/model_parts` に追加し、このモジュール経由で
再エクスポートすること。`__all__` は model_parts の公開一覧と同期させる。
"""
from __future__ import annotations

from . import model_parts as _model_parts
from .model_parts import *  # noqa: F401,F403

__all__ = _model_parts.__all__
