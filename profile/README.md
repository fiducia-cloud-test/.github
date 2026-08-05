# fiducia-cloud-test

Independent black-box acceptance and release-certification organization for [fiducia-cloud](https://github.com/fiducia-cloud).

## Live portfolio

The 2026-08-05 audit records **43 repositories**:

- 1 organization governance repository;
- 10 language-specific SDK E2E repositories;
- 21 focused API, consensus, coordination, scheduler, routing, discovery, messaging, WebSocket, memory, identity, telemetry, edge, sync, control-plane, Lambda, payments, infrastructure, CLI, and MCP suites;
- 10 clean client-consumer repositories; and
- 1 package-ingestion matrix.

Repository count is not a quality metric. The fleet is being reconciled from generated test-plan scaffolds into executable, evidence-producing probes. A schema check, source-pin check, clean skip, missing route, or workflow that only prints its profile is **not** product certification.

## Coverage maturity

| Level | Meaning | Release evidence? |
|---|---|---|
| `L0` | declared plan and source pins | no |
| `L1` | harness/schema self-test | no |
| `L2` | real product artifact launched locally and asserted | development only |
| `L3` | multi-component or multi-node local execution | release-candidate input |
| `L4` | independent test-org probe against pinned artifacts | yes, for that topology |
| `L5` | destructive, scale, security, partition, or recovery lane | yes, for that failure envelope |
| `L6` | staging/production-like certification with retained attestation | release gate |

Skipped or blocked work never increases maturity.

## Test-program contract

- [`test-program/catalog.json`](../test-program/catalog.json) is the machine-readable repository and capability ledger.
- [`docs/EVERYTHING-E2E.md`](../docs/EVERYTHING-E2E.md) defines the cross-organization architecture, cadence, evidence, and repository-creation gate.
- [`docs/PORTFOLIO-GAPS.md`](../docs/PORTFOLIO-GAPS.md) records the current audit findings and justified next gaps.
- [`docs/PROJECTS.md`](../docs/PROJECTS.md) defines Linear and GitHub Project routing.

`fiducia-cloud/fiducia-e2e` is the cross-system orchestrator. Repositories here remain independently versioned probes and consumer harnesses; they should reuse shared contracts without becoming copies of the orchestrator.

<!-- org-project-routing:start -->
## Planning and delivery

- [GitHub Project: fiducia-cloud-test-project](https://github.com/orgs/fiducia-cloud-test/projects/1)
- [Linear planning project](https://linear.app/denman/project/githubcomfiducia-cloud-test-ad993264fa5e)
- [Detailed project-routing contract](../docs/PROJECTS.md)

GitHub owns code and delivery evidence; Linear owns planning and dependencies. The linked organization Project provides the cross-repository execution view.
<!-- org-project-routing:end -->
