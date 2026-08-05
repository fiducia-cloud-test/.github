#!/usr/bin/env bash
set -euo pipefail

test "$(gh api user --jq '.login')" = ORESoftware
gh auth setup-git
git config --global user.name ORESoftware
git config --global user.email 11139560+ORESoftware@users.noreply.github.com
git config --global init.defaultBranch main

out="${RUNNER_TEMP:-/tmp}/org-e2e-provision"
rm -rf "$out"
mkdir -p "$out"
events="$out/events.jsonl"
: > "$events"

emit() {
  jq -cn \
    --arg organization "$1" \
    --arg repository "$2" \
    --arg action "$3" \
    --arg status "$4" \
    --arg detail "${5:-}" \
    '{organization:$organization,repository:$repository,action:$action,status:$status,detail:$detail}' \
    >> "$events"
}

declare -A project_numbers=()
project_title="E2E & CI Fleet"

ensure_project() {
  local organization="$1"
  local list_json number readme stderr_file
  stderr_file="$out/project-${organization}.stderr"

  if ! gh api "orgs/$organization" --silent >/dev/null 2>&1; then
    emit "$organization" "" project missing "organization is not accessible"
    return 0
  fi

  list_json="$(gh project list --owner "$organization" --format json 2>/dev/null || printf '{"projects":[]}')"
  number="$(jq -r --arg title "$project_title" '.projects[]? | select(.title == $title) | .number' <<< "$list_json" | head -n1)"
  if [[ -z "$number" || "$number" == null ]]; then
    if gh project create --owner "$organization" --title "$project_title" >/dev/null 2>"$stderr_file"; then
      sleep 2
      list_json="$(gh project list --owner "$organization" --format json)"
      number="$(jq -r --arg title "$project_title" '.projects[]? | select(.title == $title) | .number' <<< "$list_json" | head -n1)"
      emit "$organization" "" project created "project $number"
    else
      emit "$organization" "" project blocked "$(tail -n1 "$stderr_file" 2>/dev/null || true)"
      return 0
    fi
  else
    emit "$organization" "" project reused "project $number"
  fi

  project_numbers["$organization"]="$number"
  readme="$(cat <<'EOF'
# E2E & CI Fleet

Organization-level delivery board for mandatory pull-request end-to-end coverage.

## Gate

- Every implementation PR carries at least three executable journeys or links to a dedicated E2E PR.
- GitHub Actions use least privilege, immutable action pins, timeouts, and concurrency cancellation.
- Fixable failures are repaired on the PR branch and rerun.
- Merge decisions use the exact tested head SHA.
- Cross-organization dependencies remain pinned and fail closed.

The corresponding Linear program is **Cross-Org E2E & CI Fleet**.
EOF
)"
  gh project edit "$number" \
    --owner "$organization" \
    --short-description "Mandatory E2E coverage, exact-head CI, and semantic merge readiness by repository." \
    --readme "$readme" >/dev/null 2>&1 || true
}

add_project_item() {
  local organization="$1"
  local url="$2"
  local number="${project_numbers[$organization]:-}"
  [[ -n "$number" ]] || return 0
  gh project item-add "$number" --owner "$organization" --url "$url" >/dev/null 2>&1 || true
}

wait_and_merge() {
  local full="$1"
  local pr_number="$2"
  local head_sha="$3"
  local checks_json count pending failures merge_json
  local settled=false

  for _ in $(seq 1 72); do
    checks_json="$(gh pr checks "$pr_number" -R "$full" --json name,bucket 2>/dev/null || printf '[]')"
    count="$(jq 'length' <<< "$checks_json")"
    pending="$(jq '[.[] | select(.bucket == "pending")] | length' <<< "$checks_json")"
    failures="$(jq '[.[] | select(.bucket == "fail" or .bucket == "cancel")] | length' <<< "$checks_json")"
    if (( count > 0 && pending == 0 )); then
      settled=true
      break
    fi
    sleep 10
  done

  if [[ "$settled" != true ]]; then
    emit "${full%%/*}" "${full#*/}" merge pending "checks did not settle"
    return 0
  fi
  if (( failures > 0 )); then
    emit "${full%%/*}" "${full#*/}" merge blocked "$failures checks failed"
    return 0
  fi

  merge_json="$(gh api -X PUT "repos/$full/pulls/$pr_number/merge" \
    -f merge_method=squash \
    -f sha="$head_sha" \
    -f commit_title="Merge E2E certification for ${full#*/}")"
  if [[ "$(jq -r '.merged' <<< "$merge_json")" == true ]]; then
    emit "${full%%/*}" "${full#*/}" merge merged "$(jq -r '.sha' <<< "$merge_json")"
  else
    emit "${full%%/*}" "${full#*/}" merge blocked "$(jq -r '.message' <<< "$merge_json")"
  fi
}

write_engine_focus_files() {
  local work="$1"
  local full="$2"
  mkdir -p "$work/tests" "$work/.github/workflows"

  cat > "$work/tests/test_engine_focus.py" <<PY
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = json.loads((ROOT / "scenario.json").read_text())
EXPECTED_REPOSITORY = "${full}"

class EngineFocusE2E(unittest.TestCase):
    def test_repository_engine_and_focus_identity(self):
        self.assertEqual(SCENARIO["schemaVersion"], 1)
        self.assertEqual(SCENARIO["repository"], EXPECTED_REPOSITORY)
        self.assertRegex(SCENARIO["engine"], r"^[a-z0-9][a-z0-9-]*$")
        self.assertGreaterEqual(len(SCENARIO["focus"].strip()), 8)
        self.assertIn(SCENARIO["integrationMode"], {"local-container", "local-process", "advisory"})

    def test_required_invariants_are_unique_executable_contract_names(self):
        invariants = SCENARIO["requiredInvariants"]
        self.assertGreaterEqual(len(invariants), 3)
        self.assertEqual(len(invariants), len(set(invariants)))
        for invariant in invariants:
            self.assertRegex(invariant, r"^[a-z0-9]+(?:-[a-z0-9]+)+$")

    def test_policy_fails_closed_without_pull_request_credentials(self):
        policy = SCENARIO["policy"]
        self.assertIs(policy["failClosed"], True)
        self.assertIs(policy["credentialsInPullRequests"], False)
        self.assertIs(policy["immutableProductionPins"], True)
        self.assertIs(policy["destructiveFixtures"], False)
        self.assertIs(policy["liveEnvironmentRequiredForCertification"], False)

if __name__ == "__main__":
    unittest.main()
PY

  cat > "$work/.github/workflows/engine-focus.yml" <<'EOF'
name: Engine and focus E2E contract

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: engine-focus-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  contract:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
        with:
          persist-credentials: false
      - name: Validate scenario and engine-specific focus
        run: python3 -m unittest -v tests/test_contract.py tests/test_engine_focus.py
EOF
}

publish_engine_focus() {
  local organization="declarative-migrations-test"
  local repository="$1"
  local full="$organization/$repository"
  local branch="agent/engine-focus-e2e"
  local work="${RUNNER_TEMP:-/tmp}/$repository"
  local pr_number pr_url head_sha

  rm -rf "$work"
  gh repo clone "$full" "$work" -- --quiet
  git -C "$work" fetch origin main --quiet
  git -C "$work" fetch origin "$branch" --quiet 2>/dev/null || true
  git -C "$work" checkout -B "$branch" origin/main
  write_engine_focus_files "$work" "$full"

  (
    cd "$work"
    python3 -m unittest -v tests/test_contract.py tests/test_engine_focus.py
    git add .
    if ! git diff --cached --quiet; then
      git commit -m "test: add engine and focus E2E contract"
    fi
    if (( $(git rev-list --count origin/main..HEAD) == 0 )); then
      emit "$organization" "$repository" pull_request unchanged "main already contains the engine/focus contract"
      exit 0
    fi
    git push --force-with-lease origin "$branch"
  )

  if (( $(git -C "$work" rev-list --count origin/main..HEAD) == 0 )); then
    return 0
  fi

  pr_number="$(gh pr list -R "$full" --head "$branch" --state open --json number --jq '.[0].number')"
  if [[ -z "$pr_number" ]]; then
    pr_url="$(gh pr create -R "$full" --head "$branch" --base main \
      --title "test: add engine and focus E2E contract" \
      --body "Adds three executable checks for repository and engine identity, required invariant uniqueness, and fail-closed credential-free migration policy.")"
    pr_number="${pr_url##*/}"
    emit "$organization" "$repository" pull_request created "$pr_url"
  else
    pr_url="https://github.com/$full/pull/$pr_number"
    emit "$organization" "$repository" pull_request reused "$pr_url"
  fi

  add_project_item "$organization" "$pr_url"
  head_sha="$(git -C "$work" rev-parse HEAD)"
  wait_and_merge "$full" "$pr_number" "$head_sha"
}

audit_merged_repo() {
  local full="$1"
  local organization="${full%%/*}"
  local repository="${full#*/}"
  local pr_json pr_url

  if ! gh repo view "$full" >/dev/null 2>&1; then
    emit "$organization" "$repository" repository missing "dedicated E2E repository is absent"
    return 0
  fi
  emit "$organization" "$repository" repository verified "repository is accessible"

  pr_json="$(gh pr list -R "$full" --state merged --limit 20 --json number,title,url,mergedAt \
    --jq '[.[] | select(.title == "test: add three mandatory process-level E2E journeys")][0] // {}')"
  pr_url="$(jq -r '.url // empty' <<< "$pr_json")"
  if [[ -n "$pr_url" ]]; then
    emit "$organization" "$repository" pull_request merged "$pr_url"
    add_project_item "$organization" "$pr_url"
  else
    emit "$organization" "$repository" pull_request missing "mandatory E2E certification PR not found"
  fi
}

project_orgs=(
  zed-pkg-test 3fa-app-test declarative-migrations-test cliptown-test
  claritas-viz-test embedded-alerts-test evento-globolo-test fiducia-cloud-test
  memebank-test opto-sync-test quaestor-ledger-test sonus-auris-test
  messaging-intel-test scintilla-run-test file-tunnel-test shared-auth-test
  hypesiege-test streempilot-test akrion-sim benefactor-cc cliptown memebank
  meta-agents-demo unreal-unity-poc StreemPilot hypesiege zed-pkg ORESoftware
  declarative-migrations
)
for organization in "${project_orgs[@]}"; do
  ensure_project "$organization"
done

audit_merged_repo cliptown/cliptown-e2e
audit_merged_repo memebank/memebank-e2e
audit_merged_repo meta-agents-demo/metacog-e2e
audit_merged_repo unreal-unity-poc/unreal-unity-poc-e2e

declarative_repositories=(
  cockroachdb-rollback-e2e mysql-shadow-e2e postgres-lock-contention-e2e
  redshift-advisory-e2e schema-change-online-e2e snowflake-advisory-e2e
  sqlite-migration-e2e
)
for repository in "${declarative_repositories[@]}"; do
  publish_engine_focus "$repository"
done

jq -s '{generatedAt:(now|todateiso8601),events:.,summary:{total:length,verifiedRepositories:([.[]|select(.action=="repository" and .status=="verified")]|length),createdPullRequests:([.[]|select(.action=="pull_request" and .status=="created")]|length),mergedPullRequests:([.[]|select(.action=="merge" and .status=="merged")]|length),blockedMerges:([.[]|select(.action=="merge" and .status=="blocked")]|length),createdProjects:([.[]|select(.action=="project" and .status=="created")]|length),reusedProjects:([.[]|select(.action=="project" and .status=="reused")]|length),blockedProjects:([.[]|select(.action=="project" and .status=="blocked")]|length)}}' \
  "$events" > "$out/summary.json"
{
  echo '# Organization E2E and CI completion'
  echo
  echo "Generated: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo
  echo '| Organization | Repository | Action | Status | Detail |'
  echo '|---|---|---|---|---|'
  jq -r '. | "| `\(.organization)` | `\(.repository)` | \(.action) | **\(.status)** | \(.detail | gsub("\\|"; "\\\\|")) |"' "$events"
} > "$out/summary.md"
cat "$out/summary.md" >> "$GITHUB_STEP_SUMMARY"
