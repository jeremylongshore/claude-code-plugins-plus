---
title: "Wrong-Mode Green Is Not a Gate"
description: "A freshness gate that accepts the wrong mode flag and still exits green trains people to trust a board that cannot see. Pin the argv semantics, not just the script path."
date: "2026-07-22"
tags: ["testing", "ci-cd", "python", "architecture", "debugging", "claude-code"]
featured: false
---
A green board is not a gate if the checker ran the wrong mode.

That is the load-bearing failure of 2026-07-22 on the Intent Eval Platform's spec-drift track. A mutation-tested freshness loop shipped clean. An adversarial review of the merged commit then found nine defects. Two of them were P1s that re-entered the exact frozen-versus-frozen bug the machinery exists to end.

The thesis is one sentence: **if a human can flip a registry flag, get a quieter green, and never hit the comparison that reads live captures, you do not have a freshness gate. You have a confidence theater with a nicer dashboard.**

## The problem: green ship, then nine defects

`intent-eval-lab` watches Anthropic and MCP docs the same way supply-chain tooling watches dependencies. Capture upstream bytes. Project them into structured JSON. Diff projections against a hand-reconciled baseline. When a field-level surface is `enforcement: failing`, drift is a hard red, not a polite report.

PR [#237](https://github.com/jeremylongshore/intent-eval-lab/pull/237) gave the deep-capture extractors a real freshness mode and wired it into the watcher. Three surfaces flipped to ENFORCED. The suite passed. Mutation locks held. The board said clean.

Then somebody had to re-read the merge with hostile intent.

That re-read happened because **no AI reviewer runs on these repos right now**. Gemini Code Assist is sunset. Greptile is dark. CodeQL owns security scanning. Correctness and design are the repo's own CI plus human review. One pair of eyes is not a review process; it is a single point of failure with a green checkmark. The adversarial pass was the substitute for the missing bot.

Nine defects reproduced. All nine fixed in [#239](https://github.com/jeremylongshore/intent-eval-lab/pull/239), each with a regression lock mutation-tested by reverting the fix. Two of them were the same class of bug this track keeps repairing: an authoritative green that did not look at the thing it claimed to protect.

## P1: wrong mode, silent green

The registry is the file humans are told to edit. Flipping a surface to `failing` is supposed to be a one-line change. The contract for field-level coverage looks roughly like this:

```json
"semantic_coverage": {
  "status": "field-level",
  "enforcement": "failing",
  "checker": [
    "scripts/extract-marketplace-catalog-projection.py",
    "--check-fresh",
    "--surface",
    "plugin-marketplaces"
  ]
}
```

Before the fix, the registry gate validated that `checker[0]` was an existing file. That is path existence, not mode semantics.

`--surface` is a top-level argparse flag on the extractors. So this argv was accepted, ignored the surface, and exited 0:

```text
scripts/extract-marketplace-catalog-projection.py --check --surface plugin-marketplaces
```

`--check` is the self-consistency path (projection derives from files already on disk). `--check-fresh` is the path that compares against the **captured** tree. Swap the flag and the driver prints an authoritative all-green board, including for `plugin-marketplaces` while real findings still exist.

Verified, not assumed: `check-surface-registry.py` returned exit 0 on a registry with the wrong mode. So did the test suite. Both only asked "does this script exist?"

That is [exit 0 is not success](/posts/exit-0-is-not-success/) wearing a freshness costume. It is also the failure mode described in [every safety gate has a failure direction](/posts/every-safety-gate-has-a-failure-direction/): the next person who flips a surface, sees red, and "fixes" the flag gets a quieter green. No gate objects. The lane dies because people learn not to read it.

### Fix: pin mode, not only path

The registry gate now carries an allowlist of which flag makes each checker a freshness check:

```python
_FRESH_MODE_FLAG = {
    # spec-projection-diff's --check already reads the captured snapshot.
    "scripts/spec-projection-diff.py": "--check",
    "scripts/extract-agent-definition-projection.py": "--check-fresh",
    "scripts/extract-hook-config-projection.py": "--check-fresh",
    "scripts/extract-marketplace-catalog-projection.py": "--check-fresh",
    "scripts/extract-plugin-manifest-projection.py": "--check-fresh",
}

_MODE_FLAGS = {
    "--check", "--check-fresh", "--extract", "--write",
    "--self-test", "--diff", "--list", "--strict",
}
```

Validation is no longer "file exists." It is "this exact script must run in this exact freshness mode, and no other mode flag may ride along." A checker absent from the table is an error: adding one is a reviewed act. `--write` is rejected too, because a gate that mutates the baseline it guards is not a gate.

The extractors themselves now **reject** `--surface` outside `--check-fresh` instead of ignoring it. Two layers: the registry cannot name the wrong mode, and the tool will not silently accept a mismatched argv.

Chose an in-script allowlist over letting the registry self-declare its own mode. A config that attests to its own correctness is exactly the thing being defended against.

## P1: truncated closed enum as confident nonsense

The second P1 was a parser bug with worse UX than an empty result.

`plugin-manifest` pulled closed enums from description prose. A period followed by a digit is a **version number**, not a sentence end:

```text
"One of `command` (Claude Code v2.1.200+), `http`, or `mcp_tool`."
```

Without a closedness guard, that became `['command']`. Sibling extractors declined on residue. This one asserted a short enum. A short enum is worse than absence: the projection is the field-diff baseline, so the next report reads as a legitimate value **removal** and sends a human to reconcile a phantom.

The captured plugins-reference page already carries MDX comments in table cells. It had not yet landed on a `One of` row. Not hypothetical risk; loaded gun.

Fix was one shared rule (`captured_source.clause_end`): period-digit is not clause end. All three sibling extractors recover the full closed set. Mutation tests locked it by reverting the fix.

## The other seven, in one pass

| ID | Defect | Repair |
|---|---|---|
| F3/F9 | Driver printed `CLEAN (exit 0) over 0 field-level surface(s)` on an empty map | Now INOPERABLE, plus a declared `semantic_coverage_floor` so shrinking coverage is a reviewed edit |
| F4 | Malformed capture raised into Python exit 1; driver misread as DRIFT | Parser breakage is INOPERABLE, preserving 0/1/2 |
| F5 | 30-entry enum +1 member looked byte-identical for the first 400 visible characters | Scalar lists diff element-wise |
| F6 | `True == 1` and `1 == 1.0` hid type changes | Type changes always findings |
| F7 | List-valued `enforcement` killed the gate with `TypeError: unhashable type` | Coerce to a named problem |
| F8 | `re.DOTALL` MDX stripper would swallow a multi-line unbalanced `{/*` | Line-bounded strip |

Plus a gap the review surfaced in its own evidence: nothing verified that `vendor-meta.json` describes the bytes on disk. `--check` proves the projection derives from files and never reads sha256. A hand re-vendor with a wrong hash passed every gate. New `scripts/check-vendor-meta-integrity.py` checks existence, sha256, byte count, and undeclared files. Demonstrated: corrupt a recorded sha and the new gate fails while `--check` still prints OK.

That is the same family as [empty is not clean](/posts/empty-is-not-clean/) and [passing is not validating](/posts/passing-is-not-validating/): a check that never looks at the claim under audit.

## Neighbor defect: the bot restored the human baseline

While the nine defects landed, [#238](https://github.com/jeremylongshore/intent-eval-lab/pull/238) closed a live defect that would have fired on the next 09:00 UTC watcher run.

The restore step does the right thing for append-only bookkeeping:

```bash
git checkout FETCH_HEAD -- archive/ specs/_vendor/ specs/lineage/
```

But `specs/_vendor/` holds two trees with opposite ownership:

| Path | Owner | Written by |
|---|---|---|
| `specs/_vendor/<surface>/` | bot | `fetch-capture.py` on FETCH_OK |
| `specs/_vendor/upstream/` | human | hand-vendored reference docs + reconciled projections |

`upstream` is not a surface id. The capture stage cannot write it. The bot branch can only ever hold a **staler** copy. Restoring it can only regress the hand-reconciled baseline.

Reproduced in an isolated worktree with the promotion branch at one SHA and main at another: after restore, projections fell back to the 2026-06-12 baseline, `sub-agents` (now ENFORCED) went DRIFT, and the promotion PR the watcher force-pushes would have proposed undoing main's reconciliation. Silent baseline regression plus a daily red: the lane-nobody-reads failure mode again.

Fix: stop restoring human-owned vendor paths from the bot branch. Bot bookkeeping stays. Human baselines stay on main.

## CodeQL does not get to "fix" evidence

[#240](https://github.com/jeremylongshore/intent-eval-lab/pull/240) unblocked promotion by scoping CodeQL off the capture tiers.

Promotion failed on `js/incomplete-sanitization` inside `specs/_vendor/mcp-spec-docs/snapshot.html`. That file is a verbatim captured modelcontextprotocol.io page. The only way to "fix" the alert is to edit a capture, which corrupts the provenance every drift comparison depends on, and fails `check-vendor-meta-integrity` on purpose.

Choices were: permanent red on every promotion, edit evidence, or scope the scanner to code the repo authors. Path-scoped config wins:

```yaml
paths-ignore:
  - specs/_vendor/**
  - archive/**
  - _vendor/**
```

This narrows **what** is scanned, not how strictly. `scripts/`, `research/`, and every workflow stay on the security-extended suite. Verified the exclusion hides no authored code.

## Closing the loop: five surfaces, all CLEAN

[#241](https://github.com/jeremylongshore/intent-eval-lab/pull/241) reconciled the last field-level surface (`plugin-marketplaces`) against the bytes main actually holds after the promotion merge. All five extractors now run as ENFORCED freshness gates and report CLEAN:

```text
CLEAN  agentskills-spec
CLEAN  claude-hooks
CLEAN  plugins-reference
CLEAN  sub-agents
CLEAN  plugin-marketplaces
projection-freshness: CLEAN (exit 0) over 5 field-level surface(s)
```

The material finding on the marketplace catalog was not bookkeeping. Claude Code now re-checks reserved marketplace names on **every** marketplace load, not only on add. A marketplace already registered under a newly reserved name stops loading and reports an untrusted source. Before v2.1.205 it kept loading. That is live behavioral risk, not a docs niggle.

Estate exposure was checked: no `marketplace.json` under the projects tree uses the new reserved names. The Intent Solutions marketplace name is a suffix-extension of a reserved name and stays a watch item under the "impersonates official marketplaces" prose rule. The finding is the clearest argument yet for the whole track: a real, dated, operational risk that surfaced only because a gate could finally see current bytes.

Pinned extractor self-tests failed loudly on four hard-coded expectation sets when the re-capture shifted field counts. Those sets exist so a re-capture cannot pass silently. Updated them as a human, with reasoning in vendor-meta, not as bare number edits. A test that asserted the marketplace surface still reported DRIFT was retired into the reconciled-clean suite rather than deleted to make the suite pass.

Final lab numbers for the day: 226 pytest cases (33 new on the defect pass), mutation sweep red on every reverted fix, vendor-meta integrity clean over 5 captures and 23 files, audit-harness verify OK.

## Collaboration beat: models and the missing reviewer

Session signal for the day was strong across Claude Opus 4.8, Grok 4.5, and GPT-5.6 Sol: long spans, real failure-to-fix arcs, estate and lab work interleaved.

The interesting collaboration fact is not token volume. It is the gap the review filled. With AI review dark on the lab, Claude Opus 4.8 and Grok 4.5 spent the day implementing and chasing CI. The nine defects came from a deliberate hostile re-read of a commit that had already gone green under mutation tests. Tools did not invent that pass. An operator ordered it because the automated second pair of eyes was gone.

That is the same discipline as [adversarial review before team rollout](/posts/adversarial-review-before-team-rollout/), applied inward to a gate that ships under your own name.

## Also shipped

Secondary work did not get scored into the primary tier dimensions. It still landed:

- **audit-harness**: kernel-shadow detection now anchors on declaration syntax, not the bare `interface`/`type` keyword, so re-exports of kernel types stop looking like shadow declarations. Estate-wide clean under the fixed detector.
- **diagnostic-pro**: client-side gate requires a problem description or symptom before payment (live customer was stuck in a Stripe loop on empty problems); friendly save errors instead of raw JSON at the card; Android build/test breakers from a prior review.
- **now-lms fork**: MiniMax-M3 AI reviewer wired on the deploy branch only, so upstream-sync PRs into `main` are not judged by house rules.
- **intent-os**: plane-separation audit, outside-in collector scaffold, team-atlas dossiers for eleven undossiered repos.
- **bobs-big-brain-umbrella**: audit-harness v1.3.0 vendored; docs-honesty linter hash-pinned; topology maps repointed after engine renames.
- **claude-code-plugins**: promoted [no-ai-slop](https://github.com/petergyang/no-ai-slop) as Killer Skill of the Week for 2026-W30.

## Takeaway

If you run continuous upstream capture, treat these as non-optional:

1. **Pin the mode flag, not only the script path.** Path existence is not a freshness check.
2. **Cap empty and shrinking coverage.** `CLEAN over 0 surfaces` is a bug, not a victory.
3. **Do not restore human baselines from bot branches.** Opposite ownership, opposite lifetime.
4. **Scope security scanners off evidence trees.** Editing a capture to silence CodeQL destroys the artifact the gate exists to protect.
5. **When AI review is dark, schedule a hostile re-read of every green gate merge.** Mutation tests are necessary. They are not a substitute for someone trying to break the claim.

Wrong-mode green is not a gate. It is a board that learned to smile.

## Related posts

- [Exit 0 Is Not Success](/posts/exit-0-is-not-success/)
- [Every Safety Gate Has a Failure Direction](/posts/every-safety-gate-has-a-failure-direction/)
- [A Green Recovery Drill Can Still Be Lying](/posts/a-green-recovery-drill-can-still-be-lying/)
- [Passing Is Not Validating](/posts/passing-is-not-validating/)
- [Empty Is Not Clean](/posts/empty-is-not-clean/)
- [When Green CI Proves Nothing](/posts/when-green-ci-proves-nothing/)
- [Adversarial Review Before Team Rollout](/posts/adversarial-review-before-team-rollout/)
