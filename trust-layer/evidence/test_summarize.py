import json
import unittest
from pathlib import Path

import summarize

EXAMPLE = json.loads((Path(__file__).with_name("examples") / "pr-evidence.example.json").read_text(encoding="utf-8"))
HEAD = "0123456789abcdef0123456789abcdef01234567"


def summary_for(files, records):
    return summarize.build_summary(
        changed_files=files,
        records=records,
        head_sha=HEAD,
        repository="fieldsphere/grafana",
        pull_request=42,
        generated_at="2026-11-25T00:45:00Z",
    )


class SummarizeTests(unittest.TestCase):
    def test_code_paths(self):
        self.assertTrue(summarize.code_touched(["pkg/api/foo.go"]))
        self.assertTrue(summarize.code_touched(["trust-layer/controls/catalog.yaml"]))
        self.assertFalse(summarize.code_touched(["docs/sources/readme.md"]))
        self.assertFalse(summarize.code_touched(["trust-layer/README.md"]))

    def test_missing_records_are_a_gap(self):
        body, touched = summary_for(["pkg/api/foo.go"], [])
        self.assertTrue(touched)
        self.assertIn("Policy owner: Flylo-Air", body)
        self.assertIn("TL-EVD-002", body)
        self.assertIn("| gap |", body)
        self.assertIn("## Verdict\n\ngap", body)

    def test_docs_only_skips_full_catalog_gap_list(self):
        body, touched = summary_for(["docs/sources/readme.md"], [])
        self.assertFalse(touched)
        self.assertIn("not_applicable", body)
        self.assertNotIn("TL-REV-001", body)

    def test_matching_record_is_cited(self):
        payload = json.loads(json.dumps(EXAMPLE))
        payload["control_id"] = "TL-REV-001"
        payload["policy_refs"] = ["POL-SDLC-002"]
        payload["check"]["summary"] = "Human approval is on the head."
        body, _touched = summary_for(["pkg/api/foo.go"], [("trust-layer/evidence/records/TL-REV-001.json", payload)])
        self.assertIn("TL-REV-001", body)
        self.assertIn("trust-layer/evidence/records/TL-REV-001.json", body)

    def test_stale_sha_is_not_coverage(self):
        payload = json.loads(json.dumps(EXAMPLE))
        payload["commit_sha"] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        body, _touched = summary_for(["pkg/api/foo.go"], [("records/old.json", payload)])
        self.assertIn("TL-EVD-004", body)
        self.assertIn("not bound", body)

    def test_expired_waiver_on_the_head_is_a_gap(self):
        payload = json.loads(json.dumps(EXAMPLE))
        payload["result"] = "waived"
        payload["finding"] = "Old waiver."
        payload["waiver"] = {
            "approver": "flylo-air-change-board",
            "expires": "2020-01-01T00:00:00Z",
            "residual_risk": "Stale.",
            "policy_refs": ["POL-SDLC-009"],
        }
        body, _touched = summary_for(["pkg/api/foo.go"], [("records/waiver.json", payload)])
        self.assertIn("TL-EVD-006", body)
        self.assertIn("expired", body)
