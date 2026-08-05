# GitHub organization Project reconciliation

This control plane reconciles GitHub Projects v2 for the canonical 41-portfolio registry.

## Source of truth

The authoritative cross-system registry remains:

- repository: `ORESoftware/k8s-cluster`
- file: `ops/registries/portfolio-project-links.csv`
- pinned execution revision: `db63f6912c78fe95b703fa770148263fad671703`

The registry records, for every portfolio:

- canonical lowercase `portfolio_key`;
- case-preserving GitHub organization login;
- exact GitHub Project number, title, and URL;
- native Linear project ID, name, and URL;
- Slack channel identity and URL;
- ChatGPT project key.

The naming contract is `<GitHub organization login>-project`. Forty organizations use Project #1. `dancing-dragons` intentionally retains Project #4.

## Execution

`.github/workflows/reconcile-organization-projects.yml`:

1. loads the fleet PAT from `FLEET_GH_TOKEN` without printing it;
2. verifies the authenticated login is `ORESoftware`;
3. fetches the pinned canonical registry from `ORESoftware/k8s-cluster`;
4. validates the exact 41-row inventory and number/title/URL contract;
5. verifies active organization-admin membership;
6. creates a missing canonical project, or retitles the canonical project number when needed;
7. updates every Project description and README with its canonical Linear link and registry marker;
8. verifies the resulting project number and title; and
9. uploads JSON and Markdown reconciliation evidence.

The reconciler fails closed for duplicate titles, an exact title at the wrong project number, a project created at a noncanonical number, missing project scope, missing organization-admin access, or incomplete Linear identity.

The review branch intentionally receives a second push after the workflow file exists, ensuring GitHub evaluates the real reconciliation workflow rather than only the repository's pre-existing policy checks.

## Credential boundary

Only GitHub Project metadata is reconciled by this workflow. Linear documentation is written through the connected Linear app, not by copying a Linear API key into this repository. Slack and ChatGPT are not mutated by this GitHub-only run.

The PAT must have the GitHub `project` scope and organization administration rights. Rotate it immediately if exposed outside protected GitHub Actions secrets.
