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
- [Shared Linear planning project: github.com/fiducia-cloud](https://linear.app/denman/project/githubcomfiducia-cloud-8fd5e1bec9d3)
- [Production organization: fiducia-cloud](https://github.com/fiducia-cloud)
- [Production GitHub Project: fiducia-cloud-project](https://github.com/orgs/fiducia-cloud/projects/1)
- [Detailed project-routing contract](../docs/PROJECTS.md)

Linear is the single planning authority for both organizations. The test organization retains its own GitHub Project, repositories, CI history, workflow runs, immutable source pins, and evidence bundles so black-box acceptance remains independently attributable. Do not create work in the canceled `fiducia-cloud-test (superseded)` Linear shell.
<!-- org-project-routing:end -->


<!-- ore-org-baseline:begin -->
## Planning and governance

- Canonical Linear project: https://linear.app/denman/project/githubcomfiducia-cloud-8fd5e1bec9d3
- Organization defaults: https://github.com/fiducia-cloud-test/.github
- Canonical agent policy: https://github.com/fiducia-cloud-test/.github/blob/main/agents.md
- Security policy: https://github.com/fiducia-cloud-test/.github/security/policy

Repositories in this organization use semantic conflict resolution with 3–10 relevant prior commits when useful, full cross-repository context, pull-request delivery, and a hard automated-agent denylist for destructive or history-rewriting operations.
<!-- ore-org-baseline:end -->

<!-- BEGIN MANAGED REPOSITORY RELATIONSHIPS v1 -->
## Repository relationship registry

`fiducia-cloud-test` declares repository roles, dependency edges, cross-organization capabilities, deployment ownership, and the git-submodule/Zed-package contract:

- [Human-readable map](architecture/REPOSITORY_RELATIONSHIPS.md)
- [Machine-readable manifest](architecture/repository-relationships.json)
- [JSON Schema](architecture/repository-relationships.schema.json)

The public registry withholds private repository names and edges.
<!-- END MANAGED REPOSITORY RELATIONSHIPS v1 -->
