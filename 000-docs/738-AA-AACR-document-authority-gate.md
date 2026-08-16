# Document Authority Gate — After-Action Review

- **Date:** 2026-08-15
- **Authority:** Blueprint 727, Epic 2 bead 2.3
- **Bead:** `claude-hedb.2`
- **Implementation PR:** [#1200](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1200)
- **Reviewed head:** `d38fac6d7929c0d3a0cc8d164ab4bc54e74380ae`
- **Merge commit:** `6dc74d6fc157916f4ee4825cabae05cf6a6b22c1`
- **Status:** Implementation complete; Bead closure follows successful filing of this AAR

## Outcome

The existing `doc-governance` job now rejects effective `AUTHORITATIVE` or `CANONICAL` document
status metadata unless `STANDARDS.md` § Canonical documents links the claimant. The validator scans
tracked `000-docs/**/*.md`, parses the canonical table as the sole grant source, and fails closed on
ambiguous statuses, malformed tables, inactive or unsafe links, unreadable inputs, and Git inventory
failure. Document 264 was demoted to `REFERENCE` because `SCHEMA_CHANGELOG.md` and 6767-b already own
its schema facts.

## Before and after

| Measure                          | Before | After |
| -------------------------------- | -----: | ----: |
| Effective status-based claimants |      3 |     2 |
| Unlinked authority violations    |      1 |     0 |
| Canonical-table links            |     10 |    10 |
| Deterministic validator tests    |      0 |     8 |
| Required GitHub status contexts  |      3 |     3 |

The detached-base command ran the reviewed validator against clean commit
`80da5012bce3473dbdbc76c61b31d9b850f046c3`. It exited 1 at document 264 line 3 and reported one
violation among three claimants. At the reviewed head, the live command exited 0 with exactly two
linked claimants—6767-b and activated blueprint 727—and ten canonical links. The blueprint's older
headline count uses a stale or different cohort; E2.6 must reconcile it rather than broadening this
status-based detector.

## Verification evidence

- `node --test scripts/check-doc-authority.test.mjs` passed 8/8 tests. The CLI fixture planted an
  unlinked claimant and proved a non-zero, path-and-line diagnostic.
- An independent clean-checkout reviewer planted a separate claimant and probed comments, fences,
  malformed and duplicate metadata, traversal, untracked targets, and inactive links; verdict PASS.
- `node scripts/check-doc-authority.mjs` reported
  `document-authority: OK (2 effective claimant documents; 10 canonical-table links)` after merge.
- Docs-ignore reported 21 passing assertions; citation governance reported 20 baselined pairs and
  zero new failures; generated-artifact, actionlint, formatting, lint, typecheck, and secret checks
  passed.
- Every exact-head GitHub check passed, including `ci-required`, `gitleaks`, `skill-conform`, the
  complete Validate Plugins fan-out, link-check, prescreen, MiniMax Review, and MiniMax Adversarial
  Review.
- The complete PR diff changed only the authority validator and tests, fixtures, existing workflow
  wiring, document 264's status line, and `CHANGELOG.md`. STANDARDS.md, frozen 6767 bodies, mirrored
  content, catalogs, source locks, and package content were unchanged.

## Review and merge topology

MiniMax first requested a pinned ten-link assertion and durable detached-base evidence. Commit
`d38fac6d7` added the assertion; the exact command and output were attached to the PR and Bead.
Independent review then required the PR body to name the current head and make rollback verification
executable; both record corrections landed without a code-head change, after which the reviewer
returned PASS.

Platform owner Jeremy authorized administrator bypass after every exact-head executable, bot, and
independent-review gate passed. GitHub still required one approval, but no genuine second reviewer
identity was available. The bypass replaced only that approval-topology gap and was disclosed in the
PR; no branch rule, required context, or workflow gate changed. Epic 10 retains the permanent review
topology remediation.

## Scope and rollback

No registry, credential, contributor, Plane, branch-protection, package, production, or mirrored
content mutation occurred. No other Epic 2 bead was activated. Rollback is
`git revert -m 1 6dc74d6fc157916f4ee4825cabae05cf6a6b22c1`. Confirm document 264 returns to
`AUTHORITATIVE` and the validator, fixtures, workflow step, and changelog entry disappear. Then run
the validator from a detached worktree at reviewed head `d38fac6d7` against the reverted checkout;
it must report document 264 as unlinked and exit non-zero.

## Lessons and next gate

Authority is a graph edge granted by the canonical index, not a property a document can assign to
itself. Markdown visibility rules are part of that security boundary: comments, fences, historical
footers, and malformed links must be handled deliberately. The next Epic 1–3 slice requires separate
Beads/Dolt activation after this record is filed and E2.3 closes.
