---
name: trust-layer-threat-model
description: QA a pull request for Flylo-Air design controls TL-DES-001 through TL-DES-003 (POL-SDLC-008). Use when a PR adds an interface, changes authentication, moves a trust boundary, or introduces a new data flow.
---

# Threat Model Agent

Policy owner: Flylo-Air
Policy: POL-SDLC-008
Standards: STD-SDLC-008

Read the rows in `trust-layer/controls/catalog.yaml` whose `owning_agent` is `threat-model`. Flylo-Air owns the policy text. Do not look for it in this repository.

## Scope

Security-relevant design changes. A bug fix inside an existing control, with no new interface and no new data class, is not applicable for all three controls. Say that explicitly. Do not skip the report.

Applicability signals:

- TL-DES-001: new external interface, authentication change, new data store, or a moved trust boundary
- TL-DES-002: new route, API, datasource, or inbound webhook
- TL-DES-003: new field or log that can carry credentials, tokens, personal data, or customer content

## Controls

### TL-DES-001

When it applies, pass only with an evidence record on the head SHA that names assets, actors, and threats, or with an unexpired Flylo-Air waiver citing POL-SDLC-008. A design comment that was not recorded is a gap.

### TL-DES-002

When a new interface appears, pass only with an evidence record listing abuse cases for that interface, including auth bypass, injection, and unexpected callers. Otherwise not applicable.

### TL-DES-003

When a new sensitive flow appears, pass only with an evidence record that states the classification and what must not be logged. Do not invent the classification in the report without writing the record.

## Inputs

- Diff and new API or route declarations
- Catalog rows for `threat-model`
- Evidence records and waivers on the head SHA

## Decision

If you are unsure whether a change is design-level, record a gap, not a pass.

Verdict is `pass` only when every owned control on this diff is `pass`, `waived`, or `not_applicable`.

Write judged controls as evidence JSON under `trust-layer/evidence/records/`, valid against `trust-layer/evidence/schema.json`.

## Output

Use this format exactly.

```markdown
# PR control-gap report

- Agent: threat-model
- Policy owner: Flylo-Air
- Policy: POL-SDLC-008
- Standards: STD-SDLC-008
- Repository: <owner/name>
- Pull request: <number>
- Commit: <40-hex SHA>
- Generated at: <ISO-8601 timestamp>

## Verdict

gap

## Findings

| Control | Severity | Result | Finding | Evidence | Remediation |
| --- | --- | --- | --- | --- | --- |
| TL-DES-001 | high | gap | <one sentence> | <URL or path, or none> | <one sentence> |

## Evidence records

- trust-layer/evidence/records/<file>.json
```

Severity is `critical`, `high`, `medium`, `low`, or `info`. Result is `pass`, `gap`, `fail`, `waived`, or `not_applicable`. The Evidence cell is `none` only for `gap` or `fail`.

## Do not

- Do not treat this skill, `trust-layer/README.md`, or `trust-layer/GAPS.md` as Flylo-Air policy.
- Do not file the threat model only in chat. The evidence record is the artifact.
- Do not change product code while judging this control unless the task asks for a fix.
