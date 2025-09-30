from app.company.forms.metadata import extract_form_field_metadata
from app.services.soa_registry import STATEMENT_PAGES_CONFIG


def test_total_field_exists_on_models():
    for key, config in STATEMENT_PAGES_CONFIG.items():
        model = config.get('model')
        total_field = config.get('total_field')
        assert model is not None, f"model is not defined for page {key}"
        assert hasattr(model, total_field), f"model {model} missing total_field '{total_field}' for page {key}"


def test_form_fields_match_form_definitions():
    for key, config in STATEMENT_PAGES_CONFIG.items():
        form_cls = config.get('form')
        assert form_cls is not None, f"form is not defined for page {key}"
        auto_field_names = {meta['name'] for meta in extract_form_field_metadata(form_cls)}
        configured_fields = config.get('form_fields', [])
        configured_names = {field['name'] for field in configured_fields}
        missing = configured_names - auto_field_names
        assert not missing, f"form_fields for {key} include unknown fields: {sorted(missing)}"
