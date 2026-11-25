---
name: trust-layer-test-assurance
description: QA a pull request for Flylo-Air testing controls TL-TST-001 through TL-TST-006 (POL-SDLC-003). Use when checking tests, CI, QA notes, or whether a missing test was recorded as a gap.
---

# Test Assurance Agent

Policy owner: Flylo-Air
Policy: POL-SDLC-003
Standards: STD-SDLC-003

Read the rows in `trust-layer/controls/catalog.yaml` whose `owning_agent` is `test-assurance`. Flylo-Air owns the policy text. Do not look for it in this repository.

## Scope

Pull requests that change Go, TypeScript, TSX, JavaScript, or Python behavior, tests, or the workflows that run them. Documentation-only diffs make TL-TST-001 through TL-TST-006 not applicable.

## Controls

### TL-TST-001

Pass when a changed behavior has a test that would fail if that behavior regressed. Gap when production code changes and no related test does. A new test file whose cases do not cover the change is still a gap.

### TL-TST-002

Pass when the head SHA has a successful `Backend unit tests (short)` run for Go changes and a successful `Frontend lint and typecheck` run for frontend changes. Pending or red checks are a gap. Those short Go shards are not evidence for TL-TST-005.

### TL-TST-003

Not applicable when the diff does not touch authorization, query construction, or HTML encoding. Otherwise pass only when a test asserts the denied, rejected, or encoded case. Unit success without that assertion is a gap.

### TL-TST-004

Pass when TL-TST-001 passes, or when a gap or waiver evidence record for TL-TST-001 or TL-TST-004 exists on the head SHA. Silence is a gap.

### TL-TST-005

Not applicable unless the diff touches `pkg/api`, `pkg/storage`, `pkg/services/sqlstore/migrations`, or protobuf. When it applies, pass only with an integration or contract test that actually ran. `go test -short` does not pass this control.

### TL-TST-006

Not applicable unless the diff changes user-visible behavior under `public/app`, `packages/grafana-ui`, or a user-facing package. Otherwise pass only with a QA evidence record or a human QA note naming the scenario. Bugbot and typecheck do not count.

## Inputs

- Changed files and the diff
- Check runs on the head SHA, including Fieldsphere CI job names
- Test files added or edited
- Catalog rows for `test-assurance`
- Evidence records on the head SHA

## Decision

Do not treat a green lint job as behavioral coverage. Do not pass TL-TST-005 from a short unit shard.

`not_applicable` needs the catalog applicability and a reason tied to this diff.

Verdict is `pass` only when every owned control on this diff is `pass`, `waived`, or `not_applicable`.

Write judged controls as evidence JSON under `trust-layer/evidence/records/`, valid against `trust-layer/evidence/schema.json`.

## Output

Use this format exactly.

```markdown
# PR control-gap report

- Agent: test-assurance
- Policy owner: Flylo-Air
- Policy: POL-SDLC-003
- Standards: STD-SDLC-003
- Repository: <owner/name>
- Pull request: <number>
- Commit: <40-hex SHA>
- Generated at: <ISO-8601 timestamp>

## Verdict

gap

## Findings

| Control | Severity | Result | Finding | Evidence | Remediation |
| --- | --- | --- | --- | --- | --- |
| TL-TST-001 | high | gap | <one sentence> | <URL or path, or none> | <one sentence> |

## Evidence records

- trust-layer/evidence/records/<file>.json
```

Severity is `critical`, `high`, `medium`, `low`, or `info`. Result is `pass`, `gap`, `fail`, `waived`, or `not_applicable`. The Evidence cell is `none` only for `gap` or `fail`.

## Do not

- Do not treat this skill, `trust-layer/README.md`, or `trust-layer/GAPS.md` as Flylo-Air policy.
- Do not rerun the full Grafana suite unless the task asks for a test. Read the check runs first.
- Do not count an AI review comment as QA evidence.
