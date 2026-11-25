"""Load trust-layer/controls/catalog.yaml.

The catalog is a restricted YAML document: maps, lists, scalars, comments, and
single- or double-quoted strings. The loader rejects anything else so a control
cannot silently change shape.
"""

from __future__ import annotations

from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[1] / "controls" / "catalog.yaml"

REQUIRED_FIELDS = (
    "id",
    "title",
    "description",
    "sdlc_stage",
    "applicability",
    "policy_refs",
    "standard_refs",
    "nist_ssdf",
    "slsa",
    "soc2",
    "owasp_asvs",
    "automated_check",
    "required_evidence",
    "owning_agent",
)

STAGES = {"test", "review", "release"}
AGENTS = {
    "review-control",
    "test-assurance",
    "release-gate",
    "supply-chain",
    "secrets-iac",
    "threat-model",
    "branch-protection",
    "evidence-auditor",
}


class CatalogError(Exception):
    pass


def load_catalog(path: Path | None = None) -> dict:
    catalog_path = path or CATALOG_PATH
    text = catalog_path.read_text(encoding="utf-8")
    document = _parse(text)
    if not isinstance(document, dict):
        raise CatalogError("catalog root must be a mapping")
    _validate_document(document)
    return document


def _validate_document(document: dict) -> None:
    if not isinstance(document.get("policy_owner"), str) or not document["policy_owner"].strip():
        raise CatalogError("policy_owner must name the external policy owner")
    controls = document.get("controls")
    if not isinstance(controls, list) or not controls:
        raise CatalogError("controls must be a non-empty list")
    seen: set[str] = set()
    owners: set[str] = set()
    for index, control in enumerate(controls):
        if not isinstance(control, dict):
            raise CatalogError(f"controls[{index}] must be a mapping")
        missing = [field for field in REQUIRED_FIELDS if field not in control]
        if missing:
            raise CatalogError(f"controls[{index}] missing {missing}")
        control_id = control["id"]
        if control_id in seen:
            raise CatalogError(f"duplicate control id {control_id}")
        seen.add(control_id)
        if control["sdlc_stage"] not in STAGES:
            raise CatalogError(f"{control_id} has sdlc_stage {control['sdlc_stage']!r}")
        if control["owning_agent"] not in AGENTS:
            raise CatalogError(f"{control_id} has owning_agent {control['owning_agent']!r}")
        owners.add(control["owning_agent"])
        for field in ("policy_refs", "standard_refs", "nist_ssdf", "slsa", "soc2", "owasp_asvs"):
            if not isinstance(control[field], list):
                raise CatalogError(f"{control_id} field {field} must be a list")
        if not control["policy_refs"]:
            raise CatalogError(f"{control_id} needs a policy_refs entry")
    missing_owners = AGENTS - owners
    if missing_owners:
        raise CatalogError(f"agents own no controls: {sorted(missing_owners)}")


def _parse(text: str) -> object:
    lines: list[tuple[int, str, int]] = []
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("\t") or "\t" in raw[: len(raw) - len(raw.lstrip(" \t"))]:
            raise CatalogError(f"line {number}: tabs are not allowed")
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip(), number))
    parser = _Parser(lines)
    document = parser.parse_map(0)
    if parser.peek() is not None:
        raise CatalogError(f"line {parser.peek()[2]}: trailing content")
    return document


class _Parser:
    def __init__(self, lines: list[tuple[int, str, int]]) -> None:
        self.lines = lines
        self.index = 0

    def peek(self) -> tuple[int, str, int] | None:
        if self.index >= len(self.lines):
            return None
        return self.lines[self.index]

    def parse_map(self, indent: int) -> dict:
        result: dict = {}
        while True:
            current = self.peek()
            if current is None or current[0] < indent or current[1].startswith("- "):
                break
            if current[0] != indent:
                raise CatalogError(f"line {current[2]}: expected indent {indent}")
            _, text, number = self.lines[self.index]
            self.index += 1
            key, value = self._split_key(text, number)
            if key in result:
                raise CatalogError(f"line {number}: duplicate key {key}")
            result[key] = self._value_for(value, indent, number)
        return result

    def parse_list(self, indent: int) -> list:
        items: list = []
        while True:
            current = self.peek()
            if current is None or current[0] != indent or not current[1].startswith("- "):
                break
            _, text, number = self.lines[self.index]
            self.index += 1
            body = text[2:].strip()
            if body == "":
                items.append(self.parse_map(indent + 2))
                continue
            if _is_mapping_entry(body):
                key, value = self._split_key(body, number)
                item = {key: self._value_for(value, indent, number)}
                item.update(self.parse_map(indent + 2))
                items.append(item)
                continue
            items.append(_scalar(body, number))
        if not items:
            current = self.peek()
            where = f"line {current[2]}" if current else "end of file"
            raise CatalogError(f"{where}: expected a list")
        return items

    def _value_for(self, value: str, indent: int, number: int) -> object:
        if value != "":
            return _scalar(value, number)
        current = self.peek()
        if current is None or current[0] <= indent:
            raise CatalogError(f"line {number}: expected a nested value")
        if current[1].startswith("- "):
            return self.parse_list(current[0])
        return self.parse_map(current[0])

    def _split_key(self, text: str, number: int) -> tuple[str, str]:
        if text.startswith("- "):
            raise CatalogError(f"line {number}: expected a key")
        key, separator, rest = text.partition(":")
        if separator != ":" or not key.strip():
            raise CatalogError(f"line {number}: expected key: value")
        return key.strip(), rest.strip()


def _is_mapping_entry(body: str) -> bool:
    if body.startswith(("'", '"')):
        return False
    key, separator, _rest = body.partition(":")
    return separator == ":" and bool(key.strip()) and " " not in key.strip()


def _scalar(value: str, number: int) -> object:
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        body = value[1:-1]
        if value[0] == "'":
            return body.replace("''", "'")
        return body.replace('\\"', '"').replace("\\\\", "\\")
    if value in {"true", "false", "null"}:
        raise CatalogError(f"line {number}: quote scalars that would be YAML booleans or null")
    if ": " in value or value.endswith(":"):
        raise CatalogError(f"line {number}: quote scalars that contain a colon")
    return value
