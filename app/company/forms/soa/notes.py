from __future__ import annotations

from .definitions import get_soa_form_classes

_form_classes = get_soa_form_classes()

NotesReceivableForm = _form_classes['NotesReceivableForm']
NotesPayableForm = _form_classes['NotesPayableForm']

__all__ = ['NotesReceivableForm', 'NotesPayableForm']