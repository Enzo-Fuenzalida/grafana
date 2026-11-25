#!/usr/bin/env python3
"""Build the pull-request control-gap summary from evidence records.

The workflow validates records, then posts this summary. It does not grade
product code. A missing record is a gap. A record whose commit SHA is not the
pull request head does not cover its control.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from catalog import load_catalog
from validate import validate_file

REPO_ROOT = Path(__file__).resolve().parents[2]
RECORDS_DIR = REPO_ROOT / "trust-layer" / "evidence" / "records"
MARKER = "<!-- trust-layer-control-gap -->"
MAX_COMMENT = 60000

CODE_PATTERNS = (
    re.compile(r"^(apps|pkg|public|packages|kinds|scripts|conf|devenv|e2e-playwright)/"),
    re.compile(r"\.(go|ts|tsx|js|jsx|py|cue|proto)$"),
    re.compile(r"^(go\.(mod|sum)|go\.work|go\.work\.sum|package\.json|yarn\.lock)$"),
    re.compile(r"^\.github/workflows/.*\.(yml|yaml)$"),
    re.compile(r"^\.github/actions/"),
    re.compile(r"(^|/)Dockerfile"),
    re.compile(r"^trust-layer/(evidence|controls|branch-protection)/"),
)

RESULT_RANK = {"fail": 0, "gap": 1, "waived": 2, "pass": 3}


def code_touched(paths: list[str]) -> bool:
    return any(pattern.search(path) for path in paths for pattern in CODE_PATTERNS)


def build_summary(
    *,
    changed_files: list[str],
    records: list[tuple[str, dict]],
    head_sha: str,
    repository: str,
    pull_request: int,
    generated_at: str,
) -> tuple[str, bool]:
    """Return markdown and whether the pull request should get a comment."""
    catalog = load_catalog()
    touched = code_touched(changed_files)
    matching: dict[str, tuple[str, dict]] = {}
    stale: list[tuple[str, dict]] = []
    for path, record in records:
        if record.get("commit_sha") == head_sha:
            current = matching.get(record["control_id"])
            if current is None or RESULT_RANK[record["result"]] < RESULT_RANK[current[1]["result"]]:
                matching[record["control_id"]] = (path, record)
        else:
            stale.append((path, record))

    rows: list[tuple[str, str, str, str, str, str]] = []
    rows.append(
        (
            "TL-EVD-001",
            "info",
            "pass",
            "Evidence JSON in this job validated against trust-layer/evidence/schema.json.",
            "trust-layer/evidence/validate.py",
            "Keep records valid against the schema.",
        )
    )
    if stale:
        rows.append(
            (
                "TL-EVD-004",
                "high",
                "gap",
                f"{len(stale)} evidence record(s) are not bound to head {head_sha}.",
                stale[0][0],
                "Rewrite the record against the pull request head SHA.",
            )
        )
    elif matching:
        rows.append(
            (
                "TL-EVD-004",
                "info",
                "pass",
                f"All {len(matching)} covering record(s) use head {head_sha}.",
                next(iter(matching.values()))[0],
                "Keep commit_sha equal to the reviewed head.",
            )
        )
    else:
        rows.append(
            (
                "TL-EVD-004",
                "high",
                "gap",
                f"No evidence record is bound to head {head_sha}.",
                "none",
                "Write records whose commit_sha is the pull request head.",
            )
        )

    manual = [item for item in matching.values() if item[1]["check"]["method"] in {"manual", "hybrid"}]
    if not manual:
        rows.append(
            (
                "TL-EVD-003",
                "info",
                "not_applicable",
                "No manual or hybrid record is bound to this head.",
                "none",
                "Attest when a manual or hybrid check is recorded.",
            )
        )
    else:
        rows.append(
            (
                "TL-EVD-003",
                "info",
                "pass",
                f"{len(manual)} manual or hybrid record(s) include an attestation.",
                manual[0][0],
                "Keep reviewer, statement, and timestamp on manual checks.",
            )
        )

    waived = [item for item in matching.values() if item[1]["result"] == "waived"]
    if not waived:
        rows.append(
            (
                "TL-EVD-006",
                "info",
                "not_applicable",
                "No waiver is bound to this head.",
                "none",
                "A waiver needs approver, expiry, residual risk, and a policy id.",
            )
        )
    else:
        expired = []
        now = _parse_time(generated_at)
        for path, record in waived:
            expires = _parse_time(record["waiver"]["expires"])
            if expires <= now:
                expired.append(path)
        if expired:
            rows.append(
                (
                    "TL-EVD-006",
                    "high",
                    "gap",
                    f"{len(expired)} waiver(s) are expired at {generated_at}.",
                    expired[0],
                    "Renew the waiver under POL-SDLC-009 or close the gap.",
                )
            )
        else:
            rows.append(
                (
                    "TL-EVD-006",
                    "info",
                    "pass",
                    f"{len(waived)} waiver(s) are unexpired and carry approver and residual risk.",
                    waived[0][0],
                    "Drop the waiver when the control can pass.",
                )
            )

    missing = []
    for control in catalog["controls"]:
        control_id = control["id"]
        if control_id in {"TL-EVD-001", "TL-EVD-003", "TL-EVD-004", "TL-EVD-005", "TL-EVD-006"}:
            continue
        if control_id in matching:
            path, record = matching[control_id]
            severity = {"fail": "high", "gap": "medium", "waived": "info", "pass": "info"}[record["result"]]
            finding = record.get("finding") or record["check"]["summary"]
            rows.append(
                (
                    control_id,
                    severity,
                    record["result"],
                    finding,
                    path,
                    "See the owning agent for this control.",
                )
            )
        elif touched:
            missing.append(control)

    if touched and missing:
        rows.append(
            (
                "TL-EVD-002",
                "high",
                "gap",
                f"{len(missing)} catalog control(s) have no evidence record on {head_sha}.",
                "trust-layer/controls/catalog.yaml",
                "Run the owning agent and write a record, or record not_applicable in that agent's report.",
            )
        )
        for control in missing:
            rows.append(
                (
                    control["id"],
                    "info",
                    "gap",
                    f"No evidence record on {head_sha}. Owning agent {control['owning_agent']}.",
                    "none",
                    f"Produce the evidence required by {control['id']} under {control['policy_refs'][0]}.",
                )
            )
    elif not touched:
        rows.append(
            (
                "TL-EVD-002",
                "info",
                "not_applicable",
                "This pull request does not touch code paths that require a full control record set.",
                "none",
                "Run the owning agents when code, workflows, or trust-layer controls change.",
            )
        )
    else:
        rows.append(
            (
                "TL-EVD-002",
                "info",
                "pass",
                "Every other catalog control has a record on this head.",
                "trust-layer/evidence/records",
                "Re-check the set when the head SHA changes.",
            )
        )

    rows.append(
        (
            "TL-EVD-005",
            "low",
            "gap",
            "This summary covers evidence files only. Framework agents still need to file their own reports.",
            "none",
            "Run all eight framework agents and keep each report with the pull request.",
        )
    )

    verdict = "gap" if any(row[2] in {"gap", "fail"} for row in rows) else "pass"
    body = _render(
        repository=repository,
        pull_request=pull_request,
        head_sha=head_sha,
        generated_at=generated_at,
        verdict=verdict,
        rows=rows,
        touched=touched,
    )
    return body, touched


def _render(
    *,
    repository: str,
    pull_request: int,
    head_sha: str,
    generated_at: str,
    verdict: str,
    rows: list[tuple[str, str, str, str, str, str]],
    touched: bool,
) -> str:
    lines = [
        MARKER,
        "# PR control-gap report",
        "",
        "- Agent: evidence-auditor",
        "- Policy owner: Flylo-Air",
        "- Policy: POL-SDLC-009",
        "- Standards: STD-SDLC-001",
        f"- Repository: {repository}",
        f"- Pull request: {pull_request}",
        f"- Commit: {head_sha}",
        f"- Generated at: {generated_at}",
        "",
        "## Verdict",
        "",
        verdict,
        "",
        "## Findings",
        "",
        "| Control | Severity | Result | Finding | Evidence | Remediation |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_cell(part) for part in row) + " |")
    lines.extend(
        [
            "",
            "## Evidence records",
            "",
            "- trust-layer/evidence/records/",
            "",
            "## Scope",
            "",
            f"- Code or trust-layer inputs changed: {'yes' if touched else 'no'}",
            "- Policy text is not in this repository. Policy ids are external references.",
            "",
        ]
    )
    return "\n".join(lines)


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(value)
    return parsed.astimezone(timezone.utc)


def load_records(directory: Path) -> list[tuple[str, dict]]:
    if not directory.is_dir():
        return []
    loaded = []
    for path in sorted(directory.glob("*.json")):
        errors = validate_file(path)
        if errors:
            raise SystemExit(f"{path}: invalid evidence\n" + "\n".join(errors))
        loaded.append((path.as_posix(), json.loads(path.read_text(encoding="utf-8"))))
    return loaded


def post_comment(*, repository: str, pull_request: int, body: str, token: str) -> None:
    if len(body) > MAX_COMMENT:
        body = body[: MAX_COMMENT - 80] + "\n\n[truncated]\n"
    owner, repo = repository.split("/", 1)
    base = f"https://api.github.com/repos/{owner}/{repo}"
    existing = _request("GET", f"{base}/issues/{pull_request}/comments", token)
    match = next((comment for comment in existing if MARKER in comment.get("body", "")), None)
    if match:
        _request("PATCH", f"{base}/issues/comments/{match['id']}", token, {"body": body})
        return
    _request("POST", f"{base}/issues/{pull_request}/comments", token, {"body": body})


def _request(method: str, url: str, token: str, payload: dict | None = None) -> object:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "trust-layer-evidence",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else None


def _read_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a trust-layer control-gap summary.")
    parser.add_argument("--files-from", type=Path, required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--records-dir", type=Path, default=RECORDS_DIR)
    parser.add_argument("--generated-at", default="")
    parser.add_argument("--post", action="store_true")
    args = parser.parse_args(argv)

    generated_at = args.generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records = load_records(args.records_dir)
    summary, touched = build_summary(
        changed_files=_read_lines(args.files_from),
        records=records,
        head_sha=args.head_sha,
        repository=args.repository,
        pull_request=args.pull_request,
        generated_at=generated_at,
    )
    args.output.write_text(summary, encoding="utf-8")
    print(f"wrote {args.output}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            handle.write(f"code_touched={'true' if touched else 'false'}\n")
    if args.post:
        if not touched:
            print("skip comment: no code changes")
            return 0
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token:
            print("GITHUB_TOKEN is required to post", file=sys.stderr)
            return 2
        post_comment(
            repository=args.repository,
            pull_request=args.pull_request,
            body=summary,
            token=token,
        )
        print(f"posted summary to {args.repository}#{args.pull_request}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
