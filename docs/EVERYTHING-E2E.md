# Everything E2E

This document is the GitHub-side operating contract for the shared Fiducia test program.

- Linear plan: [Everything E2E — Full-System Test Program](https://linear.app/denman/document/everything-e2e-full-system-test-program-57e84c9eb677)
- Parent issue: [DEN-2353](https://linear.app/denman/issue/DEN-2353/e2e-program-certify-every-fiducia-production-surface-through)
- Milestone: `Everything E2E — Full-System Certification`
- Production organization: [fiducia-cloud](https://github.com/fiducia-cloud)
- Test organization: [fiducia-cloud-test](https://github.com/fiducia-cloud-test)

## Responsibilities

### Production repositories

Every active `fiducia-cloud/*` repository owns white-box unit/component tests, schema and migration tests, deterministic local fault tests where appropriate, and immutable package/image publication. A production PR must identify its test impact and the exact artifact passed to independent acceptance.

### Cross-system orchestrator

`fiducia-cloud/fiducia-e2e` owns shared black-box assertions and orchestration. It already documents real HTTP conformance, local three-node composition, browser journeys, three-cluster execution, chaos, and strict Hetzner proof. Reuse and extract those capabilities instead of rebuilding a second monolith.

### Shared harness

`fiducia-cloud/fiducia-test-config` owns environment schemas, process lifecycle, deterministic fixtures/seeds, retry/time budgets, cleanup, redaction, JUnit output, and evidence helpers. Test repositories consume a versioned release or immutable SHA.

### Independent probes

Each `fiducia-cloud-test/*` repository owns a narrow black-box acceptance boundary. It consumes pinned deployable artifacts, launches or targets a real topology, asserts behavior, injects relevant failures, classifies failures, emits sanitized evidence, and verifies cleanup.

## Truthfulness rules

1. A generated `test-plan.json`, source pin, schema validator, or profile-printing workflow is inventory—not product coverage.
2. A test skipped because no endpoint, route, capability, credential, provider, or browser exists is `blocked` or `not-run`; it is never a pass.
3. Pull-request smoke may skip provider-dependent execution, but release certification fails closed.
4. No mutable branch, floating package range, unpinned action, or `latest` OCI tag may enter a release proof.
5. A retry does not erase the first failure. Evidence records all attempts and the configured retry budget.
6. Quarantine requires an owner, linked defect, reason, expiry, and non-release status. Required release gates cannot be quarantined into green.
7. Cleanup is an assertion. Residual resources are recorded and fail the run when policy requires zero residue.

## Maturity

| Level | Required evidence |
|---|---|
| `L0` | declared scope and immutable source/release intent |
| `L1` | executable harness/schema self-test |
| `L2` | real product artifact launched locally and behavior asserted |
| `L3` | multi-component or multi-node local execution |
| `L4` | independent test-org execution against pinned artifacts |
| `L5` | destructive, partition, scale, security-adversarial, or recovery execution |
| `L6` | staging/production-like release certification with retained attestation |

The catalog records conservative current maturity. It may only be raised by linking retained evidence that satisfies the level.

## Evidence bundle

Every executable run produces a versioned manifest containing:

- run/trigger/repository/commit/workflow identity and UTC timestamps;
- production source SHAs, package versions, OCI digests, interfaces, migrations, harness version, and feature gates;
- provider/topology/cluster/member identity and redacted configuration hash;
- deterministic seed, selected tests, retries, timeouts, and failure-injection timeline;
- JUnit assertions, structured logs, OpenTelemetry trace IDs, metrics snapshots, and relevant sanitized events;
- product, dependency, environment, credential, or harness failure classification;
- cleanup result and residual-resource inventory; and
- hashes linking the manifest to retained artifacts.

## Cadence

| Trigger | Minimum expectation |
|---|---|
| pull request | credential-free L0/L1 plus selected deterministic L2 smoke |
| merge/main | pinned artifact build, API compatibility, local L2/L3 system coverage |
| nightly | broad non-destructive L4 probes and version-skew matrix |
| weekly | failure injection, browser matrix, NATS/DLQ, load steps, restore rehearsal |
| release candidate | all required L4/L5 lanes against one immutable release manifest |
| monthly game day | destructive multi-cloud, clean-room restore, rollback, rotation, long soak, runbooks |

GitHub-hosted and self-hosted `gha-indie-worker` execution must produce the same evidence format. Runner or Actions-minute exhaustion is blocked execution, not success.

## Delivery order

1. [DEN-2354](https://linear.app/denman/issue/DEN-2354/e2e-010-build-the-live-repositorycapability-catalog-and-truthful): live catalog and truthful maturity validator.
2. [DEN-2355](https://linear.app/denman/issue/DEN-2355/e2e-110-standardize-immutable-release-manifests-and-signed-evidence): immutable release/evidence contract.
3. [DEN-2356](https://linear.app/denman/issue/DEN-2356/e2e-210-make-api-raft-routing-and-coordination-probes-executable-and): API, Raft, routing, and coordination safety.
4. [DEN-2357](https://linear.app/denman/issue/DEN-2357/e2e-310-certify-auth-tenant-isolation-secrets-and-real-browser): identity, secrets, tenant isolation, and browser journeys.
5. [DEN-2358](https://linear.app/denman/issue/DEN-2358/e2e-410-certify-messaging-natsdlq-websockets-memory-resize-sync-and): data movement, WebSockets, memory, sync, and edge.
6. [DEN-2359](https://linear.app/denman/issue/DEN-2359/e2e-510-certify-agent-and-operations-control-planes-lambda-payments): control planes, Lambda, payments, and telemetry.
7. [DEN-2362](https://linear.app/denman/issue/DEN-2362/e2e-610-execute-every-sdk-clean-consumer-package-cli-mcp-and-version): SDK, package, CLI, MCP, and version skew.
8. [DEN-2363](https://linear.app/denman/issue/DEN-2363/e2e-710-certify-multi-cloud-infrastructure-upgraderollback): infrastructure, upgrade, rollback, backup, restore, and DR.
9. [DEN-2364](https://linear.app/denman/issue/DEN-2364/e2e-810-add-load-soak-chaos-flake-budgets-quarantine-and-ci-capacity): load, soak, chaos, flake, and CI capacity.
10. [DEN-2367](https://linear.app/denman/issue/DEN-2367/e2e-910-create-only-catalog-proven-missing-test-repositories-and): gap-proven repository creation only.
11. [DEN-2371](https://linear.app/denman/issue/DEN-2371/e2e-1010-run-immutable-release-candidate-certification-and-publish-the): immutable release certification and go/no-go record.

## Repository creation

The live fleet already has 43 repositories. Create another only when the catalog proves a unique, uncovered acceptance boundary. A new repository must arrive through a reviewed pull request with ownership, non-overlap, immutable pins, executable L2 smoke, a scheduled/manual path to L4/L5, evidence output, budgets, cleanup, dependency/security automation, and project routing. Repository count is never a success metric.