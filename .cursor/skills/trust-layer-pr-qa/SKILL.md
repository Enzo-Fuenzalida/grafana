---
name: trust-layer-pr-qa
description: QA a pull request against the Flylo-Air SDLC trust-layer catalog and write control-gap reports. Use when reviewing a PR, checking control gaps, or preparing merge or release evidence.
---

# Trust-layer pull request QA

Policy owner: Flylo-Air. Policy text is not in this repository. Controls live in `trust-layer/controls/catalog.yaml` and cite external ids such as POL-SDLC-001.

When the task is to review a pull request, run every framework agent whose controls can apply, then the evidence auditor:

- `trust-layer-review-control` owns TL-REV-* under POL-SDLC-002
- `trust-layer-test-assurance` owns TL-TST-* under POL-SDLC-003
- `trust-layer-release-gate` owns TL-REL-* under POL-SDLC-004
- `trust-layer-supply-chain` owns TL-SC-* under POL-SDLC-005
- `trust-layer-secrets-iac` owns TL-SEC-* under POL-SDLC-006
- `trust-layer-threat-model` owns TL-DES-* under POL-SDLC-008
- `trust-layer-branch-protection` owns TL-BR-* under POL-SDLC-007
- `trust-layer-evidence-auditor` owns TL-EVD-* under POL-SDLC-009 and POL-SDLC-001

Each agent emits its own PR control-gap report with control id, finding, severity, evidence link, and remediation. A control with no result is a gap. Do not treat Bugbot, a green lint job, or a ruleset file in git as a pass by itself.

Do not use `trust-layer/README.md` or `trust-layer/GAPS.md` as policy. Do not add policy or procedure markdown to the repo.
