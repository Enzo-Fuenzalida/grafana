# Engineering gaps

Snapshot against `controls/catalog.yaml` for this fork. Flylo-Air policy documents are external on purpose. Their absence from git is not a gap. Enforcement in this repository is.

Checked from the tree and from `GET /repos/fieldsphere/grafana/rules/branches/main` on 2026-11-25. The classic branch-protection endpoint returned 403, so this note does not describe that setting.

## What already runs

- `.github/workflows/fieldsphere-ci.yml` runs four shards of `CGO_ENABLED=0 go test -short` and frontend prettier, lint, and typecheck.
- `.github/workflows/govulncheck.yml` is path-filtered to Go, uses the `ubuntu-x64-large` runner, and on push runs only when the repository is `grafana/grafana`.
- `.github/renovate.json5` opens dependency updates and can automerge some npm patches.
- `.github/CODEOWNERS` covers upstream product paths. It does not cover `trust-layer/`.
- Release workflows under `.github/workflows/` still expect upstream runners and app tokens. SBOM, Trufflehog, CodeQL, and Trivy YAML sit in `.github/workflows-upstream-archive/` and are not active workflows.
- No Bugbot configuration is in the repo.

## What the catalog still does not get

- Live rules on `main` returned only organization lifecycle rules (`repository_create`, `repository_visibility`, `repository_delete`, `repository_transfer`). TL-BR-001 through TL-BR-007 are not enforced. The JSON in `branch-protection/rulesets/` is desired state only.
- The new evidence workflow fails invalid JSON and comments when records are missing. It does not fail the job for a missing record, and GitHub will not require the check until the ruleset is applied after the workflow is on the default branch.
- Short unit shards and frontend typecheck do not satisfy integration coverage (TL-TST-005) or QA evidence (TL-TST-006).
- There is no active secret scanner (TL-SEC-002), SBOM (TL-SC-004), or build provenance (TL-SC-005) on this fork.
- Most existing workflows pin actions by tag. TL-SC-006 is met by the new workflow's pinned actions and not by the rest of `.github/workflows/`.
- A human can merge after approval. TL-REL-004 is not enforced.
- The eight framework agents are definitions. Nothing in CI runs them. TL-EVD-005 stays a gap until their reports exist for the head SHA.
