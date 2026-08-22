---
title: "What a Skipped Check Is Worth in CI"
description: "A gate runner that counts SKIP as pass prints green for work that never ran. How a rig proof receipt closes that gap, and why filters must invert."
date: "2026-08-21"
tags: ["ci-cd", "security", "testing", "devops", "qml"]
featured: false
canonical: "https://startaitools.com/posts/the-skip-that-counted-as-a-pass/"
---
A gate runner has three verdicts and only two of them are honest. PASS means the check ran and the code was fine. BLOCK means the check ran and the code was not. SKIP means nothing ran at all, and if your aggregator folds SKIP into the pass column, the summary line at the bottom of the run is not reporting on your code. It is reporting on your tooling install.

That is what `gate-runner omarchy-submit` was doing in `contributing-clanker`. Two of the gates in the lane call `gate_skip` when their binary is not resolvable:

- `c32` shells out to `omarchy-plugin-validate`
- `c33` shells out to `qmllint`

Both of those binaries live on the Omarchy rig. Neither exists on a dev box, and a dev box is where the lane actually runs. So the runner walked the whole set, hit two unresolvable binaries, skipped them, counted the skips as passes, and printed **verdict PASS, 0 BLOCK** for plugins that had never run on Omarchy at all.

They were being validated by hand every time instead. Which is exactly the "if someone remembers" failure the lane exists to end.

An undesigned skip that greens the aggregate is worse than no gate, because it manufactures confidence.

Seven repos vendor a copy of this lane (`omarchy-x-files-entry`, `omarchy-listening-post-entry`, `omarchy-docket-entry`, `omarchy-mlb-booth-entry`, `omarchy-crew-chief-entry`, `omarchy-pit-wall-entry`, and `omarchy-widget-template`), so the fix had to be one that copies cleanly. About fifty commits landed across twelve repos on the day, and the plugin repos took between one and eight each.

## Why the gate cannot just do the check

The obvious move is to make `c32` and `c33` reach the rig themselves. Run the container, run the validator, report what it says. No skip, no receipt, no new file format.

The runner enforces a ten second wall clock per gate. A rig round trip does not fit in ten seconds, and raising the ceiling to fit it would mean every gate in the lane now waits on the slowest possible one. Gates that finish in fifty milliseconds would start sharing a budget with a container boot.

So the check moves off the gate and the gate checks the evidence instead. The rig run happens once, deliberately, through `scripts/rig-verify.sh`, and it leaves a receipt at `.rig-proof.json`. The new gate `c37` reads the receipt.

## What the receipt has to prove

A receipt is only worth what it is coupled to. Four properties, each with a reason it exists.

**It fingerprints the manifest and every `.qml` file.** Those are precisely what the rig validates. Fingerprinting them means the receipt cannot certify code nobody ran. Change a file, the fingerprint moves, the receipt stops matching.

**It records failures rather than omitting them.** If the rig run fails, that goes in the receipt as a failure. A receipt that only ever recorded successes would make "the rig said no" and "the rig was never asked" the same observable state, which is the original bug wearing a different hat.

**It expires after fourteen days.** The rig tracks upstream Omarchy. A proof from six weeks ago is a proof about a platform that has since moved.

**It blocks only at submit time.** Gating every intermediate save on a rig round trip would teach people to work around the lane, and a lane people route around is not a lane.

Verification, end to end against a real plugin entry: the lane BLOCKED with no receipt present, `scripts/rig-verify.sh` produced one from an actual run inside the `omarchy-rig` container, the lane then PASSED at eleven gates (the count before `c38` landed later the same day), and editing a single `.qml` file flipped it straight back to BLOCK.

## Widening the fingerprint the same day

The first version of `c37` fingerprinted the manifest and the QML. That scope was chosen to match what the rig's two tools read, and that was the wrong reason to choose it.

The receipt does not claim "those two tools were happy." It claims **this code was proven to run.** These plugins keep their parsing, host filtering, and state handling in a `Model.js` that QML imports at load. Under the original scope, that entire file could change and the receipt would still match.

Proven concretely: after the SSRF fix landed in Listening Post's `Model.js`, `c37` still returned PASS. The receipt was certifying a tree whose whole behaviour had changed underneath it.

So the fingerprint now covers every shipped `.js` too, including extension-less executables that previously sat below a `maxdepth` of 2. The choice was widening the existing fingerprint function rather than adding a second receipt field, because this function and the one inside `rig-verify.sh` have to agree byte for byte, and a single definition is the only way that stays true over time.

The widened `c37` BLOCKs the fixed Listening Post tree until `rig-verify.sh` is re-run, and PASSes after. The coupling holds in both directions, which is the only version of that test worth running.

## The clipped Text nobody could see

Separate gate, same week, and it explains why "the tools are happy" is a weak claim.

A QML `Text` element with no `width`, no `elide`, and no `wrapMode` lays out on a single line and gets clipped by whatever container holds it. The last words simply vanish.

```qml
// lays out on one line, container clips it, tail is gone
Text {
    text: "The spend meter is your friend"
}
```

`qmllint` reports zero errors on that. Clipping is valid QML.

I caught this three times by eye and never once by a test. The four plugin entries that existed at the time carry 240 offline tests between them and not one of them exercises a `.qml` file. It reached a published marketplace `preview.png` whose footer reads `The spend meter is y`. Root cause was the widget template's own list row, so it is one defect copied into all four of them.

`c36` is the detector. The interesting part is not that it exists, it is how it decides.

## The rhyme: enumerating bad forms is the failure mode

`c36` shipped twice. The first version enumerated the shapes it knew about and missed the plain form:

```qml
text: someProperty
```

That is how an attacker-controlled GitHub author login reached a row with no width bound on it. The pattern list did not have that pattern.

The second version stops matching shapes. It strips string literals and asks whether any identifier remains. If something computed is going into `text`, the element needs a width constraint and an overflow rule, full stop.

```python
# `value` is the right hand side of `text:`, captured, not the whole line.
# Strip the string literals out of it and see whether an identifier survives.
residue = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', "", value)
residue = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", "", residue)
bound = bool(re.search(r"[A-Za-z_]\w*", residue))
```

A pure literal leaves an empty residue and is not flagged as computed. Anything
with a surviving identifier is computed, so its length is not authored, so it
needs a bound. There is a second shape underneath it for the case the first one
does not cover: a string literal long enough to overrun a bar panel on its own,
which the gate puts at more than 40 characters.

Now hold that next to `c38`, which landed the same day on a completely different problem.

Listening Post guarded a `curl` call with a host filter:

```javascript
// four decimal parts, and nothing else
if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) { reject(host) }
```

curl does not resolve addresses that way. It resolves via `inet_aton`, which accepts one to four parts, reads a leading `0` as octal and a leading `0x` as hex. So `127.1`, `0177.0.0.1` and `0x7f.1` all sail past a filter that only knows one spelling of loopback, and all three reach loopback. That SSRF escaped human review twice on marketplace submission 1229.

`c38` flags that regex shape in any file that also reaches the network. Its fix hint teaches the inversion, which is to allowlist the canonical form, rather than naming three more bad patterns, because enumerating bad forms is precisely what failed twice.

Verified: `c38` BLOCKs the pre-fix Listening Post tree at `Model.js:257`, the exact line the maintainer cited, and PASSes the fixed tree.

Two detectors, two different domains, same failure and same fix. Both broke the first time by listing the bad forms they had seen. Both got fixed by inverting to a structural rule about what a correct form has to contain.

That is a denylist losing to an allowlist, which is not a new idea. What is worth noting is that neither of these started life looking like a security control. One was a layout rule and one was a host filter, and the denylist shape got in through the side door both times, because listing the bad cases you have already seen is simply the obvious way to write a check. The enumeration is the bug, and it does not announce itself as one.

`c36` got tightened later the same day for a related reason. The original rule accepted "a width constraint OR an `elide`", and `elide` without a `width` is a no-op in QML, so half the accepted forms did nothing. It now requires a width constraint AND an overflow rule. Blast radius was measured on a scratch copy before applying it: those same four entries and the template still pass.

## A detector living inside the tree it scans

Candidate repos vendor the lane. That puts the detectors physically inside the tree they are scanning, and a detector's source necessarily contains examples of the pattern it hunts.

So `c34` flagged its own shell-injection example and failed a CI run on a repo whose plugin code was clean.

The fix is one exclusion in the shared `gate_tree_files` helper (gates no longer scan `scripts/gates/**`) rather than a patch inside each gate. One exclusion in the shared enumerator covers every gate added later. Patching them one at a time would have covered exactly the gates that existed that afternoon.

## The chokepoint that was not one

`precheck-hook.sh` intercepts `gh` commands before they run. It covered four of them: issue comment, pr create, pr ready, pr merge.

A marketplace submission is filed with `gh issue create`.

So the one command that actually submits a plugin to the marketplace bypassed the chokepoint entirely, and running the gate lane before submitting was a choice rather than a gate. That was the last "if someone remembers" step in the chain.

The new guard requires **both** a lane run and `c37`'s rig receipt, because per the whole first half of this post, a lane run on its own is not evidence. It resolves the plugin tree from the issue body's `### Repository URL` line, maps the repo name to `~/000-projects/<name>`, runs that repo's vendored `run-plugin-gates.sh`, then runs `c37` from the canonical lane, because `c37` is not vendored into any plugin repo.

Posture matches the hook's existing unmatched-candidate path: fail OPEN while the tree is unidentified (warn and allow), fail CLOSED once it is identified. You cannot block on a check you were unable to aim.

Extending this hook beat adding a second one. Two chokepoints on a single action drift apart, and this hook already owns the log and the kill switch.

Two incidental bugs surfaced while testing it, both the same root cause and both worth knowing. A bracket expression written inline in a `[[ =~ ]]` test takes an escaped octal like `\047` literally instead of as a quote character, which silently excluded digits from body-file paths. `grep -oE` has the identical problem with the identical expression. Same shape of bug, two tools, one afternoon.

## The vendored copy that was intact but stale

`run-plugin-gates.sh` runs a manifest check that proves a vendored copy is intact. It cannot prove canonical has not moved on. Which is exactly the gap that let a stale `c36` sit here reporting green.

`scripts/check-lane-freshness.sh` plus a CI step now fetches canonical and compares hashes. It is wired **advisory** (`continue-on-error`), not blocking, because it needs network and a GitHub blip must not fail an unrelated PR.

That is one more case where the stricter option is the worse one. Blocking would be stricter and would be worse: a check that cries wolf is one people learn to ignore, which is how the original drift survived in the first place.

## Where the lane sits now

Canonical lane full suite: **71 passed, 0 failed.** PR #73 merged, five files, +356/-3. Lane green on four of six plugin repos at the time of the `c38` commit; the two findings in crew-chief and pit-wall were pre-existing and reported separately.

What actually changed is narrower than the commit count suggests. The lane can now tell the difference between "checked and fine" and "could not check," it can prove the rig ran against the exact bytes being submitted, its two filter-shaped detectors ask structural questions instead of matching known-bad spellings, and the submission command is finally inside the chokepoint. Claude Opus 5 carried most of the implementation across the day.

Also shipped: `claude-code-plugins` dual-published a blog post to tonsofskills.com/blog and merged PR #1295 adding two internal Omarchy plugin agents; `omarchy-mlb-booth-entry` and `omarchy-docket-entry` moved API credentials to stdin for `jq` and `curl` instead of argv; `omarchy-x-files-entry` corrected a stale test count and some deleted-CLI references in docs; `comehomealabama` and `intent-solutions-landing` each took one content commit.

## Related Posts

- [The Gate That Could Not Fail](https://startaitools.com/posts/the-gate-that-could-not-fail/)
- [We Told the Auditors to Refute Us](https://startaitools.com/posts/we-told-the-auditors-to-refute-us/)
- [The Refusal Nobody Heard](https://startaitools.com/posts/the-refusal-nobody-heard/)
