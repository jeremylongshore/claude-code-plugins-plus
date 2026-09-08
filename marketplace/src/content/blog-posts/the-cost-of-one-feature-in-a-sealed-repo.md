---
title: "Hash-Sealed Evidence: One Feature, 19,461 Lines Rebuilt"
description: "Sealed evidence expires when content changes. Adding a feature to omaTrail rewrote 19,461 lines of its balance report before shipping."
date: "2026-09-07"
tags: ["release-engineering", "testing", "architecture", "ci-cd", "automation"]
featured: false
canonical: "https://startaitools.com/posts/the-cost-of-one-feature-in-a-sealed-repo/"
---
omaTrail is an Oregon Trail inspired game plugin headed for the Omarchy marketplace. On 2026-09-07 it took 38 commits. Two of them were features. The other 36 were evidence, seals, and tests, and the full seal cycle ran three separate times.

That ratio is not waste. It is what the repo charges for a change.

## The feature

The second feature of the day landed at 18:50: a stateful dysentery event. Here is the load-bearing part of it.

```javascript
function ailmentTravelPenalty(state, member) {
  if (!member || member.ailment !== "dysentery") return 0
  var penalty = state.pace === "grueling" ? 7 : state.pace === "strenuous" ? 4 : 2
  penalty += state.rations === "bare" ? 6 : state.rations === "meager" ? 3 : 0
  if (["snow", "cold", "storm", "hot"].indexOf(state.weather) >= 0) penalty += 2
  if (state.inventory.food <= 0) penalty += 6
  if (state.difficulty === "easy") penalty -= 1
  if (state.difficulty === "hard") penalty += 1
  if (state.occupation === "doctor") penalty -= 2
  return Math.max(1, penalty) * (state.rulesProfile === "classic-1978" ? 2 : 1)
}
```

Fifty-nine lines changed in `JourneyRules.js`. The commit added one `EVENTS` entry carrying `ailment: "dysentery"` and `source: "fictional-composite"`, gave every party member an `ailment` field, wired the penalty into `applyPartyTravel`, and changed `updateMemberCondition` so a death records the ailment as its reason instead of the generic string "illness and exhaustion". It also extended the weights table in `chooseEvent` to cover both rules profiles, having previously covered only `classic-1978`. Sixty-two new lines went into `tests/journey.suite.js`, and a later commit added 69 more to harden mutation coverage.

## What those 59 lines expired

Every claim in this repo is sealed to a content hash. Change the content and the seal is not wrong, it is void. Three artifacts had to be rebuilt before the feature counted.

**The balance report.** `reports/balance/balance-100000.json` is 100,000 simulated runs across 480 matrix cells, seeded by `Math.imul(runIndex + 1, 0x9e3779b1) >>> 0 || 1`. The dysentery commit rewrote 19,461 lines of it. After the rerun: 55,256 victories against 44,744 losses, mean run 242.8 days, mean 1.46 deaths.

The split by rules profile is the interesting number. The `omatrail` profile won 17,670 of its 50,000 runs with a mean of 2.90 deaths. The `classic-1978` profile won 37,586 of its 50,000 with a mean of 0.032 deaths. The retro profile is the doubled-penalty one, per the last line of the function above, and it is still the profile that almost nobody dies in. A difficulty label is a guess until the simulation disagrees with it.

**The provenance scan.** `reports/provenance/oregon78-similarity.json` compares the candidate against the actual 1978 Oregon Trail source, pinned at `github.com/TedThompson/OREGON78` commit `38959e87`, file `OREGON78.RC.abas`. Method is exact normalized expression comparison across four-word prose n-grams, twelve-token code n-grams, and thirty-character exact lines. Adding dysentery moved the candidate sha256 from `c097b5a4...` to `43749aa0...` and its string-literal count from 1,467 to 1,505.

All four sharing sets came back empty again, and getting that answer a second time is the point of rerunning it. "This is not a copy" is a claim about specific bytes, and the bytes had just changed.

**The render matrix.** Twenty cells under `evidence/render-matrix/`, being two rules profiles by two color modes by five scenes (trail, hunt, river, event, ending). Each cell is a PNG, a `.render-proof.json`, and a `.shell.log`. The full matrix was captured twice on this day. The `.harness-hash` manifest took the difference: 62 changed lines in one commit, 84 in another.

## The flaky harness underneath it

Between 11:35 and 11:40 five commits went into the install-lifecycle tests, all of them the same bug: the shell plugin catalog was being read before it settled. Wait for the catalog after a rescan. Normalize the empty-catalog case. Actually report lifecycle assertion failures instead of swallowing them. Wait for a removed plugin to leave the catalog.

Asserting on a snapshot of state that is still moving produces a test that fails on timing and passes on luck. Waiting on the state fixes it. This matters more than usual here, because the same harness produces the evidence the seals are computed over.

`contributing-clanker` got the matching fix on the other side of that boundary: one commit to make C41 evidence scans deterministic. A scan that returns different output for identical input is a seal that cannot mean the same thing twice, which makes the whole hash chain decorative.

## Also shipped

`coastal-realty-ops` released v0.13.1 and filed an agentic parcel-feasibility assessment against live-verified sources: USGS elevation, FEMA, FWS, the NRCS soil survey, and Baldwin County parcels. Eight real issues came out of the IntentCAD review, and one finding got retracted after it turned out a stale local checkout, not `main`, was what looked broken.

`intent-os` chased down borg repository growth and found two causes, both excludes rather than compaction. The nightly TeamKB encrypted tarball (283 MB, never deduplicates, already restore-tested and pushed offsite) was sitting inside the backup repos on both boxes, so the backups were backing up a backup. Separately, 90 unpruned tonsofskills releases at 27.9 GB were the largest single source of growth on the VPS. Seventy-eight were pruned.

The nightly `/teamkb-compile` pass ran against the governed brain, now at 17,813 memories with 10,620 active. It distilled 23 candidates, ran 23 search-before-save queries, found 3 already covered, and captured the remaining 20.

`intent-solutions-landing` shipped v3.0.3 and reworked the site to read as the network gateway. `omarchy` recorded the omaTrail Classic candidate evidence.

## How the day ran across models

Four models did the work: Claude Opus 5, Claude Fable 5 1, Claude Sonnet 5, and GPT-5.6 Sol. The `intent-os` thread was the heaviest by a wide margin at 6 sessions, 112 turns, 555 tool calls, and 21 errors, split between Claude Fable 5 1 and Claude Opus 5. A Claude Fable 5 usage limit hit at 19:32 and the work continued on Claude Opus 5 after a model switch, which is now a routine enough event that it barely registers as an interruption. The `claude-code-plugins` and `intent-eval-platform` threads ran on GPT-5.6 Sol through Codex, 289 turns over 322 minutes and 100 turns over 403 minutes respectively.

Two errors from the log are worth keeping. The first is `AssertionError: expected 'HTTP 401 Authorization: Bearer sk-ant…' not to contain 'LEAKEDKEYVALUE'`, which is a secret-redaction test doing exactly its job in a place where a silent pass would have been expensive. The second is `fatal: 'main' is already used by worktree at '/home/jeremy/005-waygate-mcp/.git/beads-worktrees/main'`, which is the ordinary tax on running several agents against one checkout.

## What it costs

Thirty-six commits to ship two features, and none of the thirty-six were optional. Each one is deterministic and rerunnable, which is the property that makes the seal worth anything.

The tradeoff is legible. A feature is cheap to write and expensive to prove. On a repo where the marketplace listing rests on a provenance claim against a 1978 original, that is the correct direction to be wrong in. On a repo where nobody is asking, it would be theater.

## Related Posts

- [Every Claim Needs a Shipped Source and an Executable Proof](https://startaitools.com/posts/working-is-not-proven/)
- [A Ratchet Is Only as Strong as Its Re-Baseline Rule](https://startaitools.com/posts/the-ratchet-that-needed-a-ratchet/)
- [Verified Plugins Program: Building a Quality Signal for the Marketplace](https://startaitools.com/posts/verified-plugins-program-quality-signal-for-the-marketplace/)
