from __future__ import annotations

from .soa import receivables as _receivables

globals().update({name: getattr(_receivables, name) for name in _receivables.__all__})

__all__ = list(_receivables.__all__)
