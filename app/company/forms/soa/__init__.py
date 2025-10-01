from __future__ import annotations

from . import receivables as _receivables
from .definitions import SOA_FORM_FIELDS, get_soa_form_classes
from .deposits import DepositForm
from .notes import NotesPayableForm, NotesReceivableForm

globals().update({name: getattr(_receivables, name) for name in _receivables.__all__})

__all__ = [
    'SOA_FORM_FIELDS',
    'get_soa_form_classes',
    'DepositForm',
    'NotesPayableForm',
    'NotesReceivableForm',
    *_receivables.__all__,
]
