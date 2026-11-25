---
name: trust-layer-supply-chain
description: QA a pull request for Flylo-Air supply chain controls TL-SC-001 through TL-SC-006 (POL-SDLC-005). Use when a PR changes dependencies, lockfiles, GitHub Actions, Renovate config, an SBOM, or release provenance.
---

# Supply Chain Agent

Policy owner: Flylo-Air
Policy: POL-SDLC-005
Standards: STD-SDLC-005

Read the rows in `trust-layer/controls/catalog.yaml` whose `owning_agent` is `supply-chain`. Flylo-Air owns the policy text. Do not look for it in this repository.

## Scope

TL-SC-001, TL-SC-003, and TL-SC-006 apply when manifests, lockfiles, Dockerfiles, Renovate config, or third-party actions change. TL-SC-002 applies to Go or JavaScript dependency changes. TL-SC-004 and TL-SC-005 apply only when a release is published. Ordinary pull requests mark those two not applicable.

## Controls

### TL-SC-001

Pass only with a human approval on the dependency diff. A Renovate automerge without a human approval is a gap.

### TL-SC-002

For Go changes, pass only when govulncheck succeeded on the head SHA. If it did not run, that is a gap, not a pass. JavaScript dependency changes are a gap unless an evidence record attaches a scan. This fork has no active npm audit workflow.

### TL-SC-003

Pass when `go.mod` and `go.sum` change together, and when `package.json` and `yarn.lock` change together. A manifest without its lockfile is a gap.

### TL-SC-004

Not applicable off a release. On a release, pass only when an SBOM for that version is attached. The archived upstream SBOM workflow is not evidence for this fork.

### TL-SC-005

Not applicable off a release. On a release, pass only when provenance for the artifact digest exists. Do not invent a higher SLSA build level.

### TL-SC-006

Pass when every new or changed third-party `uses` clause is a 40-character SHA. Local `.github/actions/*` actions are exempt. A floating tag or branch is a gap.

## Inputs

- Diff of `go.mod`, `go.sum`, `package.json`, `yarn.lock`, Dockerfiles, `.github/workflows`, `.github/renovate.json5`
- Check runs named govulncheck
- Human reviews
- Catalog rows for `supply-chain`
- Evidence records on the head SHA

## Decision

A green unit-test job does not scan dependencies. Absence of a scanner is a gap.

Verdict is `pass` only when every owned control on this diff is `pass`, `waived`, or `not_applicable`.

Write judged controls as evidence JSON under `trust-layer/evidence/records/`, valid against `trust-layer/evidence/schema.json`.

## Output

Use this format exactly.

```markdown
# PR control-gap report

- Agent: supply-chain
- Policy owner: Flylo-Air
- Policy: POL-SDLC-005
- Standards: STD-SDLC-005
- Repository: <owner/name>
- Pull request: <number>
- Commit: <40-hex SHA>
- Generated at: <ISO-8601 timestamp>

## Verdict

gap

## Findings

| Control | Severity | Result | Finding | Evidence | Remediation |
| --- | --- | --- | --- | --- | --- |
| TL-SC-006 | high | gap | <one sentence> | <URL or path, or none> | <one sentence> |

## Evidence records

- trust-layer/evidence/records/<file>.json
```

Severity is `critical`, `high`, `medium`, `low`, or `info`. Result is `pass`, `gap`, `fail`, `waived`, or `not_applicable`. The Evidence cell is `none` only for `gap` or `fail`.

## Do not

- Do not treat this skill, `trust-layer/README.md`, or `trust-layer/GAPS.md` as Flylo-Air policy.
- Do not bump dependencies or enable automerge.
- Do not print credentials found in a lockfile or workflow. Hand that to the secrets agent.
