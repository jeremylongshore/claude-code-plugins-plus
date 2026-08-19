---
title: "Make the Guard Prove It Can Fail"
description: "A guard with no reachable red path is not a guard. Four gates in one day whose verdicts were decoupled from the thing they claimed to measure."
date: "2026-08-18"
tags: ["ci-cd", "testing", "devops", "ai-agents", "automation"]
featured: false
canonical: "https://startaitools.com/posts/the-gate-that-could-not-fail/"
---
## The defect class

A gate you have never seen go red is a gate you have not tested. On 2026-08-18, four gates across two repositories turned out to have that problem: a mask that returned ALLOW on a crafted payload, a secret scan that could not fire without its binary, a proof harness that could never pass, and an auditor that could quietly edit the record it audits. A fifth gate, one that worked correctly, is the control at the end.

The shape is transferable. A gate whose verdict cannot move in one direction, always green or always red, is not enforcing anything. It is theater. The only fix that generalizes is to make each gate prove it can fail before trusting that it passed. (The repos each have their own word for the thing that says no: guard, checker, scan, proof, auditor. This post calls them all gates.)

## Gate 1: the quote-unaware mask

Yesterday's post described the count-provenance checker in claude-code-plugins and the quote-aware masking fix that shipped with it ([commit a62f6f946](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/commit/a62f6f94606bedaece2349e01e016533b8a0a53b), "mask quoted markup attributes"). This is the part that fix missed. An independent reviewer subagent in a detached read-only checkout reviewed exactly that head this morning and returned RETURN FOR CORRECTION. The finding:

> The script masking fails open. `<script data-x="/>">const label="marketplace-visible"; const marker='<CountProvenance cohort="marketplace-visible" />';</script>` supplies both label and provenance with no rendered provenance component, yet the checker returns ALLOW.

The mechanism: the masking function tried to skip dead code regions in an Astro file. It walked through frontmatter and raw text elements, masking their contents. The defect lived downstream: the self-closing test that decided where a raw text region ended was not quote-aware, so a `/>` sitting inside a quoted attribute value made a paired `<script>...</script>` look self-closing, ending the region early. The actual script body fell outside the masked region.

The fix lives in `rawTextElementRegions`, the function that decides where a `<script>` or `<style>` opening tag actually ends. It now walks the tag character by character, carrying quote, escape, and brace state, so a `>` or a trailing `/` only counts when it sits outside every quote (scripts/check-published-count-cohorts.mjs, the inner loop):

```javascript
let tagQuote = '';
let tagEscaped = false;
let tagBraceDepth = 0;
let tagEnd = index + opening[0].length;
for (; tagEnd < source.length; tagEnd += 1) {
  const tagCharacter = source[tagEnd];
  if (tagEscaped) tagEscaped = false;
  else if (tagQuote) {
    if (tagCharacter === '\\') tagEscaped = true;
    else if (tagCharacter === tagQuote) tagQuote = '';
  } else if (tagCharacter === '"' || tagCharacter === "'" || tagCharacter === '`') {
    tagQuote = tagCharacter;
  } else if (tagCharacter === '{') tagBraceDepth += 1;
  else if (tagCharacter === '}') tagBraceDepth = Math.max(0, tagBraceDepth - 1);
  else if (tagCharacter === '>' && tagBraceDepth === 0) break;
}
```

Only after that walk finds the true tag end does the self-closing test run, against the unquoted tail of the tag: `openingText.slice(0, -1).trimEnd().endsWith('/')`. The `/>` planted inside the `data-x` attribute never reaches that test because it is consumed as quoted content. A regex cannot do this. You need a character walk that carries quote and escape state. That is more code and slower, and that is the price of a mask you can trust. And if the walk runs off the end of the file without finding a tag end, the checker refuses with MALFORMED_ASTRO_RAW_TEXT rather than guessing: the mask itself now has a red path.

After correction, a later independent review returned PASS. The live gate output: `ALLOW cohorts=5 enforced=5 deferred=50 discovered=51`. All 13 hostile fixture categories passed, including quoted `/>`, malformed raw text, and compound extensions. The diff was 14 files, all in the masking pre-processing and its tests; the counting and provenance verification downstream of the mask did not change.

## Gate 2: exit 127 reads as no-match

The MiniMax defect-lane review flagged a proof script calling `/home/jeremy/.codex/.../validate_plugin.py`, a hardcoded developer-home path whose failure was swallowed by `2>/dev/null ||`. On any box that was not mine, the gate silently downgraded itself and still reported success. That optional validator was removed outright rather than vendored, because verify-package.py already performs the authoritative in-repo package inventory.

Fixing that exposed a second silent pass underneath it. The scan for secrets used `rg`, wrapped in a shell conditional.

On a host without ripgrep, `rg` never runs at all; the shell returns exit 127 for the command it could not find. Inside an `if`, both "pattern not found" (exit 1) and "command not found" (exit 127) read as false. The conditional does not distinguish. The scan could never fail.

```bash
# Before: the trap. rg may not exist, and the path resolves
# against whatever directory the caller happens to be in.
if rg -n 'approval_token|private_key|BEGIN [A-Z ]+ KEY' plugins/mission-control-operator/assets; then
  exit 1
fi
```

The same shape appeared in five sibling scripts. The fix switched to `grep -rEn`. The `-r` is not decoration: `rg` recurses by default and `grep` does not, so a naive swap would have silently narrowed the scan to nothing, which is the same defect wearing the fix's clothes. This is line 10 of run-jrig-qualification-proof.sh, reflowed here for readability:

```bash
# After: the fix
if grep -rEn 'approval_token|private_key|BEGIN [A-Z ]+ KEY' \
  "$ROOT/plugins/mission-control-operator/.codex-plugin" \
  "$ROOT/plugins/mission-control-operator/skills" \
  "$ROOT/plugins/mission-control-operator/assets"; then
  echo "authority/secret field in package" >&2
  exit 1
fi
```

The assertion is now rooted at `$ROOT` instead of the caller's cwd. The plant-and-verify drill is what actually proved the fix: plant an `x_private_key` file in the assets directory, watch the scan fire and the script refuse, remove it, watch the proof return to PASS. That drill is the transferable artifact here, more than the `grep` swap. It is the difference between believing a guard works and having watched it work. Commit 3cd7063b applied the same fix across five sibling scripts at once.

## Gate 3: the frozen clock

The B6.1/B6.2/B6.3 proofs ran project discovery against the live registry with a hardcoded `--now` of 2026-08-16T12:30:00Z. Both projectors correctly failed when a record's `collected_at` was later than `--now`, and every scheduler refresh stamps `collected_at` with real wall-clock time, permanently in the future of that frozen clock.

Result: validate:authorized-work-discovery was guaranteed to fail every future automation PR. PR #526, the first repository-refresh PR to arrive after the frozen clock fell behind, hit it.

This one inverted the usual defect class. Gates 1 and 2 could never go red. Gate 3 could never go green.

The fix chose fixtures over unpinning the clock. Why not the obvious fix, unpinning `--now`? Because other fixtures in that suite depend on the frozen time for expiry semantics; unpinning would trade one broken proof for several. Instead the proof now reads a fixture-local registry (ops/agent-headquarters/fixtures/registry/, the two referenced records, schema-validated, collected_at pinned to the fixture clock), the live-registry denied-loud posture case stayed unchanged, and a new teeth case proves a future-collected registry still denies with REPOSITORY_REGISTRY_STALE. The staleness rule keeps its bite, and the proof no longer measures the wall clock.

## Gate 4: the auditor that could edit its own record

claude-code-plugins PR #1185 shipped two repo-local agents, claim-verifier and beads-warden. This repo ships 347 agents as product and ran exactly one internally (.claude/agents/skill-auditor.md). Both new agents exist because this estate produced failures they are designed to catch, not hypotheticals. This gate belongs in the set for a different reason than the first three: its defect was not a missing red path but an auditor that could rewrite the evidence its verdict rests on, which decouples the verdict from the record just as surely.

claim-verifier answered six false claims shipped in a single day: a denied build-time consumer that existed, a fabricated "hash-pinned" enforcement claim, an undercounted page set, a closure whose title promised 3x what it delivered, an "all agents A-grade" claim contradicted by 253 measured errors, and a scanner's clean run cited as containment proof for a class it structurally cannot detect. That last one is the same defect as Gates 1 and 2: a clean scan is only evidence if the scan could have come back dirty. A tool you have never seen fail cannot be trusted to succeed.

The verification honesty matters here. validate-skills-schema.py --agents-only reports 253 errors, identical to the recorded corpus baseline, and neither new agent appears in the error list. They proved they added zero errors rather than claiming the corpus was clean.

The beads-warden claimed a read-only record-integrity role. The Greptile review caught the open paths:

> beads-warden's denylist only blocked close/push verbs, leaving bd update/create/defer/import/export and git add/commit/reset as open mutation paths. The auditor could alter the record it audits.

The fix expanded disallowedTools to every state-mutating bd, bd-sync, and git verb, while keeping read verbs open-ended. Read-only agents do not fix what they find. They break the self-certification loop.

beads-warden gave up ownership of the dependency graph, not because it could not track it, but because a second owner of one fact is the competing-authority anti-pattern this program exists to remove. It kept Dolt commit history as its unique contribution, because that is the only place a dropped write is visible: the JSONL export shows the state that exists, never the write that silently vanished.

claim-verifier's negative-existence instruction also had an open path. It told the verifier to stage an untracked probe with no restoration step, contaminating the caller's index. The fix replaced it with `git grep --untracked` / `rg`, which needs no index mutation at all. Same theme as the masking function: the tool changed what it measured.

## The control: the gate that worked

A scorecard drift gate correctly failed when a branch predated a moving corpus. Merged current main, regenerated via `node scripts/measure-epic-1.mjs`, and the gate cleared. A gate that fires on a legitimate rebase against a moving corpus is a gate with a reachable red path. This one distinguished itself.

## The collaboration beat

Three of the four defects were found by an adversarial reader, not by the author. The count-cohort fail-open came from an independent reviewer subagent in detached read-only mode. The rg silent-pass came from a MiniMax defect-lane review, then from verifying the finding rather than relaying it. The beads-warden open paths came from two Greptile P1s flagging mutation vectors the design had missed. The fourth, the frozen clock, announced itself the only way a gate with no reachable green path can: as a real CI failure, on PR #526.

The sessions involved Claude Opus 5, Claude Sonnet 5, Claude Fable 5, and GPT-5.6 Sol. The claude-code-plugins Epic work ran under GPT-5.6 Sol and Claude Fable 5. Real failure arcs filled the transcripts: `fatal: refusing to merge unrelated histories`, `fatal: git-write-tree: error building trees` hit twice, `fatal: 'feat/internal-governance-agents' is already used by worktree at /tmp/claude-1000/...`, two sessions killed at exit code 143, and a review lane catching a real NameError in the intent-os work before merge (`_attempt_errors` references undefined `identity`). A day with 30 merged PRs still spent real time on worktree and index plumbing.

One human course-correction, verbatim: "Please prioritize returning the schema contract now; if tests are still running, stop after bounded implementation and report." Bounding an agent mid-run matters: an unbounded agent will keep spending on the current path rather than return the artifact you actually need.

One operational interruption is worth recording because it set the day's conditions: the box hit 100 percent disk full mid-epic. The GPT-5.6 Sol session paused Epic 1, reclaimed 46 GiB (206 inactive node_modules trees removed, /dev/shm from 11 GiB to 928 MiB), put back 4,398 generated files that eight older repos turned out to still track (deleting a tracked artifact is not cleanup, it is a pending revert), and resumed the epic.

## Also shipped

claude-code-plugins docs-governance chain merged 30 PRs across two epics. Fail-closed Cowork manifest drift, seven consecutive count-contract governance slices, document lifecycle enforcement, external stats freshness bounds with declared max_age_hours, SOPS migration of local MCP credentials, sops-env hardening to stop shell-evaluating decrypted values, live documented-number corrections, ci-required contract pinning, root README rebuild as a governed landing contract, capability vocabulary publication with full corpus coverage, model-id classifier promotion with committed exclusion list, and Kobiton fork deletion with adapter toolchain replacement. Epic 1 and Epic 2 closure AARs filed.

intent-os delivered the mission-control founder portfolio executive view composed from governed projections, a decision record on the B7 cockpit pattern, high-severity transitive dev dependency patches, and B6 epic settlement completion with evidence.

bobs-big-brain-compiler 1.23.0 shipped explicit unmetered mode, model ceiling enforcement, resume checkpoints bound to source hash, and compilation restricted to current source versions. The thematic echo: a checkpoint decoupled from source state is the same defect class as the gates above.

bobs-big-brain-umbrella separated compile and brain writer locks to prevent self-deadlock, replaced retired Tailscale login paths in identity docs. bobs-big-brain-plugin added non-Google Tailscale invite support in onboarding.

A teamkb-compile run over 2026-08-17: the governed brain at 17,530 memories (10,337 active), 16 candidates distilled and governed with search-before-save.

## What transfers

The drill generalizes to any guard, and it costs minutes:

1. Plant the thing the gate exists to catch. A fake secret, a crafted bypass payload, a stale record. Watch the gate go red. If you cannot make it go red, you do not have a gate.
2. Remove the plant. Watch it go green again. Now both directions are proven, not assumed.
3. Check what happens when the gate's own tooling is missing. Exit 127 inside an `if` is invisible. A guard that depends on a binary must fail loudly when the binary is absent, not report a clean scan.
4. Check what the gate's verdict is coupled to. A frozen clock against live data, a resume checkpoint that ignores source changes, an auditor that can edit its own record: each is a verdict decoupled from the thing it claims to measure.

Four gates failed this drill on one day across two repositories. None of them had ever been seen red for the right reason. That was the tell.

## Related posts

[Seventeen Spellings of the Same Number](https://startaitools.com/posts/seventeen-spellings-of-the-same-number/) (2026-08-17): The count-provenance checker this post's Gate 1 punctures, including the masking fix that turned out to be incomplete.

[Every Safety Gate Has a Failure Direction](https://startaitools.com/posts/every-safety-gate-has-a-failure-direction/) (2026-07-06): The same swallowed-error root cause, one gate failing closed and one failing open.

[Exit Zero Can Lie; Stdout Holds the Answer](https://startaitools.com/posts/the-failure-that-knew-its-own-name/) (2026-08-16): An exit status that vouched for a run the output contradicted.
