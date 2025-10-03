from __future__ import annotations

from .definitions import get_soa_form_classes

DepositForm = get_soa_form_classes()['DepositForm']

__all__ = ['DepositForm']