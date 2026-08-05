<!-- org-project-routing:start -->
# Project routing

- **GitHub organization:** [fiducia-cloud-test](https://github.com/fiducia-cloud-test)
- **Organization GitHub Project:** [fiducia-cloud-test-project](https://github.com/orgs/fiducia-cloud-test/projects/1) (project 1)
- **Shared Linear project:** [fiducia-cloud](https://linear.app/denman/project/fiducia-cloud-8fd5e1bec9d3)
- **Production organization:** [fiducia-cloud](https://github.com/fiducia-cloud)
- **Production GitHub Project:** [fiducia-cloud-project](https://github.com/orgs/fiducia-cloud/projects/1) (project 1)
- **Program issue:** [DEN-2353 — Everything E2E](https://linear.app/denman/issue/DEN-2353/e2e-program-certify-every-fiducia-production-surface-through)
- **Program plan:** [Everything E2E — Full-System Test Program](https://linear.app/denman/document/everything-e2e-full-system-test-program-57e84c9eb677)
- **Organization documentation repository:** [fiducia-cloud-test/.github](https://github.com/fiducia-cloud-test/.github)

## One planning project, two execution boards

Both GitHub organizations share the single Linear project `fiducia-cloud`. Do not create a second Linear backlog for the test organization. Linear owns outcomes, priorities, dependencies, milestones, acceptance criteria, and release-readiness status.

Each organization keeps GitHub Project #1 for its execution boundary:

- `fiducia-cloud` tracks production repository delivery, releases, migrations, deployments, and product-side tests.
- `fiducia-cloud-test` tracks independent probes, consumer harnesses, compatibility matrices, chaos/scale/recovery execution, and retained certification evidence.

Every GitHub Project item should link to a canonical Linear issue. Every Linear issue should link to the relevant repositories, pull requests, workflow runs, and evidence bundles.

## Status vocabulary

A GitHub item may report `declared`, `harness`, `local-executable`, `independent`, `destructive`, `release-certified`, `blocked`, or `failed`. Only evidence-backed `independent`, `destructive`, and `release-certified` states satisfy certification gates. A skipped or credential-blocked workflow never counts as passed coverage.

## Change and merge policy

Documentation and automation changes use pull requests and merge after review/checks. Concurrent edits are reconciled semantically against the latest default branch. Preserve unrelated prose and regenerate managed blocks without blindly choosing one side of a conflict.
<!-- org-project-routing:end -->
