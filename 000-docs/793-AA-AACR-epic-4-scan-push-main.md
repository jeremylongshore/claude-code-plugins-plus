<!-- doc-class: record -->

# Epic 4 Supply-Chain Scan on Push-to-Main — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 4 bead 4.7
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-or1m.5`
- **Implementation PR:** [#1281](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1281)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E4.7 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

`validate-plugins.yml` already fired on `push: main`, but the supply-chain scan step gated
itself to `pull_request` — so the scanner judged proposals and never what actually **landed**
(admin merges past a red aggregate, direct pushes). The `scan-synced-content` job now carries a
push-leg step: it scans the push range (`github.event.before`, with the zero-SHA /
unknown-`before` fallback to the parent commit so a forced push cannot silently pass) with
**full grading** — no `--warn-only` on main, REFUSE stays exit 2 and unwaivable.

## Residual, stated per the acceptance cell

`enforce_admins:false` means an administrator can still merge past a red aggregate. This step
makes that state **visible on main** (a red run on the landed commit) rather than silent; it
cannot make it impossible. Making it impossible is Epic 7's publication-gate work, not a scan.

## Register maintenance

The 790 § 3 "PRs only" row flipped to `E4.7 closed` in this same PR.

## Verification

Scanner fixture corpus green locally (`node --test scripts/scan-synced-content.test.mjs`);
workflow edit exercised by this PR's own hosted run; the first real push-leg run is this PR's
merge commit landing on main.
