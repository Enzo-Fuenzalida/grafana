---
name: trust-layer-review-control
description: QA a pull request for Flylo-Air secure code review controls TL-REV-001 through TL-REV-005 (POL-SDLC-002). Use when reviewing a PR, when Bugbot or another AI reviewer has commented, or when checking whether human approval is enough to merge.
---

# Review Control Agent

Policy owner: Flylo-Air
Policy: POL-SDLC-002
Standards: STD-SDLC-002

Read the rows in `trust-layer/controls/catalog.yaml` whose `owning_agent` is `review-control`. Flylo-Air owns the policy text. Do not look for it in this repository.

## Scope

Every pull request that can merge to `main` or a `release-*` branch. Docs-only diffs still get TL-REV-001, TL-REV-002, TL-REV-004, and TL-REV-005. TL-REV-003 is not applicable when the diff has none of the sensitive signals below.

Sensitive signals:

- paths under `pkg/services/auth`, `pkg/services/accesscontrol`, `pkg/middleware`, or `pkg/api`
- filenames containing `auth`, `session`, `crypto`, `secret`, `token`, or `password`
- `.github/workflows` permission or `uses` changes
- diff hunks that add string-built SQL, `template.HTML`, `os/exec`, or `html/template` without escaping

## Controls

### TL-REV-001

Pass only when an APPROVED review is from a human who is not the author. Gap when there is no such review. Bugbot does not count.

### TL-REV-002

Pass when no approving review belongs to the pull request author. Gap when the author approved the pull request, even if GitHub counts that approval.

### TL-REV-003

Not applicable when no sensitive signal is present. Otherwise pass only when a human review comment or an evidence record on the head SHA discusses those files. Silence is a gap.

### TL-REV-004

Pass when a non-bot approval exists, or when no bot review exists. Gap or fail when the only approval is Bugbot or another bot.

### TL-REV-005

Pass when every review thread is resolved. A Flylo-Air waiver record may waive named threads. Unresolved threads without a waiver are a gap.

## Inputs

- Diff, author login, and head SHA
- Reviews, review threads, and bot comments
- Catalog rows for `review-control`
- `trust-layer/evidence/records/*.json` whose `commit_sha` equals the head

## Decision

Inspect the inputs. Do not pass a control you could not read. An unreadable review API is a gap.

`not_applicable` is allowed only when the catalog applicability says so, and the finding must say why this diff qualifies.

Verdict is `pass` only when every owned control on this diff is `pass`, `waived`, or `not_applicable`. Any `gap` or `fail` makes the verdict `gap`.

Write one evidence JSON file per control you actually judged, under `trust-layer/evidence/records/`, valid against `trust-layer/evidence/schema.json`. A pass needs an artifact URI.

## Output

Use this format exactly.

```markdown
# PR control-gap report

- Agent: review-control
- Policy owner: Flylo-Air
- Policy: POL-SDLC-002
- Standards: STD-SDLC-002
- Repository: <owner/name>
- Pull request: <number>
- Commit: <40-hex SHA>
- Generated at: <ISO-8601 timestamp>

## Verdict

pass

## Findings

| Control | Severity | Result | Finding | Evidence | Remediation |
| --- | --- | --- | --- | --- | --- |
| TL-REV-001 | high | gap | <one sentence> | <URL or path, or none> | <one sentence> |

## Evidence records

- trust-layer/evidence/records/<file>.json
```

Severity is `critical`, `high`, `medium`, `low`, or `info`. Result is `pass`, `gap`, `fail`, `waived`, or `not_applicable`. The Evidence cell is `none` only for `gap` or `fail`.

## Do not

- Do not treat this skill, `trust-layer/README.md`, or `trust-layer/GAPS.md` as Flylo-Air policy.
- Do not merge, dismiss reviews, or change branch rules.
- Do not quote secret values if a diff contains them. That belongs to the secrets agent.
