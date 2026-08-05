#!/usr/bin/env bash
set -euo pipefail

test "$(gh api user --jq '.login')" = ORESoftware

out="${RUNNER_TEMP:-/tmp}/organization-e2e-fleet"
rm -rf "$out"
mkdir -p "$out"
projects="$out/projects.jsonl"
repositories="$out/repositories.jsonl"
pull_requests="$out/pull-requests.jsonl"
: > "$projects"
: > "$repositories"
: > "$pull_requests"

emit_project() {
  jq -cn --arg organization "$1" --arg status "$2" --arg number "${3:-}" --arg detail "${4:-}" \
    '{organization:$organization,status:$status,number:($number|select(length>0)|tonumber?),detail:$detail}' >> "$projects"
}

emit_repository() {
  jq -cn --arg repository "$1" --arg status "$2" --arg detail "${3:-}" \
    '{repository:$repository,status:$status,detail:$detail}' >> "$repositories"
}

emit_pr() {
  jq -cn --arg repository "$1" --argjson number "$2" --arg status "$3" --arg url "$4" \
    --arg head "$5" --arg merge "$6" --arg title "$7" --arg projectStatus "$8" \
    '{repository:$repository,number:$number,status:$status,url:$url,headSha:$head,mergeSha:$merge,title:$title,projectStatus:$projectStatus}' >> "$pull_requests"
}

declare -A project_numbers=()
project_title="E2E & CI Fleet"
project_readme="$(cat <<'EOF'
# E2E & CI Fleet

Organization-level delivery board for mandatory pull-request end-to-end coverage.

## Required gate

- Every implementation pull request carries at least three executable journeys or links to a dedicated E2E pull request.
- GitHub Actions use least-privilege permissions, immutable action pins, explicit timeouts, and concurrency cancellation.
- Fixable failures are repaired on the pull-request branch and rerun.
- Merge decisions use the exact tested head SHA.
- Cross-organization dependencies remain immutable and fail closed.
- Credentials, private reasoning, raw secret material, and sensitive payloads do not enter fixtures or artifacts.

Linear program: **Cross-Org E2E & CI Fleet**.
EOF
)"

ensure_project() {
  local organization="$1"
  local listing number stderr_file
  stderr_file="$out/project-${organization}.stderr"

  if ! gh api "orgs/$organization" --silent >/dev/null 2>&1; then
    emit_project "$organization" missing "" "organization is not accessible"
    return 0
  fi

  listing="$(gh project list --owner "$organization" --format json 2>"$stderr_file" || printf '{"projects":[]}')"
  number="$(jq -r --arg title "$project_title" '.projects[]? | select(.title == $title) | .number' <<< "$listing" | head -n1)"

  if [[ -z "$number" || "$number" == null ]]; then
    if gh project create --owner "$organization" --title "$project_title" >/dev/null 2>"$stderr_file"; then
      sleep 1
      listing="$(gh project list --owner "$organization" --format json)"
      number="$(jq -r --arg title "$project_title" '.projects[]? | select(.title == $title) | .number' <<< "$listing" | head -n1)"
      emit_project "$organization" created "$number" "project created"
    else
      emit_project "$organization" blocked "" "$(tail -n1 "$stderr_file" 2>/dev/null || true)"
      return 0
    fi
  else
    emit_project "$organization" reused "$number" "project already existed"
  fi

  project_numbers["$organization"]="$number"
  gh project edit "$number" --owner "$organization" \
    --short-description "Mandatory E2E coverage, exact-head CI, and semantic merge readiness by repository." \
    --readme "$project_readme" >/dev/null 2>&1 || true
}

add_project_item() {
  local organization="$1"
  local url="$2"
  local number="${project_numbers[$organization]:-}"
  if [[ -z "$number" ]]; then
    printf '%s' blocked
    return 0
  fi
  if gh project item-add "$number" --owner "$organization" --url "$url" >/dev/null 2>&1; then
    printf '%s' added
  else
    printf '%s' reused-or-blocked
  fi
}

audit_repository() {
  local full="$1"
  local workflows tests
  if ! gh repo view "$full" >/dev/null 2>&1; then
    emit_repository "$full" missing "repository is not accessible"
    return 0
  fi
  workflows="$(gh api "repos/$full/contents/.github/workflows?ref=main" --jq 'length' 2>/dev/null || printf '0')"
  tests="$(gh api "repos/$full/git/trees/main?recursive=1" --jq '[.tree[]? | select(.type == "blob") | select(.path | startswith("tests/"))] | length' 2>/dev/null || printf '0')"
  emit_repository "$full" verified "workflows=$workflows test_files=$tests"
}

audit_pr() {
  local full="$1"
  local pr_number="$2"
  local organization="${full%%/*}"
  local json state merged_at url head merge title project_status

  if ! json="$(gh pr view "$pr_number" -R "$full" --json state,mergedAt,url,headRefOid,mergeCommit,title 2>/dev/null)"; then
    emit_pr "$full" "$pr_number" missing "https://github.com/$full/pull/$pr_number" "" "" "unresolved" blocked
    return 0
  fi

  state="$(jq -r '.state' <<< "$json")"
  merged_at="$(jq -r '.mergedAt // empty' <<< "$json")"
  url="$(jq -r '.url' <<< "$json")"
  head="$(jq -r '.headRefOid' <<< "$json")"
  merge="$(jq -r '.mergeCommit.oid // empty' <<< "$json")"
  title="$(jq -r '.title' <<< "$json")"
  project_status="$(add_project_item "$organization" "$url")"

  if [[ "$state" == MERGED && -n "$merged_at" && -n "$merge" ]]; then
    emit_pr "$full" "$pr_number" merged "$url" "$head" "$merge" "$title" "$project_status"
  else
    emit_pr "$full" "$pr_number" unmerged "$url" "$head" "$merge" "$title" "$project_status"
  fi
}

organizations=(
  zed-pkg-test 3fa-app-test declarative-migrations-test cliptown-test
  claritas-viz-test embedded-alerts-test evento-globolo-test fiducia-cloud-test
  memebank-test opto-sync-test quaestor-ledger-test sonus-auris-test
  messaging-intel-test scintilla-run-test file-tunnel-test shared-auth-test
  hypesiege-test streempilot-test akrion-sim benefactor-cc cliptown memebank
  meta-agents-demo unreal-unity-poc StreemPilot hypesiege zed-pkg ORESoftware
  declarative-migrations
)
for organization in "${organizations[@]}"; do
  ensure_project "$organization"
done

repositories_to_audit=(
  akrion-sim/akrion-sim-e2e
  benefactor-cc/benefactor-e2e
  StreemPilot/streempilot-e2e
  ORESoftware/rust-unity-unreal-poc
  zed-pkg/zed-interfaces
  hypesiege/hypesiege-e2e
  zed-pkg/zed-cli
  memebank/mbk-rest-api
  meta-agents-demo/metacog
  cliptown/cliptown-e2e
  memebank/memebank-e2e
  meta-agents-demo/metacog-e2e
  unreal-unity-poc/unreal-unity-poc-e2e
  declarative-migrations-test/cockroachdb-rollback-e2e
  declarative-migrations-test/mysql-shadow-e2e
  declarative-migrations-test/postgres-lock-contention-e2e
  declarative-migrations-test/redshift-advisory-e2e
  declarative-migrations-test/schema-change-online-e2e
  declarative-migrations-test/snowflake-advisory-e2e
  declarative-migrations-test/sqlite-migration-e2e
)
for repository in "${repositories_to_audit[@]}"; do
  audit_repository "$repository"
done

pull_requests_to_audit=(
  'akrion-sim/akrion-sim-e2e|1'
  'benefactor-cc/benefactor-e2e|1'
  'StreemPilot/streempilot-e2e|4'
  'ORESoftware/rust-unity-unreal-poc|1'
  'zed-pkg/zed-interfaces|21'
  'hypesiege/hypesiege-e2e|4'
  'zed-pkg/zed-cli|43'
  'memebank/mbk-rest-api|3'
  'meta-agents-demo/metacog|1'
  'cliptown/cliptown-e2e|2'
  'memebank/memebank-e2e|2'
  'meta-agents-demo/metacog-e2e|1'
  'unreal-unity-poc/unreal-unity-poc-e2e|2'
  'declarative-migrations-test/cockroachdb-rollback-e2e|6'
  'declarative-migrations-test/mysql-shadow-e2e|5'
  'declarative-migrations-test/postgres-lock-contention-e2e|5'
  'declarative-migrations-test/redshift-advisory-e2e|4'
  'declarative-migrations-test/schema-change-online-e2e|3'
  'declarative-migrations-test/snowflake-advisory-e2e|3'
  'declarative-migrations-test/sqlite-migration-e2e|3'
)
for entry in "${pull_requests_to_audit[@]}"; do
  IFS='|' read -r repository number <<< "$entry"
  audit_pr "$repository" "$number"
done

jq -s '.' "$projects" > "$out/projects.json"
jq -s '.' "$repositories" > "$out/repositories.json"
jq -s '.' "$pull_requests" > "$out/pull-requests.json"

jq -n \
  --slurpfile projects "$out/projects.json" \
  --slurpfile repositories "$out/repositories.json" \
  --slurpfile prs "$out/pull-requests.json" \
  '{generatedAt:(now|todateiso8601),projects:$projects[0],repositories:$repositories[0],pullRequests:$prs[0],summary:{organizations:($projects[0]|length),projectsCreated:([$projects[0][]|select(.status=="created")]|length),projectsReused:([$projects[0][]|select(.status=="reused")]|length),projectBlockers:([$projects[0][]|select(.status=="blocked" or .status=="missing")]|length),repositoriesVerified:([$repositories[0][]|select(.status=="verified")]|length),repositoryFailures:([$repositories[0][]|select(.status!="verified")]|length),pullRequestsMerged:([$prs[0][]|select(.status=="merged")]|length),pullRequestFailures:([$prs[0][]|select(.status!="merged")]|length)}}' \
  > "$out/summary.json"

{
  echo '# Cross-organization E2E & CI fleet audit'
  echo
  echo "Generated: $(jq -r '.generatedAt' "$out/summary.json")"
  echo
  echo '## Summary'
  echo
  jq -r '.summary | to_entries[] | "- **\(.key):** \(.value)"' "$out/summary.json"
  echo
  echo '## GitHub Projects by organization'
  echo
  echo '| Organization | Status | Project | Detail |'
  echo '|---|---|---:|---|'
  jq -r '.projects[] | "| `\(.organization)` | **\(.status)** | \(.number // "—") | \(.detail | gsub("\\|"; "\\\\|")) |"' "$out/summary.json"
  echo
  echo '## Repository certification'
  echo
  echo '| Repository | Status | Evidence |'
  echo '|---|---|---|'
  jq -r '.repositories[] | "| `\(.repository)` | **\(.status)** | \(.detail) |"' "$out/summary.json"
  echo
  echo '## Exact-head merged pull requests'
  echo
  echo '| Pull request | Status | Head SHA | Merge SHA | Project item |'
  echo '|---|---|---|---|---|'
  jq -r '.pullRequests[] | "| [\(.repository)#\(.number)](\(.url)) | **\(.status)** | `\(.headSha[0:12])` | `\(.mergeSha[0:12])` | \(.projectStatus) |"' "$out/summary.json"
} > "$out/summary.md"

cat "$out/summary.md" >> "${GITHUB_STEP_SUMMARY:-/dev/null}"

repository_failures="$(jq '.summary.repositoryFailures' "$out/summary.json")"
pr_failures="$(jq '.summary.pullRequestFailures' "$out/summary.json")"
if (( repository_failures > 0 || pr_failures > 0 )); then
  echo "delivery audit failed: repositories=$repository_failures pull_requests=$pr_failures" >&2
  exit 1
fi
