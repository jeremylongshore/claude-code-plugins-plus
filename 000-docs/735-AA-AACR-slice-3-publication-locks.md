<!-- doc-class: record -->

# Slice 3 Interim AAR — E7.3 Publication Locks

Status: interim record; code locks are implemented and independently reviewed, while the protected Environment and token rotation remain owner-gated.

## Scope and authority

This slice implements only blueprint 727 §15.1 E7.3. Bead `claude-s03q.4` is authoritative. GitHub is the implementation PR projection. E7.4 release-failure handling, package remediation, branch protection, credentials, registry actions, contributors, and other Epics are prohibited scope.

## Entry-point inventory

The plugin publication entry points are `.github/workflows/publish-changed-packages.yml` and `.github/workflows/publish-all-packages.yml`. Both invoke `scripts/publish-candidate-report.mjs`, and both now invoke `scripts/npm-publication-preflight.mjs` before any credential-capable publish job. `.github/workflows/cli-publish.yml` publishes `packages/cli` and now invokes the same shared preflight before its credential-capable job; it is a separate CLI package path, not a plugin provenance surface. `validate-plugins.yml` is the canonical required-check producer. `release.yml` creates general GitHub releases and tags but does not run npm publish.

Inventory search covered `npm publish`, `pnpm publish`, `NPM_TOKEN`, `NODE_AUTH_TOKEN`, `registry-url`, npm provenance, tags/releases, reusable workflows, and invoked scripts. Existing release-path warning fallbacks and five-tuple gaps are recorded for E7.4 and were not changed here.

## Implemented locks

1. Changed-package publication is triggered only by a completed successful `Validate Plugins` `workflow_run` whose original event is a canonical push to `main`. It validates the canonical repository, nonempty exact SHA, exact-SHA checkout, main ancestry, and first-parent diff semantics for merge commits.
2. A shared preflight queries GitHub Checks and workflow-run evidence for `ci-required`, `gitleaks`, and `skill-conform`. It binds displayed names to observed workflow names/paths, GitHub Actions producer, repository, push event, main branch, exact SHA, successful completion, and the current main pointer. Missing, stale, pending, failed, skipped, cancelled, untrusted, and ambiguous results refuse publication with structured diagnostics and bounded polling.
3. Real publish jobs reference `npm-production`; dry-run/enumeration jobs do not receive `NPM_TOKEN`. The Environment’s protection and token rotation remain owner-only and are not claimed complete by this document.

## Proof and rollback

Fixture tests cover success, missing/failing/cancelled/skipped/pending checks, wrong SHA, untrusted producer, duplicate results, PR/fork rejection, direct/admin merge failure, zero-candidate no-op, and the legacy raw-push red proof. The implementation PR must record the exact reviewed head, merge SHA, workflow conclusions, and independent clean-checkout verdict here or in the Bead closure note after merge. Revert the workflow/script/document commit to roll back code locks; Environment and token rollback follows document 734.

## Blueprint delta

Locks 1–2 are code-complete. Lock 3 is deliberately open pending owner Environment and token actions. E7.4 remains untouched.
