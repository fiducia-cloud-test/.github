# Fiducia Cloud test-fleet audit and gaps

Audit date: 2026-08-05
Canonical planning project: [`fiducia-cloud`](https://linear.app/denman/project/fiducia-cloud-8fd5e1bec9d3)
Program issue: [DEN-2353](https://linear.app/denman/issue/DEN-2353/e2e-program-certify-every-fiducia-production-surface-through)

## Live inventory

The organization currently contains **43 repositories**:

| Class | Count |
|---|---:|
| organization governance | 1 |
| language-specific SDK E2E | 10 |
| focused API/system/failure suites | 21 |
| clean SDK consumers | 10 |
| package-ingestion matrix | 1 |

The earlier 32-repository count and legacy names such as `locks-leases-conformance`, `raft-network-chaos`, `cron-failover`, `websocket-scale`, and `nats-dlq-bridge` are no longer an accurate description of the live fleet. The current canonical names are recorded in [`../test-program/catalog.json`](../test-program/catalog.json).

## Most important finding

Name/count coverage is broad, but executable depth is not yet proven across the fleet. A representative specialized repository has useful immutable source pins and a generated `test-plan.json`; its scheduled integration workflow currently validates the plan and prints the intended profile instead of launching Fiducia and asserting the advertised invariants.

Until a repository has retained run evidence, its conservative maturity remains:

- `L0` for a declared plan/source pin;
- `L1` for harness or schema validation;
- not `L4` independent acceptance merely because its workflow is green.

`fiducia-cloud/fiducia-e2e` is materially deeper and already documents executable local, multi-node, browser, multicluster, chaos, and strict Hetzner proof modes. The test fleet should reuse that orchestration/assertion machinery while preserving independent black-box ownership.

## Immediate gaps

1. **Truthful catalog:** map all active production repositories and all 43 test repositories to owners, capabilities, environments, cadence, current/target maturity, and evidence.
2. **Immutable release/evidence contract:** every test must name exact source/package/image/interface/topology identities and emit a verifiable evidence bundle.
3. **Core safety execution:** API, Raft/quorum, routing, locks/leases/fencing, idempotency, cron, and tenant isolation must be executable and fail closed first.
4. **Data/control-plane execution:** NATS/DLQ, WebSockets, memory resize, sync, edge recovery, agent/operations control planes, Lambda, payments, and telemetry need real product assertions.
5. **Consumer compatibility:** all language E2E and clean consumer repositories must install published or immutably pinned artifacts and execute black-box calls, including version skew.
6. **Operational proof:** upgrade/downgrade, migration/rollback, backup/restore, clean-room DR, load/soak, chaos, secret rotation, and provider failure need retained evidence.
7. **Program health:** flake budgets, quarantine expiry, cleanup verification, CI-capacity parity, dashboards, and stale-evidence alerts are required.

## Repository-creation gate

Do not create repositories merely to increase count. A new repository is justified only when the catalog proves a unique acceptance boundary that cannot fit an existing suite.

Candidates requiring gap proof include:

- `upgrade-downgrade-compat-e2e`
- `backup-restore-dr-e2e`
- `data-migration-rollback-e2e`
- `supply-chain-provenance-e2e`
- `policy-rbac-abuse-e2e`
- `performance-regression-e2e`
- `sdk-version-skew-e2e`
- `customer-journey-e2e`
- `docs-quickstart-e2e`
- `billing-metering-audit-e2e`
- `operator-disaster-game-day-e2e`

Each accepted repository must start with ownership, non-overlap, immutable pins, executable local L2 smoke, a path to independent L4/L5 execution, evidence output, budgets, cleanup, and project routing. Generated profile-printing alone is not an acceptable bootstrap.

## Completion rule

The fleet is complete when every active production surface has an executable ownership path, required release lanes consume one immutable release manifest, core safety has independent and failure-mode evidence, all skipped/blocked/quarantined states remain visible, and a release decision can be reconstructed from retained evidence without trusting repository count or green badges.