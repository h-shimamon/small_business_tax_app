#!/usr/bin/env python3
"""Generate Statement of Accounts assets from a single schema map."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "resources" / "config" / "soa_schema_map.yaml"
OUTPUT_JSON = PROJECT_ROOT / "resources" / "config" / "soa_pages.json"
METADATA_PATH = PROJECT_ROOT / "app" / "company" / "forms" / "soa" / "metadata.py"
PDF_SCHEMA_PATH = PROJECT_ROOT / "resources" / "config" / "soa_pdf_map.json"

_METADATA_KEYS = ("placeholder", "autofocus", "type", "render", "rows")
_OUTPUT_KEYS = ("name",) + _METADATA_KEYS


def load_schema(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "pages" not in data:
        raise ValueError("schema map must define a 'pages' dictionary")
    return data


def generate_json(schema: dict[str, Any]) -> dict[str, Any]:
    pages: dict[str, Any] = schema.get("pages", {})
    json_pages: list[dict[str, Any]] = []
    for key, entry in pages.items():
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
        json_pages.append(page)
    return {"pages": json_pages}


def generate_metadata(schema: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    pages: dict[str, Any] = schema.get("pages", {})
    metadata: dict[str, list[dict[str, Any]]] = {}
    for key, entry in pages.items():
        meta_fields: list[dict[str, Any]] = []
        for field in entry.get("fields", []):
            name = field.get("name")
            if not name:
                continue
            meta_entry: dict[str, Any] = {"name": name}
            placeholder = field.get("placeholder")
            if placeholder:
                meta_entry["placeholder"] = placeholder
            if field.get("autofocus") is True:
                meta_entry["autofocus"] = True
            field_type = field.get("type")
            if field_type and field_type != "string":
                meta_entry["type"] = field_type
            for extra_key in ("render", "rows"):
                if extra_key in field:
                    meta_entry[extra_key] = field[extra_key]
            meta_fields.append(meta_entry)
        metadata[key] = meta_fields
    return metadata


def write_json(payload: dict[str, Any]) -> None:
    OUTPUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_metadata(metadata: dict[str, list[dict[str, Any]]]) -> None:
    header = (
        '"""Auto-generated SoA form field metadata.\n\n'
        'Do not edit manually. Run `python scripts/generate_soa_assets.py`.\n"""\n'
        "from __future__ import annotations\n\n"
        "SOA_FORM_FIELD_METADATA: dict[str, list[dict[str, object]]] = {\n"
    )
    lines: list[str] = [header]
    for page, fields in metadata.items():
        lines.append(f"    '{page}': [\n")
        for field_meta in fields:
            pieces: list[str] = []
            for key in _OUTPUT_KEYS:
                value = field_meta.get(key)
                if value is None:
                    continue
                pieces.append(f"'{key}': {repr(value)}")
            if not pieces:
                continue
            lines.append(f"        {{{', '.join(pieces)}}},\n")
        lines.append("    ],\n")
    lines.append("}\n\n__all__ = ['SOA_FORM_FIELD_METADATA']\n")
    METADATA_PATH.write_text(''.join(lines), encoding="utf-8")


def collect_pdf_keys(schema: dict[str, Any]) -> dict[str, str]:
    pages: dict[str, Any] = schema.get("pages", {})
    output: dict[str, str] = {}
    for key, entry in pages.items():
        pdf_key = entry.get("pdf_key")
        if pdf_key:
            output[key] = pdf_key
    return output


def write_pdf_map(pdf_map: dict[str, str]) -> None:
    payload = json.dumps(pdf_map, ensure_ascii=False, indent=2) + "\n"
    PDF_SCHEMA_PATH.write_text(payload, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SoA assets from schema map")
    parser.parse_args()

    schema = load_schema(SCHEMA_PATH)
    json_payload = generate_json(schema)
    write_json(json_payload)
    metadata = generate_metadata(schema)
    write_metadata(metadata)
    pdf_map = collect_pdf_keys(schema)
    write_pdf_map(pdf_map)


if __name__ == "__main__":
    main()
