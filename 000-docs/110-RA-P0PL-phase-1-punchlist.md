# Phase 1+ Punchlist (Factual, No Fixes in Phase 0)

This is a factual list of follow-ups discovered while doing Phase 0 repo hygiene. It is intentionally “evidence-first”.

## Dependency Manager / Lockfile Reality

- **Two lockfiles exist by design**: `pnpm-lock.yaml` at repo root vs `marketplace/package-lock.json` for Astro site.
  - Evidence: `package.json` (root) vs `marketplace/package.json`.
- **Generated/derived lock artifacts exist under `node_modules/`** and should not be treated as source-of-truth.
  - Evidence: `node_modules/.pnpm/lock.yaml`, `marketplace/node_modules/.package-lock.json`.
- **Potential confusion**: root scripts mention `pnpm install --frozen-lockfile`; marketplace scripts use `npm`.
  - Evidence: `CLAUDE.md`, root `package.json`, `marketplace/package.json`.

## Workspace Membership Questions (no decision in Phase 0)

- `packages/analytics-dashboard/` exists on disk but is not listed in `pnpm-workspace.yaml`.
  - Evidence: `pnpm-workspace.yaml`, `packages/analytics-dashboard/`.
  - Phase 1 decision: include it in the workspace, or remove/archive it consistently.

## CI / Verification Clarifications

- CI entry points and deploy workflows live in `.github/workflows/`; Phase 0 does not alter them.
  - Evidence: `.github/workflows/`.

## Verification Script / Tooling Mismatches

- `node scripts/check-package-manager.mjs` currently flags `marketplace/package-lock.json` as a forbidden lockfile (even though `marketplace/` is intended to be npm-managed).
  - Evidence: `scripts/check-package-manager.mjs`, `marketplace/package-lock.json`, `CLAUDE.md`.
  - Phase 1 decision: update policy script to allow `marketplace/package-lock.json`, or change marketplace dependency management approach.
- `python3 scripts/validate-frontmatter.py` requires a specific markdown file argument (not “validate everything”).
  - Evidence: running without args prints `Usage: check-frontmatter.py <markdown-file>`.
- CLI lint appears misconfigured for ESLint v9: `eslint` fails because no `eslint.config.(js|mjs|cjs)` is present.
  - Evidence: `packages/cli/package.json` (`lint: eslint src`) + ESLint v9 error output.
- CLI tests run `vitest` in watch/DEV mode by default and may not exit in automation; it also reports “No test files found”.
  - Evidence: `packages/cli/package.json` (`test: vitest`) + vitest DEV output.

## Homepage Search Behavior / Requirements

- Marketplace homepage search behavior is covered by Playwright tests and documented in marketplace testing docs.
  - Evidence: `marketplace/tests/T1-homepage-search-redirect.spec.ts`, `marketplace/TESTING.md`, `marketplace/TESTING_QUICK_REFERENCE.md`.
- Mobile UX findings include homepage search toggle issues (historical evidence).
  - Evidence: `000-docs/106c-RA-AUDT-mobile-ux-findings.md`.

## Beads / Multi-Worktree Operational Gotchas

- Local clones may include a separate git worktree for `main` under `.git/beads-worktrees/main`.
  - Evidence: `git branch -vv` output (Phase 0 evidence snapshot).
  - Operator note: ensure you are on the correct worktree/branch before making changes.
