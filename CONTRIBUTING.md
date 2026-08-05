# Contributing

Keep tests black-box where possible. Use synthetic data. Classify every failure as product regression, blocked dependency, or harness regression. Put expensive checks in scheduled/manual workflows.

## AI-assisted pull-request promotion

This policy applies to AI agents and AI-assisted automation. Repository-specific rules may be stricter and take precedence.

An AI agent may merge only when all of the following are true:

1. All required status checks and all relevant tests pass on the exact commit to be merged.
2. The source branch is current with its target, and there are no merge conflicts.
3. There are no unresolved review threads, requested changes, missing required approvals, or known security, privacy, compliance, or data-integrity blockers.
4. The change matches the approved issue and pull-request scope, and compatibility, migration, observability, and rollback implications are understood.
5. The AI records an exact confidence percentage and a concise evidence-based rationale in the pull request.

Confidence is an additional gate, not a substitute for tests, reviews, approvals, or branch protection. Never bypass protections, force-merge, dismiss valid reviews, or represent a skipped, cancelled, neutral, stale, or failing check as passing.

### Feature branch to `dev`

When every gate above passes and the AI's calibrated confidence that the feature is correct, complete, and safe is **strictly greater than 99.1%**, retarget the pull request if necessary and merge it into `dev`, the integration branch.

If confidence is 99.1% or lower, cannot be calibrated, or depends on an unresolved assumption, leave the pull request open and request human review. If the repository has no `dev` branch, do not invent a substitute or merge to production; establish `dev` or follow a stricter repository-specific integration-branch policy first.

### `dev` to `main` or `master`

When every gate above passes for the exact `dev` head commit, all release-level tests pass, and the AI's calibrated confidence that the integrated result is production-ready is **strictly greater than 99.7%**, open or update the promotion pull request and merge `dev` into the repository's production branch: `main` when that is the production branch, otherwise `master`.

If confidence is 99.7% or lower, leave the promotion pull request open and request human review. Do not merge a feature branch directly into `main` or `master` under this confidence policy.

### Confidence discipline

The confidence assessment must account for test relevance and coverage, review findings, security and privacy risk, backward compatibility, data migrations, deployment behavior, observability, and rollback readiness. Do not round up to cross a threshold. Any material unknown or unverifiable assumption keeps confidence below the applicable threshold.

### Merge record

Use the repository's permitted merge method. Re-evaluate all gates whenever the head SHA changes. In the pull request, record the source and target branches, tested SHA, check results, confidence percentage, and rationale before merging.
