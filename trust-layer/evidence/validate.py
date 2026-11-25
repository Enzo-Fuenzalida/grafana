#!/usr/bin/env python3
"""Validate trust-layer evidence records against evidence/schema.json.

The validator implements the JSON Schema draft 2020-12 keywords this schema
uses. It does not accept unknown validation keywords, so a schema change that
adds a keyword fails closed until the validator learns it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.json")

ANNOTATIONS = {"$schema", "$id", "$comment", "title", "description"}
IMPLEMENTED = ANNOTATIONS | {
    "type",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "enum",
    "const",
    "pattern",
    "minLength",
    "minimum",
    "minItems",
    "format",
    "allOf",
    "if",
    "then",
}


class ValidationError(Exception):
    def __init__(self, path: str, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{path}: {message}")


def load_schema(path: Path | None = None) -> dict:
    schema_path = path or SCHEMA_PATH
    with schema_path.open(encoding="utf-8") as handle:
        schema = json.load(handle)
    _check_keywords(schema, "$")
    return schema


def _check_keywords(schema: object, path: str) -> None:
    if not isinstance(schema, dict):
        raise ValidationError(path, "schema must be an object")
    unknown = set(schema) - IMPLEMENTED
    if unknown:
        raise ValidationError(path, f"schema uses unknown keywords: {sorted(unknown)}")
    properties = schema.get("properties")
    if isinstance(properties, dict):
        for name, sub in properties.items():
            _check_keywords(sub, f"{path}.properties.{name}")
    items = schema.get("items")
    if isinstance(items, dict):
        _check_keywords(items, f"{path}.items")
    for keyword in ("if", "then"):
        if isinstance(schema.get(keyword), dict):
            _check_keywords(schema[keyword], f"{path}.{keyword}")
    for index, sub in enumerate(schema.get("allOf", [])):
        _check_keywords(sub, f"{path}.allOf[{index}]")


def validate_instance(instance: object, schema: dict | None = None) -> list[str]:
    active = schema if schema is not None else load_schema()
    errors: list[str] = []
    _validate(instance, active, "$", errors)
    return errors


def validate_file(path: Path, schema: dict | None = None) -> list[str]:
    try:
        with path.open(encoding="utf-8") as handle:
            instance = json.load(handle)
    except json.JSONDecodeError as exc:
        return [f"$: invalid JSON ({exc})"]
    return validate_instance(instance, schema)


def _validate(instance: object, schema: dict, path: str, errors: list[str]) -> None:
    unknown = set(schema) - IMPLEMENTED
    if unknown:
        errors.append(f"{path}: schema uses unknown keywords {sorted(unknown)}")
        return

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not one of {schema['enum']!r}")

    expected = schema.get("type")
    if expected is not None and not _type_ok(instance, expected):
        errors.append(f"{path}: expected {expected}")
        return

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than {schema['minLength']}")
        if "pattern" in schema and re.fullmatch(schema["pattern"], instance) is None:
            errors.append(f"{path}: does not match {schema['pattern']}")
        if schema.get("format") == "date-time":
            _check_date_time(instance, path, errors)
        elif "format" in schema:
            errors.append(f"{path}: unsupported format {schema['format']!r}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")

    if isinstance(instance, list) and "minItems" in schema and len(instance) < schema["minItems"]:
        errors.append(f"{path}: fewer than {schema['minItems']} items")

    if "items" in schema and isinstance(instance, list):
        for index, item in enumerate(instance):
            _validate(item, schema["items"], f"{path}[{index}]", errors)

    if expected == "object" or (expected is None and isinstance(instance, dict)):
        if isinstance(instance, dict):
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            for key in required:
                if key not in instance:
                    errors.append(f"{path}: missing required property {key!r}")
            additional = schema.get("additionalProperties", True)
            for key, value in instance.items():
                if key in properties:
                    _validate(value, properties[key], f"{path}.{key}", errors)
                elif additional is False:
                    errors.append(f"{path}: unexpected property {key!r}")

    if "allOf" in schema:
        for sub in schema["allOf"]:
            _validate(instance, sub, path, errors)

    if "if" in schema:
        branch_errors: list[str] = []
        _validate(instance, schema["if"], path, branch_errors)
        if not branch_errors and "then" in schema:
            _validate(instance, schema["then"], path, errors)


def _type_ok(instance: object, expected: str) -> bool:
    if expected == "object":
        return isinstance(instance, dict)
    if expected == "array":
        return isinstance(instance, list)
    if expected == "string":
        return isinstance(instance, str)
    if expected == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    if expected == "boolean":
        return isinstance(instance, bool)
    if expected == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    return False


def _check_date_time(value: str, path: str, errors: list[str]) -> None:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value):
        errors.append(f"{path}: not an RFC 3339 date-time")
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path}: not an RFC 3339 date-time")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate trust-layer evidence JSON files.")
    parser.add_argument("files", nargs="*", type=Path, help="Evidence JSON files")
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument(
        "--records-dir",
        type=Path,
        help="Validate every *.json file under this directory",
    )
    args = parser.parse_args(argv)

    try:
        schema = load_schema(args.schema)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        print(f"schema: {exc}", file=sys.stderr)
        return 2

    paths = list(args.files)
    if args.records_dir:
        if args.records_dir.is_dir():
            paths.extend(sorted(args.records_dir.glob("*.json")))
        else:
            print(f"{args.records_dir}: records directory not found", file=sys.stderr)
            return 2

    if not paths:
        parser.error("provide evidence files or --records-dir")

    failed = False
    for path in paths:
        errors = validate_file(path, schema)
        if errors:
            failed = True
            print(f"{path}: invalid")
            for error in errors:
                print(f"  {error}")
        else:
            print(f"{path}: ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
