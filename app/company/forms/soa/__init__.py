from __future__ import annotations

from .definitions import SOA_FORM_FIELDS, get_soa_form_classes

_form_classes = get_soa_form_classes()

globals().update(_form_classes)

__all__ = ['SOA_FORM_FIELDS', 'get_soa_form_classes', *_form_classes.keys()]