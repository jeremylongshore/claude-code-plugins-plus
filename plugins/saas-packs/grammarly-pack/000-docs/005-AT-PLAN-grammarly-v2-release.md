# Grammarly v2 release and review plan

## Implementation gates

- [x] Audit all 24 v1 skills against official Grammarly sources.
- [x] Define five distinct production workflows and migration dispositions.
- [x] Complete deterministic scripts, references, eval specifications, and tests.
- [x] Remove unsafe canonical skills and stale source-database templates.
- [x] Regenerate curated, Freshie, catalog, search, README, and SaaS lattice projections.

## Validation gates

- [x] Focused offline Grammarly tests and Python compilation.
- [x] Marketplace skill schema and strict conformance.
- [x] Unicode hygiene, secret scan, lint, typecheck, generated-artifact checks.
- [x] Repository CI-equivalent verification.
- [x] Independent Luna-high forward testing, including adversarial inputs.

## PR gates

- [x] Commit and push an exact reviewed HEAD.
- [x] Open [PR #1449](https://github.com/jeremylongshore/tons-of-skills-marketplace/pull/1449), linked to Beads `claude-juoz.3.11.1`.
- [x] Wait for required checks and available configured automated reviewers; document unavailable integrations.
- [x] Independently reproduce or reject every material reviewer claim.
- [x] Report status and exact HEAD SHA to Jeremy before any merge.

MiniMax's primary, adversarial, and A-grade-coach lanes completed. Greptile did not
engage the PR despite a valid repository configuration; its latest observed repository
comment was on 2026-08-26. Restoring Greptile or explicitly waiving that unavailable
external review remains a merge-time maintainer decision. The independent disposition
is recorded in the [PR discussion](https://github.com/jeremylongshore/tons-of-skills-marketplace/pull/1449#issuecomment-5550254153).

A final Luna security pass found that the curated document evaluator still resolved
two runtime modules through the source-pack directory layout. The release candidate now
bundles those reviewed modules inside the evaluator skill, removes the obsolete pack-level
copy, and executes the curated workflow in the focused regression suite. That suite passes
34/34, and curated promotion checks the bundled files byte-for-byte against their canonical
skill source.

No merge or publication is authorized by this plan.
