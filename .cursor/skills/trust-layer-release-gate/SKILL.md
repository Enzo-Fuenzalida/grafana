---
name: trust-layer-release-gate
description: QA a pull request for Flylo-Air release controls TL-REL-001 through TL-REL-006 (POL-SDLC-004). Use when reviewing a release, tag, changelog, migration, or merge to a release branch.
---

# Release Gate Agent

Policy owner: Flylo-Air
Policy: POL-SDLC-004
Standards: STD-SDLC-004

Read the rows in `trust-layer/controls/catalog.yaml` whose `owning_agent` is `release-gate`. Flylo-Air owns the policy text. Do not look for it in this repository.

## Scope

Every code pull request gets TL-REL-001 and TL-REL-003. TL-REL-002, TL-REL-004, and TL-REL-006 apply to release publication, tags, and release-branch merges. TL-REL-005 applies to user-visible changes. Say not applicable when the catalog says the control is not in scope. Do not pass those controls early.

## Controls

### TL-REL-001

Pass when the report or evidence record links the pull request, head SHA, human approval URL, and CI URL. A release change also needs the release workflow URL. A missing link is a gap.

### TL-REL-002

Not applicable on an ordinary product pull request. On a release, tag, or release-verification change, pass only when package verification succeeded for that artifact. Pull request unit tests are not release verification.

### TL-REL-003

Pass with the finding that `git revert` is the rollback when the diff has no migration and no destructive data change. A migration or destructive change without a rollback note is a gap.

### TL-REL-004

Not applicable on an open pull request into `main`, because the releaser is not known yet. Say that in the finding. On a release-branch merge or publish, pass only when the publisher is not the author.

### TL-REL-005

Not applicable for internal-only diffs when the pull request body says so. User-visible changes pass only with a changelog hunk or an equivalent release note. Neither is a gap.

### TL-REL-006

Not applicable when nothing is published. A published artifact passes only with a checksum or signature a consumer can recompute.

## Inputs

- Diff, pull request body, labels, and head SHA
- Approvals and check runs
- Release workflow files under `.github/workflows/release-*.yml` and `create-release-*.yml`
- Catalog rows for `release-gate`
- Evidence records on the head SHA

## Decision

Do not treat the existence of an upstream release workflow as evidence that this pull request was verified.

Verdict is `pass` only when every owned control on this diff is `pass`, `waived`, or `not_applicable`.

Write judged controls as evidence JSON under `trust-layer/evidence/records/`, valid against `trust-layer/evidence/schema.json`.

## Output

Use this format exactly.

```markdown
# PR control-gap report

- Agent: release-gate
- Policy owner: Flylo-Air
- Policy: POL-SDLC-004
- Standards: STD-SDLC-004
- Repository: <owner/name>
- Pull request: <number>
- Commit: <40-hex SHA>
- Generated at: <ISO-8601 timestamp>

## Verdict

gap

## Findings

| Control | Severity | Result | Finding | Evidence | Remediation |
| --- | --- | --- | --- | --- | --- |
| TL-REL-002 | high | gap | <one sentence> | <URL or path, or none> | <one sentence> |

## Evidence records

- trust-layer/evidence/records/<file>.json
```

Severity is `critical`, `high`, `medium`, `low`, or `info`. Result is `pass`, `gap`, `fail`, `waived`, or `not_applicable`. The Evidence cell is `none` only for `gap` or `fail`.

## Do not

- Do not treat this skill, `trust-layer/README.md`, or `trust-layer/GAPS.md` as Flylo-Air policy.
- Do not tag, publish, or merge.
- Do not claim an SLSA build level the artifact does not have.
