---
name: trust-layer-branch-protection
description: QA a pull request for Flylo-Air branch protection controls TL-BR-001 through TL-BR-007 (POL-SDLC-007). Use when checking rulesets, CODEOWNERS, required checks, force-push, or bypass actors.
---

# Branch Protection Agent

Policy owner: Flylo-Air
Policy: POL-SDLC-007
Standards: STD-SDLC-007

Read the rows in `trust-layer/controls/catalog.yaml` whose `owning_agent` is `branch-protection`. Flylo-Air owns the policy text. Do not look for it in this repository.

## Scope

Every code pull request. The desired rules live in `trust-layer/branch-protection/rulesets/` and are mapped in `trust-layer/branch-protection/control-map.json`. Those files are the desired state. They are not evidence that GitHub enforces them.

## Controls

### TL-BR-001

Pass only when live rules for `main` include an active pull request requirement. A JSON file that contains the rule is not a pass.

### TL-BR-002

Pass only when live required checks include `Backend unit tests (short)`, `Frontend lint and typecheck`, and `Trust layer evidence`.

### TL-BR-003

Pass only when the live pull request rule sets `require_code_owner_review`. Also confirm `trust-layer/branch-protection/CODEOWNERS` still lists the trust-layer paths. That fragment is inactive until a Flylo-Air maintainer copies it into `.github/CODEOWNERS`.

### TL-BR-004

Pass only when live rules include `non_fast_forward` and `deletion`.

### TL-BR-005

Pass only when live rules on `release-*.*.*` match `rulesets/release-branches.json`. No release ruleset is a gap.

### TL-BR-006

Diff the ruleset JSON against the live rules API. A difference is a gap. An unreadable API is a gap, not a pass.

### TL-BR-007

The desired files have an empty `bypass_actors` list. A live bypass that is not in the JSON, or that lacks a Flylo-Air waiver, is a gap.

## Inputs

- `trust-layer/branch-protection/rulesets/*.json`
- `trust-layer/branch-protection/control-map.json`
- `trust-layer/branch-protection/CODEOWNERS`
- Live read-only rules for `fieldsphere/grafana` when the token can read them. Use `GET /repos/fieldsphere/grafana/rules/branches/main`.
- Catalog rows for `branch-protection`

## Decision

Do not apply, edit, or delete a live ruleset. Do not add a bypass actor.

If the live API returns only organization lifecycle rules, the branch controls are gaps.

Verdict is `pass` only when every owned control is `pass`, `waived`, or `not_applicable`. These controls are in scope on code pull requests, so not applicable is rare.

Write judged controls as evidence JSON under `trust-layer/evidence/records/`, valid against `trust-layer/evidence/schema.json`.

## Output

Use this format exactly.

```markdown
# PR control-gap report

- Agent: branch-protection
- Policy owner: Flylo-Air
- Policy: POL-SDLC-007
- Standards: STD-SDLC-007
- Repository: <owner/name>
- Pull request: <number>
- Commit: <40-hex SHA>
- Generated at: <ISO-8601 timestamp>

## Verdict

gap

## Findings

| Control | Severity | Result | Finding | Evidence | Remediation |
| --- | --- | --- | --- | --- | --- |
| TL-BR-006 | high | gap | <one sentence> | <URL or path, or none> | <one sentence> |

## Evidence records

- trust-layer/evidence/records/<file>.json
```

Severity is `critical`, `high`, `medium`, `low`, or `info`. Result is `pass`, `gap`, `fail`, `waived`, or `not_applicable`. The Evidence cell is `none` only for `gap` or `fail`.

## Do not

- Do not treat this skill, `trust-layer/README.md`, or `trust-layer/GAPS.md` as Flylo-Air policy.
- Do not push ruleset JSON to GitHub from a review.
- Do not treat `.github/CODEOWNERS` ownership of product paths as coverage for `trust-layer/`.
