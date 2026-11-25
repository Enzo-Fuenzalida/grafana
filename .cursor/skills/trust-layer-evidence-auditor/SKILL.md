---
name: trust-layer-evidence-auditor
description: QA a pull request for Flylo-Air evidence controls TL-EVD-001 through TL-EVD-006 (POL-SDLC-009, and POL-SDLC-001 for coverage). Use when checking evidence JSON, attestations, waivers, or whether every in-scope control was judged.
---

# Evidence Auditor

Policy owner: Flylo-Air
Policy: POL-SDLC-009
Standards: STD-SDLC-001

Also cite POL-SDLC-001 on TL-EVD-002. Flylo-Air owns that policy. The text is not in this repository.

Read the rows in `trust-layer/controls/catalog.yaml` whose `owning_agent` is `evidence-auditor`, and read the other seven agents' reports.

## Scope

Every pull request that changes code, workflows, or trust-layer controls. Run this agent after the other framework agents, or record a gap when their reports are missing.

## Controls

### TL-EVD-001

Pass when `python3 trust-layer/evidence/validate.py` accepts every file in `trust-layer/evidence/records/` and the example record. Any schema error is a fail.

### TL-EVD-002

Pass when every control that is in scope for this diff has a result of pass, fail, gap, waived, or not applicable from its owning agent. A missing row is a gap. The workflow summary listing missing records does not by itself pass this control. You still compare those rows with the other reports.

### TL-EVD-003

Pass when every manual or hybrid record on the head SHA has attestation status `attested` with reviewer, statement, and timestamp. The schema enforces the shape. Also gap when the reviewer of a review control is the pull request author.

### TL-EVD-004

Pass when every covering record uses the pull request head SHA. A record for another SHA does not cover the control.

### TL-EVD-005

Pass only when all eight framework agents have published a control-gap report for the head SHA. The workflow comment from `trust-layer-pr-review.yml` is one evidence summary. It does not replace the other seven reports.

### TL-EVD-006

Not applicable when no record is waived. Otherwise pass only when approver, expiry, residual risk, and a Flylo-Air policy id are present and the expiry is still in the future.

## Inputs

- `trust-layer/evidence/schema.json` and `trust-layer/evidence/records/*.json`
- The other agents' control-gap reports
- Catalog rows and their `owning_agent`
- Pull request head SHA

## Decision

Do not accept prose that says a control passed when no record or report row exists.

Verdict is `pass` only when every owned control is `pass`, `waived`, or `not_applicable`.

Write judged controls as evidence JSON under `trust-layer/evidence/records/`, valid against the schema. A pass needs an artifact.

## Output

Use this format exactly.

```markdown
# PR control-gap report

- Agent: evidence-auditor
- Policy owner: Flylo-Air
- Policy: POL-SDLC-009
- Standards: STD-SDLC-001
- Repository: <owner/name>
- Pull request: <number>
- Commit: <40-hex SHA>
- Generated at: <ISO-8601 timestamp>

## Verdict

gap

## Findings

| Control | Severity | Result | Finding | Evidence | Remediation |
| --- | --- | --- | --- | --- | --- |
| TL-EVD-002 | high | gap | <one sentence> | <URL or path, or none> | <one sentence> |

## Evidence records

- trust-layer/evidence/records/<file>.json
```

Severity is `critical`, `high`, `medium`, `low`, or `info`. Result is `pass`, `gap`, `fail`, `waived`, or `not_applicable`. The Evidence cell is `none` only for `gap` or `fail`.

## Do not

- Do not treat this skill, `trust-layer/README.md`, or `trust-layer/GAPS.md` as Flylo-Air policy.
- Do not weaken the schema to make a record pass.
- Do not mark TL-EVD-005 passed from the workflow comment alone.
