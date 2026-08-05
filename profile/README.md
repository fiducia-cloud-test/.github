# fiducia-cloud-test

Independent acceptance organization for **fiducia-cloud**.

Ten language-specific SDK consumers plus package, protocol, Raft, cron, websocket scale, and NATS/DLQ certification.

## Portfolio

| Repository | Class | Readiness | Primary dependency path |
|---|---|---|---|
| `rust-client-consumer` | SDK consumer | `ready` | `cargo` |
| `typescript-client-consumer` | SDK consumer | `ready` | `npm` |
| `go-client-consumer` | SDK consumer | `ready` | `go-modules` |
| `python-client-consumer` | SDK consumer | `ready` | `pip` |
| `java-client-consumer` | SDK consumer | `ready` | `maven` |
| `kotlin-client-consumer` | SDK consumer | `ready` | `gradle-maven` |
| `dart-client-consumer` | SDK consumer | `ready` | `pub` |
| `swift-client-consumer` | SDK consumer | `ready` | `swiftpm` |
| `gleam-client-consumer` | SDK consumer | `ready` | `gleam` |
| `erlang-client-consumer` | SDK consumer | `ready` | `rebar3` |
| `package-ingestion-matrix` | package-manager | `ready` | `matrix` |
| `locks-leases-conformance` | protocol conformance | `ready` | `matrix` |
| `raft-network-chaos` | chaos/fault injection | `ready` | `matrix` |
| `cron-failover` | scheduler/failover | `ready` | `matrix` |
| `websocket-scale` | performance/scale | `ready` | `matrix` |
| `nats-dlq-bridge` | interoperability | `ready` | `matrix` |

Pull requests run deterministic harness checks. Emulators, desktop matrices, live APIs/providers, databases, chaos, scale, and soaks are scheduled/manual. Missing upstreams or credentials are blocked readiness—not false passes or product regressions.
