import json
import unittest
from pathlib import Path

import catalog
import validate

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".cursor" / "skills"
AGENTS = {
    "review-control": "trust-layer-review-control",
    "test-assurance": "trust-layer-test-assurance",
    "release-gate": "trust-layer-release-gate",
    "supply-chain": "trust-layer-supply-chain",
    "secrets-iac": "trust-layer-secrets-iac",
    "threat-model": "trust-layer-threat-model",
    "branch-protection": "trust-layer-branch-protection",
    "evidence-auditor": "trust-layer-evidence-auditor",
}


class RepoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = catalog.load_catalog()

    def test_policy_owner_is_flylo_air(self):
        self.assertEqual(self.catalog["policy_owner"], "Flylo-Air")
        for document in self.catalog["external_documents"]:
            self.assertEqual(document["owner"], "Flylo-Air")
            self.assertEqual(document["system"], "external")

    def test_every_control_has_an_agent_and_is_cited(self):
        seen = set()
        for control in self.catalog["controls"]:
            self.assertNotIn(control["id"], seen)
            seen.add(control["id"])
            skill = (SKILLS / AGENTS[control["owning_agent"]] / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Flylo-Air", skill)
            self.assertIn(control["id"], skill)
            for policy_id in control["policy_refs"]:
                self.assertIn(policy_id, skill)
            for standard_id in control["standard_refs"]:
                self.assertIn(standard_id, skill)
            self.assertNotIn("trust-layer/policies", skill)
            self.assertNotIn("trust-layer/procedures", skill)

    def test_no_policy_or_procedure_tree(self):
        trust = ROOT / "trust-layer"
        self.assertFalse((trust / "policies").exists())
        self.assertFalse((trust / "procedures").exists())

    def test_readme_points_at_flylo_air_and_not_local_policy(self):
        readme = (ROOT / "trust-layer" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Flylo-Air", readme)
        self.assertIn("```mermaid", readme)
        self.assertNotIn("trust-layer/policies", readme)
        self.assertNotIn("trust-layer/procedures", readme)

    def test_rulesets_map_to_real_controls(self):
        control_ids = {control["id"] for control in self.catalog["controls"]}
        base = ROOT / "trust-layer" / "branch-protection"
        mapping = json.loads((base / "control-map.json").read_text(encoding="utf-8"))
        self.assertEqual(mapping["policy_owner"], "Flylo-Air")
        for ruleset in mapping["rulesets"]:
            payload = json.loads((base / ruleset["file"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["bypass_actors"], [])
            types = {rule["type"] for rule in payload["rules"]}
            self.assertIn("pull_request", types)
            self.assertIn("deletion", types)
            self.assertIn("non_fast_forward", types)
            checks = next(rule for rule in payload["rules"] if rule["type"] == "required_status_checks")
            contexts = {item["context"] for item in checks["parameters"]["required_status_checks"]}
            self.assertIn("Trust layer evidence", contexts)
            for control_id in ruleset["controls"]:
                self.assertIn(control_id, control_ids)

    def test_workflow_parses_and_stays_narrow(self):
        path = ROOT / ".github" / "workflows" / "trust-layer-pr-review.yml"
        workflow = _parse_workflow(path.read_text(encoding="utf-8"))
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("pull_request_target", text)
        self.assertNotIn("${{ secrets", text)
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        evidence = workflow["jobs"]["evidence"]
        self.assertEqual(evidence["name"], "Trust layer evidence")
        self.assertEqual(evidence["permissions"]["contents"], "read")
        self.assertNotIn("pull-requests", evidence["permissions"])
        comment = workflow["jobs"]["comment"]
        self.assertEqual(comment["permissions"]["contents"], "read")
        self.assertEqual(comment["permissions"]["pull-requests"], "write")
        self.assertNotIn("secrets", comment["permissions"])
        example = ROOT / "trust-layer" / "evidence" / "examples" / "pr-evidence.example.json"
        self.assertEqual(validate.validate_file(example), [])


def _parse_workflow(text: str) -> dict:
    """Parse the trust-layer workflow. Block scalars and maps only, no anchors."""
    lines = text.splitlines()
    index = 0

    def next_content(start: int) -> int | None:
        for cursor in range(start, len(lines)):
            stripped = lines[cursor].strip()
            if stripped and not stripped.startswith("#"):
                return cursor
        return None

    def parse_block(indent: int) -> object:
        nonlocal index
        current = next_content(index)
        if current is None:
            raise AssertionError("expected YAML content")
        if _indent(lines[current]) != indent:
            raise AssertionError(f"line {current + 1}: expected indent {indent}")
        if lines[current].lstrip().startswith("- "):
            return parse_list(indent)
        return parse_map(indent)

    def parse_map(indent: int) -> dict:
        nonlocal index
        result = {}
        while True:
            current = next_content(index)
            if current is None or _indent(lines[current]) < indent:
                break
            if _indent(lines[current]) != indent or lines[current].lstrip().startswith("- "):
                break
            index = current + 1
            key, raw_value = _split_key(lines[current], current)
            result[key] = parse_value(raw_value, indent, current)
        return result

    def parse_list(indent: int) -> list:
        nonlocal index
        items = []
        while True:
            current = next_content(index)
            if current is None or _indent(lines[current]) != indent or not lines[current].lstrip().startswith("- "):
                break
            index = current + 1
            body = lines[current].lstrip()[2:]
            if body == "" or body == "|":
                items.append(parse_block(indent + 2))
                continue
            if ":" in body and not body.startswith(("'", '"')):
                key, raw_value = _split_key(body, current)
                item = {key: parse_value(raw_value, indent, current)}
                extra = next_content(index)
                if extra is not None and _indent(lines[extra]) > indent:
                    item.update(parse_map(_indent(lines[extra])))
                items.append(item)
                continue
            items.append(_scalar(body))
        return items

    def parse_value(raw_value: str, indent: int, line_number: int) -> object:
        nonlocal index
        value = raw_value.strip()
        if value in {"|", "|-"}:
            return parse_literal(indent)
        if value == "":
            nested = next_content(index)
            if nested is None or _indent(lines[nested]) <= indent:
                raise AssertionError(f"line {line_number + 1}: missing nested value")
            return parse_block(_indent(lines[nested]))
        return _scalar(value)

    def parse_literal(indent: int) -> str:
        nonlocal index
        collected = []
        while index < len(lines):
            if lines[index].strip() == "":
                collected.append("")
                index += 1
                continue
            if _indent(lines[index]) <= indent:
                break
            collected.append(lines[index].strip())
            index += 1
        return "\n".join(collected).strip()

    document = parse_block(0)
    if not isinstance(document, dict):
        raise AssertionError("workflow root must be a mapping")
    return document


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _split_key(text: str, line_number: int) -> tuple[str, str]:
    body = text.strip()
    key, separator, rest = body.partition(":")
    if separator != ":":
        raise AssertionError(f"line {line_number + 1}: expected a key")
    return key.strip(), rest


def _scalar(value: str) -> object:
    body = value.split(" #", 1)[0].strip()
    if len(body) >= 2 and body[0] == body[-1] and body[0] in {"'", '"'}:
        return body[1:-1]
    return body


if __name__ == "__main__":
    unittest.main()
