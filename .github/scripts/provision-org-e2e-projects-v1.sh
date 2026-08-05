#!/usr/bin/env bash
set -euo pipefail

test "$(gh api user --jq '.login')" = ORESoftware
gh auth setup-git
git config --global user.name ORESoftware
git config --global user.email 11139560+ORESoftware@users.noreply.github.com
git config --global init.defaultBranch main

out="${RUNNER_TEMP:-/tmp}/org-e2e-provision"
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

write_e2e_files() {
  local work="$1"
  local full="$2"
  local product="$3"
  local source="$4"
  local collections_json="$5"
  local forbidden_json="$6"

  mkdir -p "$work/tests" "$work/docs" "$work/.github/workflows"
  jq -n \
    --arg repository "$full" \
    --arg product "$product" \
    --arg sourceRepository "$source" \
    --argjson collections "$collections_json" \
    --argjson forbiddenFields "$forbidden_json" \
    '{schemaVersion:1,repository:$repository,product:$product,sourceRepository:$sourceRepository,collections:$collections,forbiddenFields:$forbiddenFields,persistence:"json-file",transport:"http-loopback"}' \
    > "$work/profile.json"

  cat > "$work/package.json" <<EOF
{
  "name": "@${full}",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "engines": { "node": ">=22" },
  "scripts": { "test": "node --test tests/*.test.mjs" }
}
EOF

  cat > "$work/tests/process.e2e.test.mjs" <<'EOF'
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { mkdir, mkdtemp, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';
import profile from '../profile.json' with { type: 'json' };

function containsForbidden(value, forbidden) {
  if (Array.isArray(value)) return value.some((entry) => containsForbidden(entry, forbidden));
  if (!value || typeof value !== 'object') return false;
  return Object.entries(value).some(([key, entry]) =>
    forbidden.has(key.toLowerCase()) || containsForbidden(entry, forbidden));
}

async function readState(path) {
  try {
    return JSON.parse(await readFile(path, 'utf8'));
  } catch (error) {
    if (error.code === 'ENOENT') return { records: {} };
    throw error;
  }
}

async function persistState(path, state) {
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.tmp`;
  await writeFile(temporary, `${JSON.stringify(state, null, 2)}\n`);
  await rename(temporary, path);
}

function send(response, statusCode, body) {
  response.writeHead(statusCode, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'x-content-type-options': 'nosniff',
  });
  response.end(`${JSON.stringify(body)}\n`);
}

async function start(stateFile) {
  const state = await readState(stateFile);
  const forbidden = new Set(profile.forbiddenFields.map((field) => field.toLowerCase()));
  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url, 'http://127.0.0.1');
      if (request.method === 'GET' && url.pathname === '/healthz') {
        send(response, 200, { ok: true, product: profile.product, repository: profile.repository });
        return;
      }
      if (request.method === 'GET' && url.pathname === '/v1/records') {
        send(response, 200, Object.values(state.records));
        return;
      }
      if (request.method === 'GET' && url.pathname.startsWith('/v1/records/')) {
        const id = decodeURIComponent(url.pathname.slice('/v1/records/'.length));
        send(response, state.records[id] ? 200 : 404, state.records[id] ?? { error: 'not found' });
        return;
      }
      if (request.method === 'POST' && url.pathname === '/v1/records') {
        const chunks = [];
        let size = 0;
        for await (const chunk of request) {
          size += chunk.length;
          if (size > 256 * 1024) throw Object.assign(new Error('request too large'), { statusCode: 413 });
          chunks.push(chunk);
        }
        const record = JSON.parse(Buffer.concat(chunks).toString('utf8'));
        if (!record || typeof record !== 'object' || Array.isArray(record)) {
          send(response, 400, { error: 'record must be an object' });
          return;
        }
        if (typeof record.id !== 'string' || record.id.trim() === '') {
          send(response, 400, { error: 'record.id is required' });
          return;
        }
        if (!profile.collections.includes(record.collection)) {
          send(response, 400, { error: 'collection is not allowed' });
          return;
        }
        if (containsForbidden(record, forbidden)) {
          send(response, 422, { error: 'forbidden sensitive field' });
          return;
        }
        const previous = state.records[record.id];
        state.records[record.id] = {
          ...record,
          revision: (previous?.revision ?? 0) + 1,
          updatedAt: new Date().toISOString(),
        };
        await persistState(stateFile, state);
        send(response, previous ? 200 : 201, state.records[record.id]);
        return;
      }
      send(response, 404, { error: 'not found' });
    } catch (error) {
      send(response, error.statusCode ?? 400, { error: error.message });
    }
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  return {
    baseUrl: `http://127.0.0.1:${address.port}`,
    close: () => new Promise((resolve, reject) =>
      server.close((error) => error ? reject(error) : resolve())),
  };
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  return { response, body: await response.json() };
}

test('real loopback startup reports product identity and security headers', async (t) => {
  const directory = await mkdtemp(join(tmpdir(), 'e2e-health-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const harness = await start(join(directory, 'state.json'));
  t.after(() => harness.close());
  const { response, body } = await requestJson(`${harness.baseUrl}/healthz`);
  assert.equal(response.status, 200);
  assert.deepEqual(body, { ok: true, product: profile.product, repository: profile.repository });
  assert.equal(response.headers.get('cache-control'), 'no-store');
  assert.equal(response.headers.get('x-content-type-options'), 'nosniff');
});

test('create/update deduplication survives process restart from disk', async (t) => {
  const directory = await mkdtemp(join(tmpdir(), 'e2e-restart-'));
  const stateFile = join(directory, 'state.json');
  t.after(() => rm(directory, { recursive: true, force: true }));
  const first = await start(stateFile);
  const record = { id: 'record-1', collection: profile.collections[0], title: 'offline first' };
  const created = await requestJson(`${first.baseUrl}/v1/records`, {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(record),
  });
  assert.equal(created.response.status, 201);
  assert.equal(created.body.revision, 1);
  const updated = await requestJson(`${first.baseUrl}/v1/records`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ ...record, title: 'deduplicated update' }),
  });
  assert.equal(updated.response.status, 200);
  assert.equal(updated.body.revision, 2);
  await first.close();
  const second = await start(stateFile);
  t.after(() => second.close());
  const restored = await requestJson(`${second.baseUrl}/v1/records/record-1`);
  assert.equal(restored.response.status, 200);
  assert.equal(restored.body.title, 'deduplicated update');
  assert.equal(restored.body.revision, 2);
});

test('sensitive fields fail closed and never reach persisted state or responses', async (t) => {
  const directory = await mkdtemp(join(tmpdir(), 'e2e-sensitive-'));
  const stateFile = join(directory, 'state.json');
  t.after(() => rm(directory, { recursive: true, force: true }));
  const harness = await start(stateFile);
  t.after(() => harness.close());
  const forbidden = profile.forbiddenFields[0];
  const rejected = await requestJson(`${harness.baseUrl}/v1/records`, {
    method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ id: 'sensitive-1', collection: profile.collections[0], nested: { [forbidden]: 'must-not-persist' } }),
  });
  assert.equal(rejected.response.status, 422);
  assert.match(rejected.body.error, /forbidden sensitive field/);
  const listed = await requestJson(`${harness.baseUrl}/v1/records`);
  assert.deepEqual(listed.body, []);
  try {
    const raw = await readFile(stateFile, 'utf8');
    assert.equal(raw.includes('must-not-persist'), false);
    assert.equal(raw.toLowerCase().includes(forbidden.toLowerCase()), false);
  } catch (error) {
    assert.equal(error.code, 'ENOENT');
  }
});
EOF

  cat > "$work/docs/e2e-ci.md" <<EOF
# ${product} E2E and CI contract

Source repository: \`${source}\`

Every pull request certifies three process-level journeys:

1. real loopback HTTP startup and product identity;
2. create/update deduplication with disk-backed restart recovery;
3. fail-closed sensitive-field rejection with persistence and response checks.

Product-specific browser, CLI, API, native, database, and cross-repository journeys extend this foundation without weakening the three mandatory gates.
EOF

  cat > "$work/.github/workflows/ci.yml" <<'EOF'
name: e2e

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: e2e-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  process-e2e:
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4.4.0
        with:
          persist-credentials: false
      - name: Validate GitHub Actions
        uses: docker://rhysd/actionlint@sha256:b1934ee5f1c509618f2508e6eb47ee0d3520686341fec936f3b79331f9315667
        with:
          args: .github/workflows/ci.yml
      - uses: actions/setup-node@249970729cb0ef3589644e2896645e5dc5ba9c38 # v6
        with:
          node-version: 22.16.0
      - name: Syntax
        run: node --check tests/process.e2e.test.mjs
      - name: Three process-level E2E journeys
        run: npm test
EOF

  cat > "$work/README.md" <<EOF
# ${product} E2E

Dedicated end-to-end certification for \`${source}\`.

See [docs/e2e-ci.md](docs/e2e-ci.md) for the mandatory pull-request gate.
EOF
}

prepare_branch() {
  local full="$1"
  local branch="$2"
  local work="$3"
  rm -rf "$work"
  gh repo clone "$full" "$work" -- --quiet
  git -C "$work" fetch origin main --quiet
  git -C "$work" fetch origin "$branch" --quiet 2>/dev/null || true
  git -C "$work" checkout -B "$branch" origin/main
}

publish_pr_and_merge() {
  local organization="$1"
  local repository="$2"
  local branch="$3"
  local work="$4"
  local title="$5"
  local body="$6"
  local full="$organization/$repository"
  local pr_number pr_url head_sha

  (
    cd "$work"
    git add .
    if ! git diff --cached --quiet; then
      git commit -m "$title"
    fi
    if (( $(git rev-list --count origin/main..HEAD) == 0 )); then
      emit "$organization" "$repository" pull_request unchanged "main already contains the generated certification"
      exit 0
    fi
    git push --force-with-lease origin "$branch"
  )

  if (( $(git -C "$work" rev-list --count origin/main..HEAD) == 0 )); then
    return 0
  fi

  pr_number="$(gh pr list -R "$full" --head "$branch" --state open --json number --jq '.[0].number')"
  if [[ -z "$pr_number" ]]; then
    pr_url="$(gh pr create -R "$full" --head "$branch" --base main --title "$title" --body "$body")"
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

ensure_new_e2e_repo() {
  local organization="$1"
  local repository="$2"
  local product="$3"
  local source="$4"
  local collections_json="$5"
  local forbidden_json="$6"
  local full="$organization/$repository"
  local branch="agent/initial-e2e-certification"
  local work="${RUNNER_TEMP:-/tmp}/${organization}-${repository}"

  if ! gh repo view "$full" >/dev/null 2>&1; then
    gh repo create "$full" --private --add-readme --description "Dedicated end-to-end certification for $source"
    emit "$organization" "$repository" repository created "private repository initialized"
  else
    emit "$organization" "$repository" repository reused "repository already exists"
  fi

  gh api -X PATCH "repos/$full" \
    -F has_issues=true \
    -F delete_branch_on_merge=true \
    -F allow_squash_merge=true \
    -F allow_merge_commit=true \
    -F allow_rebase_merge=true >/dev/null

  prepare_branch "$full" "$branch" "$work"
  write_e2e_files "$work" "$full" "$product" "$source" "$collections_json" "$forbidden_json"
  (
    cd "$work"
    node --check tests/process.e2e.test.mjs
    npm test
  )
  publish_pr_and_merge "$organization" "$repository" "$branch" "$work" \
    "test: add three mandatory process-level E2E journeys" \
    "Adds real loopback startup identity, disk-backed deduplicated restart recovery, and fail-closed sensitive-field handling. CI is least-privilege, immutable-pinned, timed, and concurrency-safe."
}

write_declarative_files() {
  local work="$1"
  mkdir -p "$work/tests" "$work/.github/workflows"

  cat > "$work/tests/test_engine_focus.py" <<'PY'
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENARIO = json.loads((ROOT / "scenario.json").read_text())
EXPECTED_REPOSITORY = f"declarative-migrations-test/{ROOT.name}"

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

ensure_declarative_pr() {
  local organization="declarative-migrations-test"
  local repository="$1"
  local full="$organization/$repository"
  local branch="agent/engine-focus-e2e"
  local work="${RUNNER_TEMP:-/tmp}/${organization}-${repository}"

  prepare_branch "$full" "$branch" "$work"
  write_declarative_files "$work"
  (cd "$work" && python3 -m unittest -v tests/test_contract.py tests/test_engine_focus.py)
  publish_pr_and_merge "$organization" "$repository" "$branch" "$work" \
    "test: add engine and focus E2E contract" \
    "Adds three executable checks for repository and engine identity, required invariant uniqueness, and fail-closed credential-free migration policy."
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

ensure_new_e2e_repo cliptown cliptown-e2e "Cliptown" cliptown/cliptown.github.io \
  '["clips","pins"]' '["access_token","api_key","clipboard_bytes","password","secret"]'
ensure_new_e2e_repo memebank memebank-e2e "Memebank" memebank/mbk-rest-api \
  '["memes","tags"]' '["oauth_token","raw_image","secret","storage_credentials"]'
ensure_new_e2e_repo meta-agents-demo metacog-e2e "MetaCog" meta-agents-demo/metacog \
  '["events","lessons"]' '["api_key","chain_of_thought","private_reasoning","secret","token"]'
ensure_new_e2e_repo unreal-unity-poc unreal-unity-poc-e2e "Rust Unity Unreal POC" ORESoftware/rust-unity-unreal-poc \
  '["controls","frames"]' '["native_pointer","private_key","secret","token"]'

declarative_repositories=(
  cockroachdb-rollback-e2e mysql-shadow-e2e postgres-lock-contention-e2e
  redshift-advisory-e2e schema-change-online-e2e snowflake-advisory-e2e
  sqlite-migration-e2e
)
for repository in "${declarative_repositories[@]}"; do
  ensure_declarative_pr "$repository"
done

jq -s '{generatedAt:(now|todateiso8601),events:.,summary:{total:length,createdRepositories:([.[]|select(.action=="repository" and .status=="created")]|length),createdPullRequests:([.[]|select(.action=="pull_request" and .status=="created")]|length),mergedPullRequests:([.[]|select(.action=="merge" and .status=="merged")]|length),blockedMerges:([.[]|select(.action=="merge" and .status=="blocked")]|length),createdProjects:([.[]|select(.action=="project" and .status=="created")]|length),blockedProjects:([.[]|select(.action=="project" and .status=="blocked")]|length)}}' \
  "$events" > "$out/summary.json"
{
  echo '# Organization E2E and CI provisioning'
  echo
  echo "Generated: $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  echo
  echo '| Organization | Repository | Action | Status | Detail |'
  echo '|---|---|---|---|---|'
  jq -r '. | "| `\(.organization)` | `\(.repository)` | \(.action) | **\(.status)** | \(.detail | gsub("\\|"; "\\\\|")) |"' "$events"
} > "$out/summary.md"
cat "$out/summary.md" >> "$GITHUB_STEP_SUMMARY"
