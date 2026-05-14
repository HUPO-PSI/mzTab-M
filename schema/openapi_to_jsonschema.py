#!/usr/bin/env python3
"""Convert mzTab_2_1-M_openapi.yml to a standalone JSON Schema (draft 2020-12).

OpenAPI 3.1 uses JSON Schema 2020-12 for its schema objects, so the conversion
is mostly structural:
  - Move components/schemas  →  $defs
  - Rewrite $ref paths from  #/components/schemas/X  →  #/$defs/X
  - Convert x-mztab-example  →  examples  (JSON Schema array form)
  - Convert singular example  →  prepend to examples
  - Strip non-schema OpenAPI wrapper fields (paths, info, servers, …)

Usage:
    python3 openapi_to_jsonschema.py [--input INPUT] [--output OUTPUT]
"""

import argparse
import json
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
DEFAULT_INPUT = SCRIPT_DIR / "mzTab_2_1-M_openapi.yml"
DEFAULT_OUTPUT = SCRIPT_DIR / "mzTab_2_1-M_openapi.json"

# Top-level OpenAPI keys that are NOT schema-related; never appear inside
# components/schemas but guard against accidental recursion.
_OPENAPI_ROOT_KEYS = {
    "openapi", "info", "paths", "tags", "servers", "externalDocs",
    "x-global-options", "security", "webhooks",
}

# OpenAPI extension keys that appear inside schema objects but carry no
# JSON Schema meaning and should be dropped from the output.
_DROP_SCHEMA_EXTENSIONS = {
    # serialization hints for the Java/Go code generators
}

# Extension keys to KEEP inside schema objects (domain-specific metadata).
# Everything not in _DROP_SCHEMA_EXTENSIONS is kept by default, so this is
# just documentation of intentional keeps.
# "x-mztab-serialize-by-id", "x-mztab-example" (converted), etc.


def _fix_ref(ref: str) -> str:
    return ref.replace("#/components/schemas/", "#/$defs/")


def _to_examples_list(value) -> list:
    """Normalise an x-mztab-example / example value to a list."""
    if isinstance(value, list):
        return value
    return [value]


def transform(obj):
    """Recursively transform an OpenAPI schema node to JSON Schema."""
    if not isinstance(obj, dict):
        if isinstance(obj, list):
            return [transform(item) for item in obj]
        return obj

    result = {}

    # Collect existing examples array (may be empty).
    existing_examples = list(obj.get("examples") or [])

    # Convert singular OpenAPI `example` → prepend to examples list.
    if "example" in obj:
        ex = obj["example"]
        if ex not in existing_examples:
            existing_examples.insert(0, ex)

    # Convert x-mztab-example → examples (takes priority / appended after).
    if "x-mztab-example" in obj:
        for ex in _to_examples_list(obj["x-mztab-example"]):
            if ex not in existing_examples:
                existing_examples.append(ex)

    if existing_examples:
        result["examples"] = existing_examples

    for key, val in obj.items():
        if key in _DROP_SCHEMA_EXTENSIONS:
            continue
        if key in ("example", "x-mztab-example", "examples"):
            continue  # already handled above

        if key == "$ref" and isinstance(val, str):
            result[key] = _fix_ref(val)
        else:
            result[key] = transform(val)

    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", "-o", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as fh:
        openapi = yaml.safe_load(fh)

    info = openapi.get("info", {})
    raw_schemas = openapi.get("components", {}).get("schemas", {})

    defs = {name: transform(schema) for name, schema in raw_schemas.items()}

    output = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://raw.githubusercontent.com/HUPO-PSI/mzTab-M/main/schema/"
            + Path(args.output).name
        ),
        "title": info.get("title", "mzTab-M"),
        "description": info.get("description", ""),
        "$ref": "#/$defs/MzTab",
        "$defs": defs,
    }

    out_path = Path(args.output)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"Generated: {out_path}  ({len(defs)} schema definitions)")


if __name__ == "__main__":
    main()
