# Standard E2E repository provisioning

This control plane creates and populates four missing canonical end-to-end repositories:

- `cliptown/cliptown-e2e`
- `memebank/memebank-e2e`
- `meta-agents-demo/metacog-e2e`
- `unreal-unity-poc/unreal-unity-poc-e2e`

## Repository lifecycle

The provisioner verifies the authenticated GitHub login is `ORESoftware` and requires active organization-admin membership before mutation. Each missing repository is created as private, initialized on `main`, and populated on `agent/bootstrap-real-e2e`. The change is submitted as a draft pull request; product PR checks decide whether it is eligible for review and merge.

Every generated repository includes:

- `AGENTS.md` with immutable-pin, secret-hygiene, semantic-merge, and no-test-weakening rules;
- `source-lock.json` with an exact 40-character source commit;
- at least three product-specific journeys;
- a read-only, immutable-pinned GitHub Actions workflow; and
- disabled persisted checkout credentials.

## Real source access

Public source repositories are checked out directly at immutable commits. Private source repositories use unique Ed25519 deploy keys:

- the public key is attached to the source repository as read-only;
- the private key is stored only as `E2E_SOURCE_DEPLOY_KEY` in the corresponding private E2E repository;
- no cross-organization PAT is copied into the generated repositories; and
- reruns rotate the target-specific deploy key before updating the branch.

## Test profiles

- ClipTown: local build/artifact checks, real Chromium variant matrix, and deployed-site smoke.
- MemeBank: real TCP health/shutdown, real HTTP CORS policy, and shared-auth → official ClipTown SDK boundary.
- MetaCog: real binary CLI, HTTP lifecycle/recall, and shared TCP/UDP state/provenance.
- Unreal/Unity POC: strict C11 dynamic host journeys for lifecycle, callbacks/reset, and zero-copy surface data.

## Idempotency and evidence

Existing repositories are preserved. Existing open agent branches and PRs are updated in place. The workflow uploads sanitized JSON and Markdown evidence containing repository URLs, source pins, branch heads, pull-request URLs, creation decisions, and deploy-key IDs—but never private key material or token values.
