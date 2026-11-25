---
name: trust-layer-secrets-iac
description: QA a pull request for Flylo-Air secrets and workflow-trust controls TL-SEC-001 through TL-SEC-005 (POL-SDLC-006). Use when a PR might add credentials, change GitHub Actions permissions, or touch deploy identity.
---

# Secrets and IaC Agent

Policy owner: Flylo-Air
Policy: POL-SDLC-006
Standards: STD-SDLC-006

Read the rows in `trust-layer/controls/catalog.yaml` whose `owning_agent` is `secrets-iac`. Flylo-Air owns the policy text. Do not look for it in this repository.

## Scope

TL-SEC-001 and TL-SEC-002 apply to every pull request that changes files. TL-SEC-003 applies when `.github/workflows` or `.github/actions` change. TL-SEC-004 applies to `.github/workflows/trust-layer-pr-review.yml` on every pull request. TL-SEC-005 applies when deploy, Docker publish, or OIDC permissions change.

## Controls

### TL-SEC-001

Fail when the diff adds a private key, cloud token, or credential assignment. Pass only after the diff was inspected and was clean. Report the file path, never the secret value.

### TL-SEC-002

Pass only when a secret scanner ran on the head SHA and the run URL is the evidence. The archived Trufflehog workflow is not an active scanner. No run is a gap.

### TL-SEC-003

Pass when added permissions stay at `contents: read` or equally narrow, with `pull-requests: write` or `actions: write` only where the job needs them. `contents: write`, `id-token: write`, or `pull_request_target` combined with a write token or a secret is a fail unless a justification record exists. Prefer fail for `pull_request_target` plus secrets.

### TL-SEC-004

Pass when `trust-layer-pr-review.yml` has no `secrets.` context. `github.token` is the workflow token and is allowed. Any repository secret reference is a fail.

### TL-SEC-005

Not applicable when deploy identity does not change. Otherwise pass only with an evidence record that states which identity the workflow can assume.

## Inputs

- Full diff, especially added lines
- `.github/workflows/**` and `.github/actions/**`
- Check runs whose names mention secret scanning or Trufflehog
- Catalog rows for `secrets-iac`
- Evidence records on the head SHA

## Decision

Do not pass TL-SEC-002 because you personally saw no secret. The control requires a scanner run.

Verdict is `pass` only when every owned control on this diff is `pass`, `waived`, or `not_applicable`. A secret in the diff is `fail`, not `gap`.

Write judged controls as evidence JSON under `trust-layer/evidence/records/`, valid against `trust-layer/evidence/schema.json`. Do not put the secret in the JSON.

## Output

Use this format exactly.

```markdown
# PR control-gap report

- Agent: secrets-iac
- Policy owner: Flylo-Air
- Policy: POL-SDLC-006
- Standards: STD-SDLC-006
- Repository: <owner/name>
- Pull request: <number>
- Commit: <40-hex SHA>
- Generated at: <ISO-8601 timestamp>

## Verdict

fail

## Findings

| Control | Severity | Result | Finding | Evidence | Remediation |
| --- | --- | --- | --- | --- | --- |
| TL-SEC-001 | critical | fail | <one sentence, no secret value> | <path> | <one sentence> |

## Evidence records

- trust-layer/evidence/records/<file>.json
```

Severity is `critical`, `high`, `medium`, `low`, or `info`. Result is `pass`, `gap`, `fail`, `waived`, or `not_applicable`. The Evidence cell is `none` only for `gap` or `fail`.

## Do not

- Do not treat this skill, `trust-layer/README.md`, or `trust-layer/GAPS.md` as Flylo-Air policy.
- Do not copy a secret into the report, the evidence file, or a comment.
- Do not rotate or revoke credentials unless the task explicitly asks. Tell the author to revoke them.
