# Fiducia Cloud test-fleet reconciliation

Audit date: 2026-08-05

The canonical portfolio declares one policy repository plus sixteen consumer, conformance, chaos, failover, scale, and bridge repositories for `fiducia-cloud-test`. The remote organization currently contains the policy repository and an additional TypeScript client harness.

## Present

- `.github`
- `fiducia-typescript-client-e2e` (preserved extra repository)

## Missing canonical certification repositories

- `rust-client-consumer`
- `typescript-client-consumer`
- `go-client-consumer`
- `python-client-consumer`
- `java-client-consumer`
- `kotlin-client-consumer`
- `dart-client-consumer`
- `swift-client-consumer`
- `gleam-client-consumer`
- `erlang-client-consumer`
- `package-ingestion-matrix`
- `locks-leases-conformance`
- `raft-network-chaos`
- `cron-failover`
- `websocket-scale`
- `nats-dlq-bridge`

## Hardening already in progress

`fiducia-cloud-test/fiducia-typescript-client-e2e#2` adds executable stale-fence, retry/idempotency, redirect-refusal, leader-failover, WebSocket-resume, and NATS dead-letter replay contracts.

## Completion rule

The fleet is not complete until every canonical repository exists with immutable source coordinates or an explicit source gate. Extra repositories are retained, and missing live credentials must be classified separately from product or harness failures.
