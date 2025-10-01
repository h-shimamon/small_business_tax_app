from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from wtforms import Form, SubmitField
from wtforms.fields.core import UnboundField

FieldMetadata = dict[str, Any]


def extract_form_field_metadata(form_cls: type[Form]) -> list[FieldMetadata]:
    """Return lightweight metadata for fields defined on a WTForms class."""
    form = _instantiate_form_safely(form_cls)
    if form is not None:
        fields_iter: Iterable[tuple[str, Any]] = form._fields.items()
    else:
        fields_iter = _iter_unbound_fields(form_cls)

    metadata: list[FieldMetadata] = []
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


def merge_field_metadata(base: list[FieldMetadata], overrides: list[FieldMetadata]) -> list[FieldMetadata]:
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


def _iter_unbound_fields(form_cls: type[Form]) -> Iterable[tuple[str, Any]]:
    seen: dict[str, Any] = {}
    for cls in reversed(form_cls.mro()):
        if not issubclass(cls, Form):
            continue
        for name, attr in cls.__dict__.items():
            if isinstance(attr, UnboundField):
                seen[name] = attr
    return list(seen.items())
