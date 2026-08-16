# Catalog Shadow Guard — After-Action Review

**Date:** 2026-08-15  
**Authority:** Blueprint 727, Epic 1 bead 1.1  
**Bead:** `claude-hz8f.1`  
**Implementation PR:** [#1196](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1196)  
**Reviewed head:** `ed18ed4a0fa065f7ec5ae6aa86cb9f48f330ae78`  
**Merge commit:** `94e84d4c989fb1b9e214a6df2e00225bde557b92`  
**Status:** Complete

## Outcome

The tracked stale catalog backup was removed and the existing catalog invariant now proves that
Git tracks exactly the two root catalog paths governed by `STANDARDS.md`. It rejects any additional
`marketplace*.json*` shadow and fails closed when either canonical catalog is missing or Git cannot
enumerate the tracked inventory.

## Before and after

| Measure                           | Before |     After |
| --------------------------------- | -----: | --------: |
| Tracked root catalog-shaped files |      3 |         2 |
| Tracked catalog shadows           |      1 |         0 |
| Canonical catalog entries         |    471 |       471 |
| Stale backup entries              |    234 |   removed |
| Targeted regression tests         |      0 | 5 passing |

The deleted backup's blob was `c9bb532a6c5a28d162f718961a05c1041090dbe2`.

## Verification evidence

- `python3 -m pytest -q tests/test_validate_catalog_invariants.py` — `5 passed`.
- `python3 scripts/validate-catalog-invariants.py` —
  `Catalog invariant check passed (471 plugins).`
- Independent clean-checkout review planted its own shadow variants and exercised empty inventory,
  `git ls-files` failure, and process `OSError`; every failure was visible and non-zero.
- `pnpm run sync-marketplace` and the generated-artifact check produced no tracked drift.
- Ruff, Prettier, lint, typecheck, `git diff --check`, MiniMax Review, MiniMax Adversarial Review,
  `ci-required`, `gitleaks`, and `skill-conform` passed at the reviewed head.
- The complete PR diff touched only the deleted backup, validator, regression test, and
  `CHANGELOG.md`. No mirrored content changed.

## Review and merge topology

The independent clean-checkout reviewer returned **PASS**. The repository's one-approval topology
still lacked a second GitHub approval identity. Platform owner Jeremy explicitly authorized an
administrator bypass after all executable and independent-review gates passed. The bypass was
disclosed in the PR record; no branch rule or required status context was changed.

## Scope and rollback

No registry, credential, contributor, Plane, branch-protection, package publication, or production
mutation occurred. Duplicate catalog-entry remediation and every other Epic 1 bead remained out of
scope. Rollback is `git revert 94e84d4c989fb1b9e214a6df2e00225bde557b92`, followed by the targeted
test and live validator; that intentionally restores the prior backup and removes the gate.

## Lessons and next gate

An absence claim is only valid when the inventory source is itself proven complete. Treating an
empty successful Git query as “no shadows” would have left the source-of-truth boundary fail-open.
The next Epic 1 slice must be activated separately in Beads/Dolt after this bead closes.
