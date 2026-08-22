<!-- doc-class: record -->

# Epic 4 Unverified-Secret PR Scan — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 4 bead 4.6 (strictly after 4.5)
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-or1m.6`
- **Implementation PR:** [#1282](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1282)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E4.6 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

The union gap is closed. Before this slice, the blocking scanner (gitleaks) was
rule-shape-based and the only trufflehog run was weekly, full-history, `--only-verified` — so
a **rotated key or an internal token whose issuer cannot be probed never gated a PR**; it was
invisible to both scanners. `validate-plugins.yml` now carries `secret-diff-scan`: trufflehog
over the exact PR range (`base.sha`..`head.sha`), **without** `--only-verified`
(`--results=verified,unknown` — both fail the job), SHA-pinned to the same v3.95.9 commit as
the weekly job, in `ci-required.needs` (the 22nd gate job; the CLAUDE.md prose count is
updated and the E2.8 fact assertion re-pins it).

## Serial-order discipline

E4.5 (the gitleaks de-blanket, #1280) merged first, per the blueprint's STRICTLY SERIAL edge —
"or the new scan drowns in the same false positives and gets neutered." The measured
false-positive posture at landing: trufflehog without `--only-verified` produced **0 findings
across the repo's prior 30 commits** — detector-shape matching does not fire on the corpus's
teaching placeholders the way generic-entropy rules would. (A full-tree _filesystem_-mode run
was also attempted and abandoned at 8k+ findings/10 min — confirming diff-scoped **git** mode
as the only viable shape.) Per the blueprint, the first week's measured FP count on live PRs
gets recorded on the bead.

## Register maintenance

790 § 2's union-gap row flipped to `E4.6 closed`; the compare-page row's note updated now that
E4.5/E4.6/E4.7 all exist (residual: the stalled-fork-PR class and `enforce_admins:false`).

## Verification

Local diff-scoped run over the last 30 commits (exit 0, 0 findings) quoted above; the job's
step-level `if: pull_request` designed-skip keeps the aggregate honest on non-PR events (the
same pattern as `scan-synced-content`); this PR's own hosted run is the first live execution
of the job — over a diff that includes this very change.
