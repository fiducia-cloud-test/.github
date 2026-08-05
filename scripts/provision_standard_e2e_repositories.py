#!/usr/bin/env python3
"""Create and populate canonical product E2E repositories through reviewed PRs."""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXPECTED_LOGIN = "ORESoftware"
BRANCH = "agent/bootstrap-real-e2e"
SOURCE_SECRET = "E2E_SOURCE_DEPLOY_KEY"
EXPECTED_TARGETS = (
    "cliptown/cliptown-e2e",
    "memebank/memebank-e2e",
    "meta-agents-demo/metacog-e2e",
    "unreal-unity-poc/unreal-unity-poc-e2e",
)


class ProvisionError(RuntimeError):
    pass


@dataclass(frozen=True)
class RepoSpec:
    target: str
    description: str
    source: str
    source_sha: str
    source_private: bool
    profile: str
    readme: str
    tests_path: str
    tests_content: str
    workflow: str

    @property
    def org(self) -> str:
        return self.target.split("/", 1)[0]

    @property
    def repo(self) -> str:
        return self.target.split("/", 1)[1]


def run(
    *args: str,
    cwd: Path | None = None,
    check: bool = True,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        list(args),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        input=input_text,
        env=os.environ,
    )
    if check and result.returncode != 0:
        raise ProvisionError(
            f"{' '.join(args)} failed ({result.returncode})\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def gh_json(*args: str) -> Any:
    result = run("gh", *args)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ProvisionError(f"gh {' '.join(args)} returned invalid JSON") from exc


def load_specs(path: Path) -> tuple[RepoSpec, ...]:
    encoded = "".join(path.read_text(encoding="utf-8").split())
    try:
        payload = json.loads(gzip.decompress(base64.b64decode(encoded)))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise ProvisionError(f"invalid compressed spec file: {path}") from exc
    if payload.get("schema_version") != 1:
        raise ProvisionError("unsupported E2E spec schema")
    return tuple(RepoSpec(**item) for item in payload.get("specs", []))


def validate_specs(values: tuple[RepoSpec, ...]) -> None:
    targets = tuple(value.target for value in values)
    if targets != EXPECTED_TARGETS:
        raise ProvisionError(f"canonical target drift: {targets!r}")
    for spec in values:
        if len(spec.source_sha) != 40 or any(
            character not in "0123456789abcdef" for character in spec.source_sha
        ):
            raise ProvisionError(f"{spec.target}: source revision must be a lowercase SHA")
        required = (
            f"ref: {spec.source_sha}",
            "permissions:\n  contents: read",
            "persist-credentials: false",
            "pull_request:",
        )
        for marker in required:
            if marker not in spec.workflow:
                raise ProvisionError(f"{spec.target}: workflow missing {marker!r}")
        for mutable in (
            "@main",
            "@master",
            "@v1",
            "@v2",
            "@v3",
            "@v4",
            "@v5",
            "@v6",
            "@v7",
        ):
            if mutable in spec.workflow:
                raise ProvisionError(f"{spec.target}: mutable action reference {mutable}")
        secret_marker = f"secrets.{SOURCE_SECRET}"
        if spec.source_private != (secret_marker in spec.workflow):
            raise ProvisionError(f"{spec.target}: deploy-key boundary does not match privacy")
        journeys = spec.tests_content.count("def test_") + spec.tests_content.count("test(")
        if journeys < 3:
            raise ProvisionError(f"{spec.target}: fewer than three named journeys")


def verify_identity_and_admin(values: tuple[RepoSpec, ...]) -> None:
    if not os.environ.get("GH_TOKEN"):
        raise ProvisionError("GH_TOKEN is required")
    login = run("gh", "api", "user", "--jq", ".login").stdout.strip()
    if login != EXPECTED_LOGIN:
        raise ProvisionError(f"expected login {EXPECTED_LOGIN!r}, found {login!r}")
    orgs = {spec.org for spec in values}
    orgs.update(spec.source.split("/", 1)[0] for spec in values if spec.source_private)
    for org in sorted(orgs):
        membership = gh_json("api", f"user/memberships/orgs/{org}")
        if membership.get("state") != "active" or membership.get("role") != "admin":
            raise ProvisionError(f"{org}: active organization-admin membership required")


def repo_exists(full_name: str) -> bool:
    result = run("gh", "api", f"repos/{full_name}", check=False)
    if result.returncode == 0:
        return True
    if "404" in result.stderr or "Not Found" in result.stderr:
        return False
    raise ProvisionError(f"failed to query {full_name}: {result.stderr}")


def ensure_repo(spec: RepoSpec) -> bool:
    if repo_exists(spec.target):
        return False
    run(
        "gh",
        "api",
        "-X",
        "POST",
        f"orgs/{spec.org}/repos",
        "-f",
        f"name={spec.repo}",
        "-f",
        f"description={spec.description}",
        "-F",
        "private=true",
        "-F",
        "has_issues=true",
        "-F",
        "has_projects=false",
        "-F",
        "has_wiki=false",
        "-F",
        "auto_init=false",
    )
    return True


def configure_deploy_key(spec: RepoSpec, work: Path) -> int | None:
    if not spec.source_private:
        return None
    key_path = work / "source_read_key"
    run(
        "ssh-keygen",
        "-q",
        "-t",
        "ed25519",
        "-N",
        "",
        "-C",
        f"read-only:{spec.target}",
        "-f",
        str(key_path),
    )
    title = f"read-only:{spec.target}"
    for key in gh_json("api", f"repos/{spec.source}/keys"):
        if key.get("title") == title:
            run("gh", "api", "-X", "DELETE", f"repos/{spec.source}/keys/{key['id']}")
    public_key = key_path.with_suffix(".pub").read_text(encoding="utf-8").strip()
    created = gh_json(
        "api",
        "-X",
        "POST",
        f"repos/{spec.source}/keys",
        "-f",
        f"title={title}",
        "-f",
        f"key={public_key}",
        "-F",
        "read_only=true",
    )
    run(
        "gh",
        "secret",
        "set",
        SOURCE_SECRET,
        "--repo",
        spec.target,
        input_text=key_path.read_text(encoding="utf-8"),
    )
    return int(created["id"])


def write_file(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")


def git_config(repo: Path) -> None:
    run("git", "config", "user.name", "github-actions[bot]", cwd=repo)
    run(
        "git",
        "config",
        "user.email",
        "41898282+github-actions[bot]@users.noreply.github.com",
        cwd=repo,
    )


def agents_file() -> str:
    return """# AGENTS.md

- Pin source revisions and third-party Actions to immutable commits or digests.
- Preserve read-only workflow permissions and disabled persisted credentials.
- Never print deploy keys, tokens, or provider secrets.
- Fix product, harness, or source-pin defects; never skip failing assertions.
- Keep at least three repository-specific journeys mandatory on every PR.
- Resolve conflicts semantically using the merge base and relevant history.
"""


def initial_readme(spec: RepoSpec) -> str:
    return f"""# {spec.repo}

Canonical end-to-end certification repository for `{spec.source}`.

Changes land through pull requests. Private-source access uses a repository-scoped read-only deploy key.
"""


def ensure_main(spec: RepoSpec, root: Path) -> None:
    run("git", "init", "-b", "main", str(root))
    git_config(root)
    run("git", "remote", "add", "origin", f"https://github.com/{spec.target}.git", cwd=root)
    remote = run("git", "ls-remote", "--heads", "origin", "main", cwd=root)
    if remote.stdout.strip():
        run("git", "fetch", "origin", "main", cwd=root)
        run("git", "checkout", "-B", "main", "origin/main", cwd=root)
        return
    write_file(root, "README.md", initial_readme(spec))
    write_file(root, "AGENTS.md", agents_file())
    write_file(root, ".gitignore", "test-results/\nplaywright-report/\ntarget/\nnode_modules/\n")
    run("git", "add", ".", cwd=root)
    run("git", "commit", "-m", "chore: initialize canonical E2E repository", cwd=root)
    run("git", "push", "-u", "origin", "main", cwd=root)
    run("gh", "api", "-X", "PATCH", f"repos/{spec.target}", "-f", "default_branch=main")


def branch_files(spec: RepoSpec) -> dict[str, str]:
    lock = {
        "schema_version": 1,
        "profile": spec.profile,
        "source_repository": spec.source,
        "source_commit": spec.source_sha,
        "source_private": spec.source_private,
        "access": "read-only-deploy-key" if spec.source_private else "public-read",
    }
    return {
        "README.md": spec.readme,
        "AGENTS.md": agents_file(),
        "source-lock.json": json.dumps(lock, indent=2, sort_keys=True) + "\n",
        spec.tests_path: spec.tests_content,
        ".github/workflows/e2e.yml": spec.workflow,
    }


def create_or_update_pr(spec: RepoSpec, root: Path) -> tuple[int, str, str]:
    run("git", "checkout", "-B", BRANCH, "origin/main", cwd=root)
    for relative, content in branch_files(spec).items():
        write_file(root, relative, content)
    run("git", "add", ".", cwd=root)
    changed = run("git", "diff", "--cached", "--quiet", cwd=root, check=False).returncode != 0
    if changed:
        run("git", "commit", "-m", "test: add source-backed product E2E certification", cwd=root)
    run("git", "push", "--force-with-lease", "-u", "origin", BRANCH, cwd=root)
    head_sha = run("git", "rev-parse", "HEAD", cwd=root).stdout.strip()
    existing = gh_json(
        "pr",
        "list",
        "--repo",
        spec.target,
        "--head",
        BRANCH,
        "--state",
        "open",
        "--json",
        "number,url",
    )
    title = "Add source-backed product E2E certification"
    body = f"""## What changed

- pin `{spec.source}` at immutable commit `{spec.source_sha}`
- add three mandatory `{spec.profile}` journeys backed by the real source revision
- run on every PR with read-only permissions, immutable Actions, and disabled persisted credentials
- keep private-source access repository-scoped through a read-only deploy key

## Security boundary

No production credential is committed or printed. Source-pin updates require a new pull request.
"""
    if existing:
        number = int(existing[0]["number"])
        run("gh", "pr", "edit", str(number), "--repo", spec.target, "--title", title, "--body", body)
        url = str(existing[0]["url"])
    else:
        created = run(
            "gh",
            "pr",
            "create",
            "--repo",
            spec.target,
            "--head",
            BRANCH,
            "--base",
            "main",
            "--draft",
            "--title",
            title,
            "--body",
            body,
        )
        url = created.stdout.strip()
        number = int(url.rstrip("/").rsplit("/", 1)[-1])
    return number, url, head_sha


def provision(spec: RepoSpec, temp_root: Path, apply: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "target": spec.target,
        "source": spec.source,
        "source_sha": spec.source_sha,
        "profile": spec.profile,
        "created": False,
    }
    if not apply:
        result.update({"status": "planned", "branch": BRANCH})
        return result
    result["created"] = ensure_repo(spec)
    repo_root = temp_root / spec.repo
    ensure_main(spec, repo_root)
    result["deploy_key_id"] = configure_deploy_key(spec, repo_root)
    number, url, head_sha = create_or_update_pr(spec, repo_root)
    result.update(
        {
            "status": "pull-request-opened",
            "branch": BRANCH,
            "head_sha": head_sha,
            "pr_number": number,
            "pr_url": url,
            "repo_url": f"https://github.com/{spec.target}",
        }
    )
    return result


def write_evidence(
    results: list[dict[str, Any]],
    failures: list[dict[str, str]],
    *,
    apply: bool,
    json_output: Path,
    markdown_output: Path,
) -> None:
    summary = {
        "expected": 4,
        "processed": len(results),
        "created": sum(bool(item.get("created")) for item in results),
        "pull_requests": sum("pr_number" in item for item in results),
        "failed": len(failures),
    }
    payload = {
        "schema_version": 1,
        "mode": "apply" if apply else "plan",
        "summary": summary,
        "results": results,
        "failures": failures,
    }
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Standard E2E repository provisioning",
        "",
        f"- mode: `{'apply' if apply else 'plan'}`",
        f"- expected: `{summary['expected']}`",
        f"- processed: `{summary['processed']}`",
        f"- created: `{summary['created']}`",
        f"- pull requests: `{summary['pull_requests']}`",
        f"- failures: `{summary['failed']}`",
        "",
        "| Repository | Source pin | Created | Pull request |",
        "|---|---|---|---|",
    ]
    for item in results:
        lines.append(
            f"| `{item['target']}` | `{item['source']}@{item['source_sha']}` | "
            f"`{str(item.get('created', False)).lower()}` | {item.get('pr_url', 'planned')} |"
        )
    for failure in failures:
        lines.append(f"| `{failure['target']}` | failure | - | {failure['error']} |")
    markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--specs", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        values = load_specs(args.specs)
        validate_specs(values)
        if args.apply:
            verify_identity_and_admin(values)
            run("gh", "auth", "setup-git")
    except ProvisionError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="standard-e2e-provision-") as tmp:
        for spec in values:
            print(f"Provisioning {spec.target} from {spec.source}@{spec.source_sha}")
            try:
                results.append(provision(spec, Path(tmp), args.apply))
            except ProvisionError as exc:
                failures.append({"target": spec.target, "error": str(exc)})
                print(f"{spec.target}: {exc}", file=sys.stderr)
    write_evidence(
        results,
        failures,
        apply=args.apply,
        json_output=args.json_output,
        markdown_output=args.markdown_output,
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
