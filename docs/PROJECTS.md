<!-- org-project-routing:start -->
# Project routing

- **GitHub organization:** [fiducia-cloud-test](https://github.com/fiducia-cloud-test)
- **Organization GitHub Project:** [fiducia-cloud-test-project](https://github.com/orgs/fiducia-cloud-test/projects/1) (project 1)
- **Shared Linear project:** [github.com/fiducia-cloud](https://linear.app/denman/project/githubcomfiducia-cloud-8fd5e1bec9d3)
- **Production organization:** [fiducia-cloud](https://github.com/fiducia-cloud)
- **Production GitHub Project:** [fiducia-cloud-project](https://github.com/orgs/fiducia-cloud/projects/1) (project 1)
- **Organization documentation repository:** [fiducia-cloud-test/.github](https://github.com/fiducia-cloud-test/.github)
- **Canonical fleet registry correction:** [ORESoftware/k8s-cluster PR #1221](https://github.com/ORESoftware/k8s-cluster/pull/1221)

## One planning project, two execution boards

Both GitHub organizations use the single active Linear project `github.com/fiducia-cloud`. Do not create or route new work to the canceled `fiducia-cloud-test (superseded)` Linear shell.

Each organization keeps GitHub Project #1 for its own execution boundary:

- `fiducia-cloud` tracks production repository delivery, releases, migrations, deployments, and product-side validation.
- `fiducia-cloud-test` tracks independent probes, consumer harnesses, compatibility matrices, chaos/scale/recovery execution, and retained certification evidence.

Every GitHub Project item should link to a canonical issue in the shared Linear project. Every Linear issue should link to the relevant repositories, pull requests, exact workflow runs, immutable source or artifact pins, and evidence bundles.

## Source-of-truth boundaries

GitHub is authoritative for repositories, commits, pull requests, reviews, CI checks, releases, deployable artifacts, workflow runs, and runtime evidence. Linear is authoritative for outcomes, priorities, ownership, dependencies, milestones, acceptance criteria, and release-readiness status.

Sharing Linear planning does not merge the two GitHub organizations. Their repositories, Projects, access boundaries, CI histories, and certification artifacts remain independently attributable.

## Status vocabulary

A GitHub item may report `declared`, `harness`, `local-executable`, `independent`, `destructive`, `release-certified`, `blocked`, or `failed`. Only evidence-backed `independent`, `destructive`, and `release-certified` states satisfy certification gates. A skipped, missing-route, or credential-blocked workflow never counts as passed coverage.

## Change and merge policy

Documentation and automation changes use pull requests and merge after review and checks. Concurrent edits are reconciled semantically against the latest default branch. Preserve unrelated prose and regenerate managed blocks without blindly choosing one side of a conflict.
<!-- org-project-routing:end -->
