# `fiducia-cloud-test` organization defaults

This public `.github` repository is the canonical home for shared community-health files, organization profile content, contribution guidance, security reporting, agent policy, and repository-boundary notes.

## Durable engineering policy

- This repository defines public organization-wide defaults for `fiducia-cloud-test`.
- Never commit credentials, private keys, access tokens, customer data, or private-repository inventories.
- Resolve Git conflicts semantically: inspect both sides, the merge base, nearby tests and contracts, and normally 3–10 relevant prior commits. Never blindly select all of `ours` or all of `theirs`.
- Prefer focused pull requests, explicit validation, non-destructive Git operations, and documented tradeoffs.
- Cross-repository integration uses versioned interfaces, APIs, SDKs, events, or explicitly owned replicated read models. Services do not reach into another service's database by default.
- `*-infra` repositories and `*-monorepo` application source remain separate. A `*-infra` repository must never appear as a Git submodule under `*-monorepo/apps`.
- Git submodules are reserved for explicitly coordinated editable source composition. Zed packages or immutable artifacts are preferred for package dependencies. Production deploys immutable artifacts or OCI digests, not source clones.

## Inheritance note

GitHub can inherit supported community-health files from this repository when a target repository does not define its own version. Workflows, branch protections, rulesets, repository settings, and arbitrary documentation are not inherited automatically.
