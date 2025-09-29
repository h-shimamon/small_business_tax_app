from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from wtforms import Form, SubmitField
from wtforms.fields.core import UnboundField

FieldMetadata = Dict[str, Any]


def extract_form_field_metadata(form_cls: type[Form]) -> List[FieldMetadata]:
    """Return lightweight metadata for fields defined on a WTForms class."""
    form = _instantiate_form_safely(form_cls)
    if form is not None:
        fields_iter: Iterable[Tuple[str, Any]] = form._fields.items()
    else:
        fields_iter = _iter_unbound_fields(form_cls)

    metadata: List[FieldMetadata] = []
    for name, field in fields_iter:
        if name == 'csrf_token' or isinstance(field, SubmitField):
            continue
        entry: FieldMetadata = {
            'name': name,
            'type': getattr(field, '__class__', type(field)).__name__,
        }
        render_kw = getattr(field, 'render_kw', None)
        if isinstance(render_kw, dict):
            placeholder = render_kw.get('placeholder')
            if placeholder:
                entry['placeholder'] = placeholder
        description = getattr(field, 'description', None)
        if description:
            entry['description'] = description
        metadata.append(entry)
    return metadata


def merge_field_metadata(base: List[FieldMetadata], overrides: List[FieldMetadata]) -> List[FieldMetadata]:
    """Apply overrides onto auto-extracted metadata keyed by field name."""
    index = {item['name']: dict(item) for item in base}
    for override in overrides:
        target = index.setdefault(override['name'], {})
        target.update(override)
    return list(index.values())


def _instantiate_form_safely(form_cls: type[Form]) -> Form | None:
    try:
        return form_cls(meta={'csrf': False})
    except (TypeError, RuntimeError):
        try:
            return form_cls()
        except Exception:
            return None


def _iter_unbound_fields(form_cls: type[Form]) -> Iterable[Tuple[str, Any]]:
    seen: Dict[str, Any] = {}
    for cls in reversed(form_cls.mro()):
        if not issubclass(cls, Form):
            continue
        for name, attr in cls.__dict__.items():
            if isinstance(attr, UnboundField):
                seen[name] = attr
    return list(seen.items())
