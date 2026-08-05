#!/usr/bin/env python3
"""Validate the checked-in E2E fleet ledgers and publish a deterministic audit."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECTS_PATH = ROOT / ".github/data/e2e-projects.tsv"
PRS_PATH = ROOT / ".github/data/e2e-pull-requests.tsv"
OUTPUT = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "organization-e2e-fleet"
SHA = re.compile(r"^[0-9a-f]{40}$")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows:
        raise SystemExit(f"{path} is empty")
    return rows


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_projects(rows: list[dict[str, str]]) -> None:
    if len(rows) != 29:
        raise SystemExit(f"expected 29 owner rows, found {len(rows)}")
    owners = [row["owner"] for row in rows]
    if len(owners) != len(set(owners)):
        raise SystemExit("duplicate project owner")
    organizations = [row for row in rows if row["owner_type"] == "organization"]
    if len(organizations) != 28:
        raise SystemExit(f"expected 28 organization projects, found {len(organizations)}")
    for row in organizations:
        if row["project_number"] != "2" or row["status"] != "active":
            raise SystemExit(f"invalid project metadata for {row['owner']}")
        expected = f"https://github.com/orgs/{row['owner']}/projects/2"
        if row["url"] != expected:
            raise SystemExit(f"invalid project URL for {row['owner']}")
    user_rows = [row for row in rows if row["owner_type"] == "user"]
    if user_rows != [{
        "owner": "ORESoftware",
        "owner_type": "user",
        "project_number": "",
        "status": "not-applicable",
        "url": "",
    }]:
        raise SystemExit("the only non-organization row must be ORESoftware")


def validate_prs(rows: list[dict[str, str]]) -> None:
    if len(rows) != 20:
        raise SystemExit(f"expected 20 canonical PRs, found {len(rows)}")
    identities = [(row["repository"], row["pr"]) for row in rows]
    if len(identities) != len(set(identities)):
        raise SystemExit("duplicate pull-request identity")
    for row in rows:
        if row["status"] != "merged":
            raise SystemExit(f"unmerged target: {row['repository']}#{row['pr']}")
        if not SHA.fullmatch(row["head_sha"]) or not SHA.fullmatch(row["merge_sha"]):
            raise SystemExit(f"invalid SHA for {row['repository']}#{row['pr']}")
        expected = f"https://github.com/{row['repository']}/pull/{row['pr']}"
        if row["url"] != expected:
            raise SystemExit(f"invalid PR URL for {row['repository']}#{row['pr']}")


def markdown(projects: list[dict[str, str]], prs: list[dict[str, str]], summary: dict) -> str:
    lines = [
        "# Cross-organization E2E & CI fleet audit",
        "",
        "**Date:** August 5, 2026  ",
        "**Linear project:** [Cross-Org E2E & CI Fleet](https://linear.app/denman/project/cross-org-e2e-and-ci-fleet-71970126dfc6)  ",
        "**Execution issue:** [DEN-2435](https://linear.app/denman/issue/DEN-2435/provision-missing-e2e-repositories-organization-projects-and-exact)",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- **{key}:** {value}")
    lines.extend([
        "",
        "## GitHub projects by organization",
        "",
        "| Owner | Type | Project | Status |",
        "|---|---|---|---|",
    ])
    for row in projects:
        project = f"[E2E & CI Fleet #2]({row['url']})" if row["url"] else "—"
        lines.append(f"| `{row['owner']}` | {row['owner_type']} | {project} | {row['status']} |")
    lines.extend([
        "",
        "## Exact-head merged pull requests",
        "",
        "| Pull request | Category | Tested head | Merge SHA |",
        "|---|---|---|---|",
    ])
    for row in prs:
        lines.append(
            f"| [{row['repository']}#{row['pr']}]({row['url']}) | {row['category']} | "
            f"`{row['head_sha'][:12]}` | `{row['merge_sha'][:12]}` |"
        )
    lines.extend([
        "",
        "## Evidence",
        "",
        "- Project ledger source: `organization-e2e-provisioning` artifact from run "
        "[31042139871](https://github.com/fiducia-cloud-test/.github/actions/runs/31042139871).",
        "- Retained artifact ID: `8945157777`.",
        "- Artifact digest: `sha256:e7b190555fa01adedfea8ff69cd636573008f4cfd568c4ca226ed9dd594bec81`.",
        "- The audit is rendered from checked-in TSV ledgers and performs no GitHub API calls.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    projects = read_tsv(PROJECTS_PATH)
    prs = read_tsv(PRS_PATH)
    validate_projects(projects)
    validate_prs(prs)
    categories = Counter(row["category"] for row in prs)
    summary = {
        "organization projects": 28,
        "non-organization owners": 1,
        "canonical merged pull requests": 20,
        "new dedicated E2E repositories": categories["new-e2e-repository"],
        "database-engine repositories": categories["database-engine-e2e"],
        "unmerged target pull requests": 0,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PROJECTS_PATH, OUTPUT / PROJECTS_PATH.name)
    shutil.copy2(PRS_PATH, OUTPUT / PRS_PATH.name)
    report = markdown(projects, prs, summary)
    (OUTPUT / "summary.md").write_text(report, encoding="utf-8")
    payload = {
        "schemaVersion": 1,
        "generatedAt": "2026-08-05T20:20:00Z",
        "summary": summary,
        "ledgerDigests": {
            PROJECTS_PATH.name: f"sha256:{digest(PROJECTS_PATH)}",
            PRS_PATH.name: f"sha256:{digest(PRS_PATH)}",
        },
        "projects": projects,
        "pullRequests": prs,
    }
    (OUTPUT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as handle:
            handle.write(report)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
