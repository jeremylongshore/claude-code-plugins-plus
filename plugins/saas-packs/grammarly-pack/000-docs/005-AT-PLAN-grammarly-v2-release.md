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

- [ ] Commit and push an exact reviewed HEAD.
- [ ] Open a PR linked to Beads `claude-juoz.3.11.1`.
- [ ] Wait for required checks and configured automated reviewers.
- [ ] Independently reproduce or reject every material reviewer claim.
- [ ] Report status and exact HEAD SHA to Jeremy before any merge.

No merge or publication is authorized by this plan.
