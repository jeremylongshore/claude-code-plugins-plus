# Epic 2 Supersession Record — After-Action Review

- **Date:** 2026-08-16
- **Authority:** Blueprint 727, Epic 2 bead 2.12
- **Bead:** `claude-hedb.5`
- **Implementation PR:** [#1214](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1214)
- **Reviewed head:** `2795a25a5418d62a05ba7c1e22f655e15e6e6150`
- **Merge commit:** `53bcfc889505028f75bca7a6a41fdc5a55387d53`
- **Status:** Implementation merged and post-merge verification passed; Bead closure follows this filing transaction

## Outcome

Document 746 now defines the repository's reusable supersession transaction. One completed record
must bind the machine-readable frozen class, a controlled `SUPERSEDED–FROZEN` banner, a nonempty
per-section disposition table, the `STANDARDS.md` canonical-pointer task, and one-pull-request
atomicity. The corpus checker discovers tracked Markdown under `000-docs/`, validates every visible
record attempt, rejects malformed or incomplete records, and fails closed when the governed corpus
contains zero completed records.

The completed 6767 reconciliation is the worked example. Documents 6767-a/c/d/e/h received only
the machine-readable frozen marker and a blank line above their existing banners. Every byte below
that prepend remained identical to base `3978bfd38cbe48a22051f40667fca4ff0cedeff1`; 6767-b remains the
live rubric authority and was untouched. The gate runs inside the existing `doc-governance` job, so
the required contexts remain exactly `ci-required`, `gitleaks`, and `skill-conform`.

## Decision and before/after evidence

Before the slice, the tracked documentation corpus contained no visible completed supersession
record and the five blueprint-superseded 6767 standards had no machine-readable frozen marker.
After merge, corpus mode reports one completed record in one tracked document and all five
superseded standards carry the marker. The record's disposition table covers all five documents;
the generated index contains 186 filed documents.

Natural-language interpretation was rejected in favor of strict structure. Direct-banner evidence
is a title-only raw Markdown blockquote containing the controlled title and optional plain ASCII
metadata. Zero to three leading spaces are allowed; code indentation, emphasis variants, HTML
comments, lazy continuations, trailing prose, and self-disclaiming banner text are rejected. The
scanner walks both directions to the record boundary so a hidden comment cannot be separated from
the title by whitespace. The exact machine marker is the only permitted adjacent comment.

The checker uses Git's tracked-path inventory and verifies lexical and physical repository
containment. Symlinks, non-regular files, malformed records, unclosed records, and a zero-record
corpus all fail closed with stable reason codes. No name-based allowlist or hand-lowered baseline
was introduced.

## Verification and independent review

Post-merge verification on `53bcfc889505028f75bca7a6a41fdc5a55387d53` passed:

- `node scripts/check-supersession-template.mjs --all` reported one completed record in one tracked
  document.
- The combined supersession, document-authority, and index suite passed 19/19 post-merge. The final
  implementation-head review additionally ran 11/11 focused supersession tests, 26/26 combined
  governance tests, and 36/36 Epic 1 measurement tests plus the exact scorecard-artifact check.
- `node scripts/check-doc-authority.mjs`, `node scripts/generate-docs-index.mjs --check`, and
  `node scripts/measure-epic-1-scorecard.mjs --check 000-docs/742-RA-DATA-epic-1-scorecard.json`
  passed.
- The exact-base comparison passed 5/5 frozen bodies; `6767-b` and mirror-owned content had zero
  diff.

Required and substantive GitHub checks passed at the reviewed head. Receipts include
[Validate Plugins](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31963065341),
[gitleaks](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31963065352),
[skill-conform](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31963065327),
[actionlint](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31963065340),
and [MiniMax](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/actions/runs/31963080866).
The first normal MiniMax attempt reached its configured ten-minute limit without a verdict. Only
that failed job was retried against the unchanged head; the retry completed successfully and
returned LGTM with nonblocking notes. The adversarial lane's external-state questions were
independently reproduced rather than accepted as prose.

Independent review repeatedly planted hostile fixtures. Early reviews returned the work for
correction after proving fail-open behavior in comment-wrapped markers, negated pointer and
atomicity claims, invalid dispositions, contraction-based negation, self-disclaiming banners,
symlink escape, and increasingly indirect Markdown/comment layouts. Each reproducible defect became
a permanent red proof. The final clean-checkout reviewer tested 10 valid and 42 invalid banner
forms with zero mismatches, reran 11/11, 26/26, and 36/36 suites, verified the five frozen bodies,
and returned
[PASS](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1214#issuecomment-5308895340)
for diff SHA-256 `53b89fe5fd0decf85a86a5eb07cd4c76b53bab18a4d8ab35d82c536bccc9edb9`.

The free Greptile review was inspected at the exact head, but returned only an
[expired-trial notice](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1214#pullrequestreview-4946970538).
It is recorded and was not counted as substantive evidence.

## Generated artifacts and merge topology

The implementation regenerated `000-docs/000-INDEX.md` and scorecard 742 with their canonical
writers. This filing transaction appends document 747 to the public ledger before regenerating the
same artifacts. Their committed bytes must pass both generators' `--check` modes; neither file is
hand-edited. Scorecard row 46 still counts `.gitleaks.toml` path expressions, not public-ledger
negations in `000-docs/.gitignore`, so those populations remain intentionally distinct.

GitHub still required one human approval after exact-head CI, MiniMax, and independent review
passed. The platform owner authorized and the PR record disclosed an administrator bypass solely
for that known review-topology limitation. No branch-protection rule, status context, or approval
policy changed.

## Scope, rollback, and lessons

This slice changed documentation governance, fixtures, the existing validation workflow,
generated documentation artifacts, and `CHANGELOG.md`. It performed no registry, credential,
contributor, Plane, branch-protection, package-release, billing, mirrored-content, provenance, or
production mutation.

Rollback must reverse this AAR filing first, then revert merge commit
`53bcfc889505028f75bca7a6a41fdc5a55387d53`. Regenerate the documentation index and scorecard and
rerun the supersession corpus gate. No external rollback is required.

The principal lesson is that a security-sensitive documentation transaction must recognize a
small controlled syntax rather than infer intent from prose. Hostile review was most valuable when
each bypass was retained as a fixture and the grammar became narrower, deterministic, and
fail-closed.
