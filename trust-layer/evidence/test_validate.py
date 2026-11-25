import copy
import json
import unittest
from pathlib import Path

import validate

EXAMPLE = Path(__file__).with_name("examples") / "pr-evidence.example.json"
SCHEMA = Path(__file__).with_name("schema.json")


def record():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


class ValidateTests(unittest.TestCase):
    def test_example_and_schema_load(self):
        schema = validate.load_schema(SCHEMA)
        self.assertEqual(validate.validate_instance(record(), schema), [])
        self.assertEqual(validate.validate_file(EXAMPLE, schema), [])

    def test_missing_required_field(self):
        payload = record()
        del payload["commit_sha"]
        errors = validate.validate_instance(payload)
        self.assertTrue(any("commit_sha" in error for error in errors))

    def test_bad_sha_and_extra_property(self):
        payload = record()
        payload["commit_sha"] = "abc"
        payload["note"] = "extra"
        errors = validate.validate_instance(payload)
        self.assertTrue(any("commit_sha" in error for error in errors))
        self.assertTrue(any("note" in error for error in errors))

    def test_pass_without_artifact(self):
        payload = record()
        payload["artifacts"] = []
        errors = validate.validate_instance(payload)
        self.assertTrue(any("artifacts" in error for error in errors))

    def test_gap_requires_finding(self):
        payload = record()
        payload["result"] = "gap"
        errors = validate.validate_instance(payload)
        self.assertTrue(any("finding" in error for error in errors))

    def test_waived_requires_waiver(self):
        payload = record()
        payload["result"] = "waived"
        payload["finding"] = "Accepted for this head only."
        errors = validate.validate_instance(payload)
        self.assertTrue(any("waiver" in error for error in errors))

    def test_manual_requires_attestation(self):
        payload = record()
        payload["check"]["method"] = "manual"
        errors = validate.validate_instance(payload)
        self.assertTrue(any("attestation" in error or "attested" in error for error in errors))

    def test_manual_attestation_passes(self):
        payload = record()
        payload["check"]["method"] = "hybrid"
        payload["attestation"] = {
            "status": "attested",
            "reviewer": "octocat",
            "statement": "I inspected the diff.",
            "timestamp": "2026-11-25T00:41:00Z",
        }
        self.assertEqual(validate.validate_instance(payload), [])

    def test_bad_timestamp_and_bool_pull_request(self):
        payload = record()
        payload["timestamp"] = "2026-11-25"
        payload["pull_request"] = True
        errors = validate.validate_instance(payload)
        self.assertTrue(any("timestamp" in error for error in errors))
        self.assertTrue(any("pull_request" in error for error in errors))

    def test_unknown_schema_keyword_fails_closed(self):
        with self.assertRaises(validate.ValidationError):
            validate._check_keywords({"type": "object", "oneOf": []}, "$")

    def test_expired_shape_still_valid_json(self):
        payload = record()
        payload["result"] = "waived"
        payload["finding"] = "Waiver recorded."
        payload["waiver"] = {
            "approver": "flylo-air-change-board",
            "expires": "2026-12-01T00:00:00Z",
            "residual_risk": "Review thread stays open until the next patch.",
            "policy_refs": ["POL-SDLC-002"],
        }
        self.assertEqual(validate.validate_instance(payload), [])
        unused = copy.deepcopy(payload)
        self.assertEqual(unused["waiver"]["approver"], "flylo-air-change-board")
