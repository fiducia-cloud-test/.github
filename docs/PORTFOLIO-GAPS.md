# Fiducia Cloud test-fleet reconciliation

Audit date: 2026-08-05
Canonical source: `zed-pkg-test/zed-pkg-e2e` live 341-repository manifest

## Current result

The live portfolio declares **31 specialized repositories plus one public `.github` governance repository** for `fiducia-cloud-test`: **32 canonical repositories** in total.

The remote organization currently contains **32 repositories**, so the canonical count is complete. The independently added TypeScript client harness is preserved as part of the current fleet rather than overwritten.

## Remaining verification

Count completeness is established. Name-level drift should be checked against the deterministic canonical index proposed in `zed-pkg-test/zed-pkg-e2e#94`. Every canonical repository must preserve:

- immutable client/interface source pins or explicit source gates;
- credential-free pull-request checks;
- explicit scheduled/manual lanes for multi-node, scale, NATS, and provider-dependent execution; and
- separate product, dependency, credential, and harness failure classifications.

## Hardening in progress

`fiducia-cloud-test/fiducia-typescript-client-e2e#2` adds executable stale-fence, retry/idempotency, redirect-refusal, leader-failover, WebSocket-resume, and NATS dead-letter replay contracts.

## Completion rule

The fleet is complete when the exact canonical name set is present, generated bootstrap pull requests are merged in dependency order, and the language, conformance, chaos, scheduler, scale, and bridge lanes remain green. Extra repositories remain intact.
