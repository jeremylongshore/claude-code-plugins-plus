---
title: "Five AARs and a Count That Blinked"
description: "Filing is the unit, the receipt is the artifact. Five AARs closed Epic 2 docs governance slices, and one count correction needed a second edit."
date: "2026-08-15"
tags: ["documentation", "release-engineering", "devops", "claude-code", "automation"]
featured: false
canonical: "https://startaitools.com/posts/five-aars-and-a-count-that-blinked/"
---
Five AARs landed in one day, numbered 736 through 740, and one of them needed five follow-up commits before its filing could be honest about what the day actually changed. The day's other repo shipped a count that blinked: a "finish" commit that corrected what the "correct" commit had already corrected.

## claude-code-plugins: Epic 2 docs governance closes out, slice by slice

Epic 2 in claude-code-plugins has been a sequence of governance gates closing into the catalog and standards freeze. Today shipped the last five AARs and the four gates under them. Each gate landed as its own PR with its own test, the AAR came in a follow-up PR, and the bead that tracks the slice closed only after both arrived.

The four gates are the day's named artifacts:

`scripts/check-doc-authority.mjs` (284 lines) and its test (204 lines) close the document-authority-pointer gate. Every document under `000-docs/` carries a canonical pointer to its superseding or governing source. The gate enforces that pointer exists and resolves to a tracked file; the fixture file enumerates nine canonical classes (`canonical-class.md`, `conditional.md`, `fenced.md`, `frozen.md`, `linked.md`, `masked.md`, `near-frozen.md`, `ordinary.md`, `reference.md`, `unlinked.md`) so the gate has something to refuse against. A second test pinned the canonical link count to its actual value, which is the kind of enforcement that earns the gate's name rather than its assumption.

`scripts/generate-docs-index.mjs` (186 lines) and its test (199 lines) close the generated-document-index feature. `000-docs/000-INDEX.md` is now produced from the directory contents and the index is regenerated on every plugin-validation workflow run. The test exercises the generator against a fixture tree and verifies the output structure. The fixture is project-shaped, not generic, which is the right level of specificity for a gate that is not yet meant to be reused outside the estate.

`tests/test_prose_anchors.py` (152 lines) plus the matching fixture (`tests/fixtures/prose-anchors/expected-output.json`, 33 lines) close the frozen-prose-anchor gate. A pinned block of prose in a standards document cannot be silently rewritten without failing CI. The gate keys on the prose-anchor JSON sidecar rather than on the rendered HTML, so an edit that does not move the anchor is silently accepted. The choice is deliberate and the test fixture carries the documented behaviour; changing the fixture is the documented way to change the rule.

`scripts/validate-catalog-invariants.py` carries the catalog-shadow invariant (forbid tracked marketplace shadows), which was the day's most-teased AAR because it needed five corrections before the bead could close. The AAR itself is document number 736; the corrections were (in order): correct the tracked document count (`b52bb83`), reconcile index and review topology (`7b1cb4f`), anchor the bypass authorization (`fa012cdae`), satisfy the whitespace gate (`c45f1ab5f`), sequence the AAR before bead closure (`f4228654d`), and only then correct the catalog rollback command (`4b8ff67`). Five follow-up commits. The AAR filed with all six predecessors landed. That is the chain the bead now records, and the chain is itself the audit. Earlier snapshots of the same story would have shipped the gate, filed the AAR, and left the bead without a record that the first filing was wrong about the topology. The corrections are what make the filing honest about what the day actually changed.

The five AARs landed as PRs in cadence with their gates: PR #1195 (governed brain startup fix, the day's actual first slice after the npm-credential lock from yesterday), PR #1196 (catalog shadow invariant fix), PR #1197 (standards freeze), PR #1198 (catalog AAR), PR #1199 (standards freeze AAR), PR #1200 (document authority pointer gate), PR #1201 (document authority AAR), PR #1202 (generated docs index feature), PR #1203 (generated index AAR), PR #1204 (prose anchor CI gate), PR #1205 (prose anchor AAR). Ten PRs by the close, all required checks green, all merged. The Epic 2 close is one PR and one AAR sequence at a time.

The Epic 2 closure owes its completeness to one rule that has held throughout: an AAR ships only after the slice it documents is verifiable from the documents and the code at the same head. The corrective chain on the catalog-shadow AAR was the day's clearest case of that rule catching its own filing before the bead closed. The corrections themselves are now part of the bead, and the next reader who reads 736 alone will not see the chain; the corrections show up via the commit graph (each follow-up commit references 736 in the message body) and via the AAR text itself, which records the topology reconciliation, the whitespace gate, the bypass authorization anchor, and the rollback command correction as named steps. The chain is durable in both directions.

## bobs-big-brain-plugin: a count that needed a second edit

Two commits, both CHANGELOG/PR-body micro-fixes. PR #62 was the native-dependency count correction; PR #63 finished it. The names say the same thing; the diff is not what either name implies. Both touched the same line in the runtime docs to align the published count with the actual plugin manifest after the CHANGELOG moved. The first commit corrected against the manifest. The second commit corrected the line the first commit missed, which a re-read against the merged CHANGELOG surfaced.

This is the same shape as four of the last two weeks' worth of "correct the correction" PR pairs in the corpus. The first edit accepts a measured number. The second edit accepts a different measured number, because the first edit did not re-read the surface it was changing. The cost of the second edit is the same as the cost of the first: one commit, one PR, one CHANGELOG line. The benefit is the README does not lie about the count next week.

The honest question this shape keeps surfacing is whether the first edit should have caught the second. Probably yes, in most cases. The honest answer is the second edit is the cheaper fix in repos where the re-read happens anyway. The corpus is full of these pairs and the corpus is now full enough that the pattern is recognisable on sight. That is either a healthy sign that the verification loop is closing or a worrying sign that the first edit is no longer the substantive work. I do not have a way to tell yet.

## the day's through-line

Epic 2 closes via filing. bobs-big-brain-plugin closes via a count correction. Both are the same shape: an artifact ships with a claim, and the next artifact corrects the claim because the first one did not yet have the evidence it implied. Five AARs in a row is filing-as-procedure; one count correction that needed a second edit is filing-as-bug-fix. The unit is the same in both cases: the next receipt.

The session signal for the day is absent in the analyzer's accepted sense. The blog-backfill session itself showed up in the transcript (auth failures, no work done), and a buzz session with GPT-5.6 Sol showed up alongside it (a cleanup arc that landed in a different repo, on a different frame, and is its own self-contained story rather than today's narrative). Neither intersects the day's two-active-repo arc in a way that earns the collaboration beat, so the beat is skipped. A day with no collaboration arc is allowed to be the day with no collaboration beat; forcing one when the transcript is empty is the failure mode the rules exist to prevent.

The corpus has been on the AAR-as-receipt frame for six posts in two weeks. That is starting to look like a habit rather than a story, and a post that openly names the habit (this is the third in a row) is more useful than a post that pretends each day is fresh. The honest read is the day's work is the closing of Epic 2 plus two CHANGELOG corrections; the framing is "the receipt is the artifact"; and the next AAR will be filed at the rate the slices close. Tomorrow is another day. The slices do not run on a fixed cadence, so the filing cadence follows the slice cadence, not me. That is the protocol's claim, and the day shipped consistent with it.

## Related Posts

- [Four Slices, One Shape](https://startaitools.com/posts/four-slices-one-shape/)
- [Every Fix Failed In The Shape Of The Bug](https://startaitools.com/posts/every-fix-failed-in-the-shape-of-the-bug/)
- [Six Systems Reporting Nothing](https://startaitools.com/posts/the-status-nothing-could-write-to/)
