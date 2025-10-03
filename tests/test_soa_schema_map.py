from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path

import pytest
import yaml

from app.company.forms.soa.metadata import SOA_FORM_FIELD_METADATA

SCHEMA_PATH = Path("resources/config/soa_schema_map.yaml")
SOA_JSON_PATH = Path("resources/config/soa_pages.json")
PDF_MAP_PATH = Path("resources/config/soa_pdf_map.json")
TEMPLATES_ROOT = Path("app/templates")

_METADATA_KEYS = ("placeholder", "autofocus", "type", "render", "rows")


def _load_schema() -> dict[str, object]:
    schema = yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(schema, dict) and "pages" in schema, "schema must define pages"
    return schema


def _resolve(import_path: str):
    module_path, attr = import_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, attr)


def _generate_json(schema: dict[str, object]) -> dict[str, object]:
    pages = schema.get("pages", {})
    output: list[dict[str, object]] = []
    for key, entry in pages.items():  # type: ignore[assignment]
        entry = dict(entry)  # shallow copy
        page = {
            "key": key,
            "model": entry["model"],
            "form": entry["form"],
            "title": entry.get("title"),
            "total_field": entry.get("total_field"),
            "template": entry.get("template"),
            "summary": entry.get("summary"),
        }
        if entry.get("pl_targets"):
            page["pl_targets"] = entry["pl_targets"]
        if entry.get("query_filter"):
            page["query_filter"] = entry["query_filter"]
        output.append(page)
    return {"pages": output}


def _generate_metadata(schema: dict[str, object]) -> dict[str, list[dict[str, object]]]:
    pages = schema.get("pages", {})
    metadata: dict[str, list[dict[str, object]]] = {}
    for key, entry in pages.items():  # type: ignore[assignment]
        fields_meta: list[dict[str, object]] = []
        for field in entry.get("fields", []):  # type: ignore[attr-defined]
            name = field.get("name")
            if not name:
                continue
            meta_entry: dict[str, object] = {"name": name}
            placeholder = field.get("placeholder")
            if placeholder:
                meta_entry["placeholder"] = placeholder
            if field.get("autofocus"):
                meta_entry["autofocus"] = True
            field_type = field.get("type")
            if field_type and field_type != "string":
                meta_entry["type"] = field_type
            for extra_key in ("render", "rows"):
                if extra_key in field:
                    meta_entry[extra_key] = field[extra_key]
            fields_meta.append(meta_entry)
        metadata[key] = fields_meta
    return metadata


def _generate_pdf_map(schema: dict[str, object]) -> dict[str, str]:
    pages = schema.get("pages", {})
    pdf_map: dict[str, str] = {}
    for key, entry in pages.items():  # type: ignore[assignment]
        pdf_key = entry.get("pdf_key")
        if pdf_key:
            pdf_map[key] = pdf_key
    return pdf_map



def test_schema_map_assets_are_up_to_date():
    schema = _load_schema()

    expected_json = _generate_json(schema)
    actual_json = json.loads(SOA_JSON_PATH.read_text(encoding="utf-8"))
    assert actual_json == expected_json, "resources/config/soa_pages.json is stale; regenerate via generate_soa_assets.py"

    expected_metadata = _generate_metadata(schema)
    assert SOA_FORM_FIELD_METADATA == expected_metadata, "SoA form metadata is stale; regenerate via generate_soa_assets.py"

    expected_pdf_map = _generate_pdf_map(schema)
    actual_pdf_map = json.loads(PDF_MAP_PATH.read_text(encoding="utf-8"))
    assert actual_pdf_map == expected_pdf_map, "SoA PDF map is stale; regenerate via generate_soa_assets.py"


@pytest.mark.parametrize("page_key", sorted(yaml.safe_load(SCHEMA_PATH.read_text(encoding="utf-8"))["pages"].keys()))
def test_schema_map_forms_and_templates_exist(page_key, app):
    schema = _load_schema()
    entry = schema["pages"][page_key]

    template_name = entry["template"]
    template_path = TEMPLATES_ROOT / 'company' / template_name
    assert template_path.exists(), f"Template '{template_name}' not found for page '{page_key}'"

    form_cls = _resolve(entry["form"])
    # WTForms は CSRF メタを明示しないとセッション依存になるためオフにする
    form = form_cls(meta={"csrf": False})
    defined_fields = set(form._fields.keys())

    for field in entry.get("fields", []):  # type: ignore[attr-defined]
        name = field.get("name")
        if not name:
            continue
        assert name in defined_fields, f"Field '{name}' missing on form '{entry['form']}' for page '{page_key}'"
