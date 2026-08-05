# Cross-organization E2E & CI fleet

**Date:** August 5, 2026  
**Linear project:** [Cross-Org E2E & CI Fleet](https://linear.app/denman/project/cross-org-e2e-and-ci-fleet-71970126dfc6)  
**Execution issue:** [DEN-2435](https://linear.app/denman/issue/DEN-2435/provision-missing-e2e-repositories-organization-projects-and-exact)

## Outcome

- 28 GitHub organizations have an **E2E & CI Fleet** project at project #2.
- 20 canonical delivery pull requests are merged.
- Four previously missing dedicated E2E repositories were created, populated, tested, and merged.
- Seven Declarative Migrations engine repositories have engine/focus contracts with canonical mode semantics.
- The targeted PR set has zero unmerged pull requests.
- `ORESoftware` is a user account rather than an organization, so organization-project provisioning is not applicable to it.

## Required pull-request gate

1. At least three executable journeys per implementation PR, or an explicit linked dedicated E2E PR.
2. Read-only default GitHub Actions permissions and no persisted checkout credentials.
3. Immutable third-party action pins, explicit timeouts, and concurrency cancellation.
4. Fixable failures repaired on the PR branch and rerun.
5. Merge performed against the exact tested head SHA.
6. No credentials, raw secret material, private reasoning, or sensitive payloads in fixtures or artifacts.

## GitHub projects by organization

| Organization | Project | Status |
|---|---|---|
| `zed-pkg-test` | [E2E & CI Fleet #2](https://github.com/orgs/zed-pkg-test/projects/2) | active |
| `3fa-app-test` | [E2E & CI Fleet #2](https://github.com/orgs/3fa-app-test/projects/2) | active |
| `declarative-migrations-test` | [E2E & CI Fleet #2](https://github.com/orgs/declarative-migrations-test/projects/2) | active |
| `cliptown-test` | [E2E & CI Fleet #2](https://github.com/orgs/cliptown-test/projects/2) | active |
| `claritas-viz-test` | [E2E & CI Fleet #2](https://github.com/orgs/claritas-viz-test/projects/2) | active |
| `embedded-alerts-test` | [E2E & CI Fleet #2](https://github.com/orgs/embedded-alerts-test/projects/2) | active |
| `evento-globolo-test` | [E2E & CI Fleet #2](https://github.com/orgs/evento-globolo-test/projects/2) | active |
| `fiducia-cloud-test` | [E2E & CI Fleet #2](https://github.com/orgs/fiducia-cloud-test/projects/2) | active |
| `memebank-test` | [E2E & CI Fleet #2](https://github.com/orgs/memebank-test/projects/2) | active |
| `opto-sync-test` | [E2E & CI Fleet #2](https://github.com/orgs/opto-sync-test/projects/2) | active |
| `quaestor-ledger-test` | [E2E & CI Fleet #2](https://github.com/orgs/quaestor-ledger-test/projects/2) | active |
| `sonus-auris-test` | [E2E & CI Fleet #2](https://github.com/orgs/sonus-auris-test/projects/2) | active |
| `messaging-intel-test` | [E2E & CI Fleet #2](https://github.com/orgs/messaging-intel-test/projects/2) | active |
| `scintilla-run-test` | [E2E & CI Fleet #2](https://github.com/orgs/scintilla-run-test/projects/2) | active |
| `file-tunnel-test` | [E2E & CI Fleet #2](https://github.com/orgs/file-tunnel-test/projects/2) | active |
| `shared-auth-test` | [E2E & CI Fleet #2](https://github.com/orgs/shared-auth-test/projects/2) | active |
| `hypesiege-test` | [E2E & CI Fleet #2](https://github.com/orgs/hypesiege-test/projects/2) | active |
| `streempilot-test` | [E2E & CI Fleet #2](https://github.com/orgs/streempilot-test/projects/2) | active |
| `akrion-sim` | [E2E & CI Fleet #2](https://github.com/orgs/akrion-sim/projects/2) | active |
| `benefactor-cc` | [E2E & CI Fleet #2](https://github.com/orgs/benefactor-cc/projects/2) | active |
| `cliptown` | [E2E & CI Fleet #2](https://github.com/orgs/cliptown/projects/2) | active |
| `memebank` | [E2E & CI Fleet #2](https://github.com/orgs/memebank/projects/2) | active |
| `meta-agents-demo` | [E2E & CI Fleet #2](https://github.com/orgs/meta-agents-demo/projects/2) | active |
| `unreal-unity-poc` | [E2E & CI Fleet #2](https://github.com/orgs/unreal-unity-poc/projects/2) | active |
| `StreemPilot` | [E2E & CI Fleet #2](https://github.com/orgs/StreemPilot/projects/2) | active |
| `hypesiege` | [E2E & CI Fleet #2](https://github.com/orgs/hypesiege/projects/2) | active |
| `zed-pkg` | [E2E & CI Fleet #2](https://github.com/orgs/zed-pkg/projects/2) | active |
| `declarative-migrations` | [E2E & CI Fleet #2](https://github.com/orgs/declarative-migrations/projects/2) | active |
| `ORESoftware` | — | not applicable: user account |

## Exact-head merged pull requests

| Repository PR | Category | Tested head | Merge SHA |
|---|---|---|---|
| [akrion-sim/akrion-sim-e2e#1](https://github.com/akrion-sim/akrion-sim-e2e/pull/1) | product E2E | `1be0583010b1` | `fb6eb0f4c42b` |
| [benefactor-cc/benefactor-e2e#1](https://github.com/benefactor-cc/benefactor-e2e/pull/1) | product E2E | `d3fb709b16db` | `aa57912ba1b0` |
| [StreemPilot/streempilot-e2e#4](https://github.com/StreemPilot/streempilot-e2e/pull/4) | product E2E | `a65188130fcc` | `b37c3836089b` |
| [ORESoftware/rust-unity-unreal-poc#1](https://github.com/ORESoftware/rust-unity-unreal-poc/pull/1) | native E2E | `7986c35e4860` | `ac701fce84f6` |
| [zed-pkg/zed-interfaces#21](https://github.com/zed-pkg/zed-interfaces/pull/21) | package integrity | `40146d69632c` | `cc5ed7339672` |
| [hypesiege/hypesiege-e2e#4](https://github.com/hypesiege/hypesiege-e2e/pull/4) | product E2E | `07609a441095` | `5a77aa45e32b` |
| [zed-pkg/zed-cli#43](https://github.com/zed-pkg/zed-cli/pull/43) | package integrity | `9c8cf3014693` | `a850dbcc799a` |
| [memebank/mbk-rest-api#3](https://github.com/memebank/mbk-rest-api/pull/3) | API E2E | `6256af082f51` | `d082ed0f3ef3` |
| [meta-agents-demo/metacog#1](https://github.com/meta-agents-demo/metacog/pull/1) | process E2E | `88cb8e481591` | `c472f00a257d` |
| [cliptown/cliptown-e2e#2](https://github.com/cliptown/cliptown-e2e/pull/2) | new E2E repository | `d4796165c3c5` | `7819d9172cab` |
| [memebank/memebank-e2e#2](https://github.com/memebank/memebank-e2e/pull/2) | new E2E repository | `068801d942aa` | `7dbb8fe9234b` |
| [meta-agents-demo/metacog-e2e#1](https://github.com/meta-agents-demo/metacog-e2e/pull/1) | new E2E repository | `1673395a6698` | `9fdd95ec392c` |
| [unreal-unity-poc/unreal-unity-poc-e2e#2](https://github.com/unreal-unity-poc/unreal-unity-poc-e2e/pull/2) | new E2E repository | `53b4d9ef78ae` | `c25027e8b534` |
| [declarative-migrations-test/cockroachdb-rollback-e2e#6](https://github.com/declarative-migrations-test/cockroachdb-rollback-e2e/pull/6) | database engine E2E | `8b9b69188307` | `b38feac4da67` |
| [declarative-migrations-test/mysql-shadow-e2e#5](https://github.com/declarative-migrations-test/mysql-shadow-e2e/pull/5) | database engine E2E | `125ebd0ce79d` | `220be6c18f37` |
| [declarative-migrations-test/postgres-lock-contention-e2e#5](https://github.com/declarative-migrations-test/postgres-lock-contention-e2e/pull/5) | database engine E2E | `d81c96862c55` | `7cc28ead37bd` |
| [declarative-migrations-test/redshift-advisory-e2e#4](https://github.com/declarative-migrations-test/redshift-advisory-e2e/pull/4) | database engine E2E | `bd2100d1d8bd` | `1b3bdcf4912b` |
| [declarative-migrations-test/schema-change-online-e2e#3](https://github.com/declarative-migrations-test/schema-change-online-e2e/pull/3) | database engine E2E | `12e6c30a02ee` | `11d1697ed2bb` |
| [declarative-migrations-test/snowflake-advisory-e2e#3](https://github.com/declarative-migrations-test/snowflake-advisory-e2e/pull/3) | database engine E2E | `66c89a26d49f` | `8cce9d96ee80` |
| [declarative-migrations-test/sqlite-migration-e2e#3](https://github.com/declarative-migrations-test/sqlite-migration-e2e/pull/3) | database engine E2E | `ea6cba253f3d` | `f8c50c757321` |

## Evidence

- Project ledger: workflow run [31042139871](https://github.com/fiducia-cloud-test/.github/actions/runs/31042139871).
- Retained artifact: `organization-e2e-provisioning`, artifact ID `8945157777`.
- Artifact digest: `sha256:e7b190555fa01adedfea8ff69cd636573008f4cfd568c4ca226ed9dd594bec81`.
- Machine-readable sources: `.github/data/e2e-projects.tsv` and `.github/data/e2e-pull-requests.tsv`.
