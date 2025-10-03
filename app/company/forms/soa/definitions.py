from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import yaml
from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, SelectField, StringField, SubmitField
from wtforms.fields import DateField, FloatField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from ..base_fields import CorporateNumberField, MoneyField

SCHEMA_PATH = Path(__file__).resolve().parents[4] / 'resources' / 'config' / 'soa_schema_map.yaml'

FieldFactory = Tuple[str, Callable[[], Any]]
FormFieldDefinitions = Dict[str, List[FieldFactory]]

# Default max lengths for string/text fields to keep parity with legacy WTForms definitions.
_FIELD_MAX_LENGTHS: Dict[str, int] = {
    'financial_institution': 100,
    'branch_name': 100,
    'account_number': 50,
    'drawer': 100,
    'payer_bank': 100,
    'payer_branch': 100,
    'discount_bank': 100,
    'discount_branch': 100,
    'payee': 100,
    'partner_name': 100,
    'partner_address': 200,
    'transaction_details': 200,
    'relationship': 100,
    'borrower_name': 100,
    'borrower_address': 200,
    'collateral_details': 200,
    'item_name': 100,
    'location': 200,
    'unit': 20,
    'remarks': 200,
    'security_type': 50,
    'issuer': 100,
    'asset_type': 50,
    'lessor_name': 100,
    'property_details': 200,
    'details': 200,
}

# Additional select choices not yet defined in the schema map.
_SELECT_DEFAULTS: Dict[str, List[str]] = {
    'account_type': [
        '普通預金',
        '当座預金',
        '通知預金',
        '定期預金',
        '定期積金',
        '別段預金',
        '納税準備預金',
        'その他',
    ],
}


def _load_schema() -> Dict[str, Any]:
    raw = yaml.safe_load(SCHEMA_PATH.read_text(encoding='utf-8')) or {}
    pages = raw.get('pages', {})
    if not isinstance(pages, dict):
        raise ValueError('soa_schema_map.yaml must define a mapping under "pages"')
    return pages


def _data_required(label: str) -> DataRequired:
    return DataRequired(message=f"{label}は必須です。")


def _length_validator(field_name: str) -> Optional[Length]:
    max_len = _FIELD_MAX_LENGTHS.get(field_name)
    return Length(max=max_len) if max_len else None


def _build_render_kw(field_conf: Dict[str, Any]) -> Dict[str, Any]:
    render_kw: Dict[str, Any] = {}
    placeholder = field_conf.get('placeholder')
    if placeholder:
        render_kw['placeholder'] = placeholder
    if field_conf.get('autofocus'):
        render_kw['autofocus'] = True
    rows = field_conf.get('rows')
    if rows:
        render_kw['rows'] = rows
    return render_kw


def _string_field(label: str, name: str, required: bool, render_kw: Dict[str, Any]):
    validators: List[Any] = []
    if required:
        validators.append(_data_required(label))
    else:
        validators.append(Optional())
    length_validator = _length_validator(name)
    if length_validator:
        validators.append(length_validator)
    return StringField(label, validators=validators, render_kw=render_kw or None)


def _text_field(label: str, name: str, required: bool, render_kw: Dict[str, Any]):
    validators: List[Any] = []
    if required:
        validators.append(_data_required(label))
    else:
        validators.append(Optional())
    length_validator = _length_validator(name)
    if length_validator:
        validators.append(length_validator)
    return TextAreaField(label, validators=validators, render_kw=render_kw or None)


def _numeric_field(field_cls, label: str, required: bool, render_kw: Dict[str, Any]):
    validators: List[Any] = []
    if required:
        validators.append(_data_required(label))
    else:
        validators.append(Optional())
    return field_cls(label, validators=validators, render_kw=render_kw or None)


def _select_field(field_conf: Dict[str, Any], label: str, required: bool, render_kw: Dict[str, Any]):
    choices = field_conf.get('choices') or _SELECT_DEFAULTS.get(field_conf['name'], [])
    processed: List[Tuple[str, str]] = []
    for choice in choices:
        if isinstance(choice, (list, tuple)) and len(choice) == 2:
            processed.append((str(choice[0]), str(choice[1])))
        else:
            processed.append((str(choice), str(choice)))
    validators: List[Any] = []
    if required:
        validators.append(_data_required(label))
    else:
        validators.append(Optional())
    return SelectField(label, choices=processed, validators=validators, render_kw=render_kw or None)


def _hidden_field(field_conf: Dict[str, Any]):
    kwargs: Dict[str, Any] = {}
    default = field_conf.get('default')
    if default is not None:
        kwargs['default'] = default
    return HiddenField(**kwargs)


def _date_field(label: str, required: bool, render_kw: Dict[str, Any]):
    render = {'class': 'js-date'}
    render.update(render_kw)
    validators: List[Any] = []
    if required:
        validators.append(_data_required(label))
    else:
        validators.append(Optional())
    return DateField(label, format='%Y-%m-%d', validators=validators, render_kw=render)


def _create_field(field_conf: Dict[str, Any]):
    label = field_conf.get('label', field_conf['name'])
    field_type = field_conf.get('type', 'string')
    required = bool(field_conf.get('required'))
    render_kw = _build_render_kw(field_conf)

    if field_type == 'string':
        return _string_field(label, field_conf['name'], required, render_kw)
    if field_type == 'text':
        return _text_field(label, field_conf['name'], required, render_kw)
    if field_type == 'money':
        field = MoneyField(label, required=required)
        if render_kw:
            field.render_kw = render_kw
        return field
    if field_type == 'corporate_number':
        field = CorporateNumberField(label, required=required)
        if render_kw:
            field.render_kw = render_kw
        return field
    if field_type == 'select':
        return _select_field(field_conf, label, required, render_kw)
    if field_type == 'boolean':
        return BooleanField(label, render_kw=render_kw or None)
    if field_type == 'hidden':
        field = _hidden_field(field_conf)
        if render_kw:
            field.render_kw = render_kw
        return field
    if field_type == 'date':
        return _date_field(label, required, render_kw)
    if field_type == 'integer':
        return _numeric_field(IntegerField, label, required, render_kw)
    if field_type == 'float':
        return _numeric_field(FloatField, label, required, render_kw)
    if field_type == 'percent':
        field = _numeric_field(FloatField, label, required, render_kw)
        existing = getattr(field, 'render_kw', {}) or {}
        existing.setdefault('step', '0.01')
        field.render_kw = existing
        return field
    return _string_field(label, field_conf['name'], required, render_kw)


def _build_field_factory(field_conf: Dict[str, Any]) -> FieldFactory:
    field_name = field_conf['name']

    def factory(conf: Dict[str, Any] = field_conf) -> Any:
        return _create_field(conf)

    return field_name, factory


@lru_cache(maxsize=1)
def _build_form_field_definitions() -> FormFieldDefinitions:
    pages = _load_schema()
    mapping: FormFieldDefinitions = {}
    for entry in pages.values():
        form_import = entry.get('form')
        if not form_import:
            continue
        form_name = form_import.split('.')[-1]
        field_factories = [_build_field_factory(dict(field)) for field in entry.get('fields', [])]
        mapping[form_name] = field_factories
    return mapping


SOA_FORM_FIELDS: FormFieldDefinitions = _build_form_field_definitions()


@lru_cache(maxsize=1)
def get_soa_form_classes() -> Dict[str, type[FlaskForm]]:
    classes: Dict[str, type[FlaskForm]] = {}
    for form_name, field_factories in SOA_FORM_FIELDS.items():
        attrs = {name: factory() for name, factory in field_factories}
        attrs.setdefault('submit', SubmitField('保存する'))
        form_class = type(form_name, (FlaskForm,), attrs)
        form_class.__module__ = __name__
        classes[form_name] = form_class
    return classes


__all__ = ['SOA_FORM_FIELDS', 'get_soa_form_classes']