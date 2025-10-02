from app.services.soa_registry import STATEMENT_PAGES_CONFIG
from app.company.forms.soa.metadata import SOA_FORM_FIELD_METADATA
from app.services import soa_registry


def _iter_field_names(meta_list):
    for meta in meta_list:
        if isinstance(meta, dict):
            name = meta.get('name')
            if name:
                yield name
        elif isinstance(meta, str):
            yield meta


def test_form_fields_match_config(app):
    with app.app_context():
        for page, config in STATEMENT_PAGES_CONFIG.items():
            form_class = config.get('form')
            if not form_class:
                continue
            form = form_class()
            defined_fields = set(form._fields.keys())

            metadata_expected = SOA_FORM_FIELD_METADATA.get(page) or []
            for field_name in _iter_field_names(metadata_expected):
                assert field_name in defined_fields, (
                    f"SOA_FORM_FIELD_METADATA[{page!r}] references field '{field_name}', "
                    "but the corresponding form is missing it."
                )

            form_fields_meta = config.get('form_fields') or []
            for field_name in _iter_field_names(form_fields_meta):
                assert field_name in defined_fields, (
                    f"STATEMENT_PAGES_CONFIG[{page!r}] references field '{field_name}', "
                    "but the corresponding form is missing it."
                )


def test_soa_json_form_fields_excluded():
    definitions = soa_registry._load_page_definitions()  # type: ignore[attr-defined]
    for definition in definitions:
        assert not definition.form_fields, (
            f"resources/config/soa_pages.json should not define form_fields (found in {definition.key})"
        )
