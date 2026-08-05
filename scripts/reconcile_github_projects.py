#!/usr/bin/env python3
"""Reconcile GitHub organization Projects v2 from the canonical portfolio registry."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

EXPECTED_PROJECTS = 41
EXPECTED_LOGIN = "ORESoftware"


@dataclass(frozen=True)
class RegistryEntry:
    portfolio_key: str
    github_org: str
    github_project_number: int
    github_project_title: str
    github_project_url: str
    linear_project_name: str
    linear_project_url: str


@dataclass(frozen=True)
class Decision:
    action: str
    number: int | None
    reason: str


class ReconcileError(RuntimeError):
    pass


def load_registry(path: Path) -> list[RegistryEntry]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if len(rows) != EXPECTED_PROJECTS:
        raise ReconcileError(
            f"registry must contain exactly {EXPECTED_PROJECTS} projects; found {len(rows)}"
        )

    entries: list[RegistryEntry] = []
    seen_keys: set[str] = set()
    seen_orgs: set[str] = set()
    for row in rows:
        key = row["portfolio_key"].strip()
        org = row["github_org"].strip()
        title = row["github_project_title"].strip()
        number = int(row["github_project_number"])
        expected_title = f"{org}-project"
        expected_url = f"https://github.com/orgs/{org}/projects/{number}"

        if not key or key != key.lower():
            raise ReconcileError(f"invalid portfolio key: {key!r}")
        if key in seen_keys:
            raise ReconcileError(f"duplicate portfolio key: {key}")
        if org in seen_orgs:
            raise ReconcileError(f"duplicate GitHub organization: {org}")
        if title != expected_title:
            raise ReconcileError(
                f"{org}: expected project title {expected_title!r}, found {title!r}"
            )
        if row["github_project_url"].strip() != expected_url:
            raise ReconcileError(
                f"{org}: expected project URL {expected_url!r}, "
                f"found {row['github_project_url']!r}"
            )
        if number != (4 if org == "dancing-dragons" else 1):
            raise ReconcileError(f"{org}: unexpected canonical project number {number}")
        if not row["linear_project_name"].strip() or not row["linear_project_url"].strip():
            raise ReconcileError(f"{org}: Linear project identity is incomplete")

        seen_keys.add(key)
        seen_orgs.add(org)
        entries.append(
            RegistryEntry(
                portfolio_key=key,
                github_org=org,
                github_project_number=number,
                github_project_title=title,
                github_project_url=expected_url,
                linear_project_name=row["linear_project_name"].strip(),
                linear_project_url=row["linear_project_url"].strip(),
            )
        )

    return entries


def decide(projects: Iterable[dict[str, Any]], entry: RegistryEntry) -> Decision:
    projects = list(projects)
    exact = [p for p in projects if p.get("title") == entry.github_project_title]
    if len(exact) > 1:
        raise ReconcileError(
            f"{entry.github_org}: duplicate projects named {entry.github_project_title!r}"
        )
    if exact:
        number = int(exact[0]["number"])
        if number != entry.github_project_number:
            raise ReconcileError(
                f"{entry.github_org}: exact title exists at project #{number}, "
                f"not canonical #{entry.github_project_number}"
            )
        return Decision("update", number, "canonical project already exists")

    canonical_number = [
        p for p in projects if int(p.get("number", -1)) == entry.github_project_number
    ]
    if len(canonical_number) > 1:
        raise ReconcileError(
            f"{entry.github_org}: duplicate project number {entry.github_project_number}"
        )
    if canonical_number:
        return Decision(
            "retitle",
            entry.github_project_number,
            f"canonical number has title {canonical_number[0].get('title')!r}",
        )

    return Decision("create", None, "canonical project is absent")


def run_gh(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["gh", *args],
        check=False,
        capture_output=True,
        text=True,
        env=os.environ,
    )
    if check and result.returncode != 0:
        raise ReconcileError(
            f"gh {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result


def gh_json(*args: str) -> dict[str, Any]:
    result = run_gh(*args)
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ReconcileError(
            f"gh {' '.join(args)} returned invalid JSON: {result.stdout[:300]!r}"
        ) from exc
    if not isinstance(value, dict):
        raise ReconcileError(f"gh {' '.join(args)} returned a non-object JSON value")
    return value


def verify_identity() -> None:
    if not os.environ.get("GH_TOKEN"):
        raise ReconcileError("GH_TOKEN is required")
    login = run_gh("api", "user", "--jq", ".login").stdout.strip()
    if login != EXPECTED_LOGIN:
        raise ReconcileError(
            f"expected authenticated GitHub login {EXPECTED_LOGIN!r}, found {login!r}"
        )


def verify_org_admin(org: str) -> None:
    membership = gh_json("api", f"user/memberships/orgs/{org}")
    if membership.get("state") != "active" or membership.get("role") != "admin":
        raise ReconcileError(
            f"{org}: active admin membership required, got "
            f"state={membership.get('state')!r} role={membership.get('role')!r}"
        )


def project_description(entry: RegistryEntry) -> str:
    return (
        f"Canonical delivery project for {entry.github_org}. "
        f"Linear: {entry.linear_project_name}. portfolio_key={entry.portfolio_key}"
    )


def project_readme(entry: RegistryEntry, registry_commit: str) -> str:
    return "\n".join(
        [
            "## Canonical cross-system links",
            "",
            f"- Portfolio key: `{entry.portfolio_key}`",
            f"- GitHub organization: https://github.com/{entry.github_org}",
            f"- Linear project: [{entry.linear_project_name}]({entry.linear_project_url})",
            (
                "- Registry source: "
                f"`ORESoftware/k8s-cluster@{registry_commit}` "
                "`ops/registries/portfolio-project-links.csv`"
            ),
            "",
            "Managed idempotently. Update the canonical registry instead of creating duplicates.",
        ]
    )


def reconcile_one(
    entry: RegistryEntry,
    *,
    apply: bool,
    registry_commit: str,
) -> dict[str, Any]:
    verify_org_admin(entry.github_org)
    listing = gh_json(
        "project",
        "list",
        "--owner",
        entry.github_org,
        "--limit",
        "100",
        "--format",
        "json",
    )
    projects = listing.get("projects")
    if not isinstance(projects, list):
        raise ReconcileError(f"{entry.github_org}: project list response lacks projects[]")

    decision = decide(projects, entry)
    actual_number = decision.number
    created_url: str | None = None

    if apply and decision.action == "create":
        created = gh_json(
            "project",
            "create",
            "--owner",
            entry.github_org,
            "--title",
            entry.github_project_title,
            "--format",
            "json",
        )
        actual_number = int(created["number"])
        created_url = str(created["url"])
        if actual_number != entry.github_project_number:
            raise ReconcileError(
                f"{entry.github_org}: created project #{actual_number}, "
                f"but registry requires #{entry.github_project_number}; "
                "update the registry deliberately before retrying"
            )

    if apply:
        if actual_number is None:
            raise ReconcileError(f"{entry.github_org}: no project number to update")
        run_gh(
            "project",
            "edit",
            str(actual_number),
            "--owner",
            entry.github_org,
            "--title",
            entry.github_project_title,
            "--description",
            project_description(entry),
            "--readme",
            project_readme(entry, registry_commit),
            "--format",
            "json",
        )
        viewed = gh_json(
            "project",
            "view",
            str(actual_number),
            "--owner",
            entry.github_org,
            "--format",
            "json",
        )
        actual_title = str(viewed.get("title", ""))
        actual_url = str(viewed.get("url", created_url or ""))
        if actual_title != entry.github_project_title:
            raise ReconcileError(
                f"{entry.github_org}: project title remained {actual_title!r} after update"
            )
        if actual_number != entry.github_project_number:
            raise ReconcileError(
                f"{entry.github_org}: project number drifted to {actual_number}"
            )
    else:
        actual_title = entry.github_project_title if actual_number is not None else ""
        actual_url = entry.github_project_url if actual_number is not None else ""

    return {
        **asdict(entry),
        "decision": asdict(decision),
        "apply": apply,
        "actual_number": actual_number,
        "actual_title": actual_title,
        "actual_url": actual_url,
        "status": "reconciled" if apply else "planned",
    }


def write_outputs(
    results: list[dict[str, Any]],
    failures: list[dict[str, str]],
    *,
    apply: bool,
    json_output: Path,
    markdown_output: Path,
    registry_commit: str,
) -> None:
    payload = {
        "schema_version": 1,
        "registry_commit": registry_commit,
        "mode": "apply" if apply else "plan",
        "summary": {
            "expected": EXPECTED_PROJECTS,
            "reconciled": len(results),
            "failed": len(failures),
            "created": sum(r["decision"]["action"] == "create" for r in results),
            "retitled": sum(r["decision"]["action"] == "retitle" for r in results),
            "updated": sum(r["decision"]["action"] == "update" for r in results),
        },
        "results": results,
        "failures": failures,
    }
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    lines = [
        "# GitHub organization Project reconciliation",
        "",
        f"- registry commit: `{registry_commit}`",
        f"- mode: `{'apply' if apply else 'plan'}`",
        f"- expected: `{EXPECTED_PROJECTS}`",
        f"- reconciled: `{len(results)}`",
        f"- failed: `{len(failures)}`",
        "",
        "| Organization | Project | Number | Action | Linear |",
        "|---|---|---:|---|---|",
    ]
    for result in results:
        lines.append(
            "| "
            f"`{result['github_org']}` | "
            f"`{result['github_project_title']}` | "
            f"{result['actual_number'] or result['github_project_number']} | "
            f"{result['decision']['action']} | "
            f"[{result['linear_project_name']}]({result['linear_project_url']}) |"
        )
    for failure in failures:
        lines.append(
            f"| `{failure['github_org']}` | failure | - | error | {failure['error']} |"
        )
    markdown_output.write_text("\n".join(lines) + "\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--registry-commit", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        entries = load_registry(args.registry)
        verify_identity()
    except ReconcileError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for entry in entries:
        print(f"Reconciling {entry.github_org} project #{entry.github_project_number}")
        try:
            results.append(
                reconcile_one(
                    entry,
                    apply=args.apply,
                    registry_commit=args.registry_commit,
                )
            )
        except ReconcileError as exc:
            failures.append({"github_org": entry.github_org, "error": str(exc)})
            print(str(exc), file=sys.stderr)

    write_outputs(
        results,
        failures,
        apply=args.apply,
        json_output=args.json_output,
        markdown_output=args.markdown_output,
        registry_commit=args.registry_commit,
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
