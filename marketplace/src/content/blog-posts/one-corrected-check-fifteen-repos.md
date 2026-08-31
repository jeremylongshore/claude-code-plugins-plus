---
title: "One Corrected Check, Fifteen Repos"
description: "Correcting a gate is cheap. Propagating it through fifteen repos on a vendored, hash-pinned lane is the part that costs a day."
date: "2026-08-30"
tags: ["ci-cd", "quality-gates", "governance", "testing", "devops", "automation"]
featured: false
canonical: "https://startaitools.com/posts/one-corrected-check-fifteen-repos/"
---
Two gates failed the same way on 2026-08-30, in systems that share no code.

The first checked whether a set of run fields were non-null. A recorded discovery run could therefore declare 3,000 skills while carrying 19 rows, and the boundary would pass it, because 3,000 is not null and 19 is not null. Runs 6 through 11 all disagreed with their own row counts. Run 11 declared 3,069 against 3,678 actual rows.

The second checked whether a marketplace submission description was exactly 500 characters. Which 500 characters was never asked. So 500 characters of filler passed, and 500 characters of filler is precisely the submission the gate was written to stop.

A check measuring a proxy instead of the property is the house failure mode on this blog and has been for months. I am not going to pretend it was a discovery. What was actually expensive on this day was not diagnosing either gate. It was pushing one corrected gate through fifteen repos that carry it as a vendored, hash-pinned copy rather than importing it. That half is the post.

## The evidence boundary that could not see its own run

Epic 5, "Coherent Freshie Evidence," closed in `claude-code-plugins` that day. The closure AAR is `000-docs/809-AA-AACR-epic-5-closure.md`, 134 lines, filed against epic bead `claude-h05s`.

The AAR states the defect in one line: "The old boundary checked whether required run fields were non-null, not whether the header and its rows described the same run." The run-6 shape is the image that sticks. Three thousand declared skills, nineteen rows, green.

Five invariants replaced it:

1. `gate_run_completeness()` compares the run header against same-run rows before any export work begins.
2. The grade histogram, CSV row count, CSV hash, run tag, and immutable Dolt commit must identify one export, not adjacent runs that happen to be close.
3. Behavioral-evaluation identity is `jrig_run_id`, held separate from discovery-run identity.
4. Evidence class and retention are validity conditions, not annotations. Three legacy proofs are now honestly classified E0. No public verified projection remains.
5. Blocking CI installs a pinned Dolt binary immediately before an exact guarded runner, which must execute one real hermetic cycle with zero skips against scratch SQLite, Dolt, and filesystem state, then prove live-server refusal.

Nine commits landed that sequence, and read as a run they are a reviewer finding bypasses faster than they could be closed:

```text
make exit evidence fail closed
reject skipped and overwritten proofs
close generator and overwrite bypasses
require executed hermetic proof
bind proof method and install order
verify guarded cycle invocation
bind receipts and harden hermetic proof
publish reproducible run 14 receipts
enforce graded corpus parity
```

The independent boundary review returned PASS only "after reproducing and closing skipped tests, generator no-op, lifecycle replacement, aliased mutation, and post-verification binary-overwrite attacks." Five attacks. Each one maps onto a commit in that list. `reject skipped and overwritten proofs` is the skipped-test attack. `close generator and overwrite bypasses` is the generator no-op. `bind proof method and install order` is what stops the binary being swapped after verification. The commit log is not a changelog here, it is an attack transcript with the reviewer's half missing.

The first commit alone touched 8 files for +1515/-256, including `run-delta.py` at +247/-50, `measure-epic-1-scorecard.mjs` at +382, and four test files. All nine commit bodies were empty, which is worth one dry line: the sequence that produced the most legible story of the day carried no explanation with it at all.

Final receipts. Run 14 declared 3,053 against 3,053 rows, delta 0. 3,630 compliance rows against 3,630 grade rows with matching SHA-256. Run 14 is bound to immutable Dolt commit `2ljhn79ge74uj1kd7q2chqgo9ne0tulb`, grade CSV SHA-256 `72fbb289e8451d9a4bbe95cae0b9a1797588c0197589f94ddd1cde48241e4ef0`, histogram A 1,872 / B 1,117 / C 479 / D 157 / F 5. `pnpm run measure:e1:check` passed 39 measurement tests and the tracked artifact matched its exact regeneration from the Git index. PR #1387 merged as `78e3580c` after 34 reporting checks with zero failures.

The AAR's own first lesson is the one to keep:

> A green test command is not proof that the governed body ran. Exact test count, zero skips, and a guarded method invocation are part of the boundary now.

Its second lesson is quieter and I think better: "Zero E2/E3 claims is a safe state, not a 100% retention measurement." The scorecard now reports `retention_percent` as `null`. A tool with nothing to measure says nothing rather than reporting a flattering 100%.

## Five hundred characters of anything

The second gate is `scripts/gates/c43-omarchy-marketplace-presentation.sh`, which guards marketplace submission copy across the Omarchy widget fleet. Here is what it checked:

```bash
if [[ "$HAS_BAR_WIDGET" == "true" && "$BAR_DESC_LENGTH" != "500" ]]; then
  FINDINGS+=("barWidget description uses $BAR_DESC_LENGTH/500 characters")
fi
```

Length equality, and nothing else. A submission had to fill its allowance exactly, and filling an allowance is trivially satisfied by padding.

The comment written above the replacement checks is the whole day in five lines:

> Length alone is not copy quality. A submission description must identify the product, explain what the user can see or do, and state a meaningful trust boundary. These checks deliberately reject generic 500-character filler while repo-specific contract tests pin the precise claims each plugin is allowed to make.

The new checks run as an embedded `python3` heredoc inside the bash gate, each one appending to a findings list rather than exiting early, so a bad description gets told everything wrong with it at once. Four of them, excerpted:

```python
sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", description) if part.strip()]
if len(sentences) < 4:
    findings.append("description needs at least four readable sentences")
if sentences and len(sentences[0]) < 50:
    findings.append("opening sentence is too thin to establish the user outcome")

surface_terms = ("bar", "panel", "pill", "widget")
if not any(re.search(rf"\b{term}\b", lower) for term in surface_terms):
    findings.append("description never explains the visible bar, panel, pill, or widget")
```

Two more term lists do the load-bearing work. An interaction list (`open`, `click`, `select`, `copy`, `install`, `focus`, `refresh`, `preview`, `sort`, `scan`, and about a dozen more) fails a description that "gives no concrete user interaction or visible behavior." A boundary list (`no `, `never `, `only `, `without `, `offline`, `local`, `private`, `fixed `) fails one that "gives no privacy, network, data, or write boundary." A description can be four fluent sentences about nothing and still fail both.

Then there is a banned-phrase list inside the gate, nine entries: `cutting-edge`, `game-changer`, `game-changing`, `revolutionary`, `supercharge`, `seamless`, `robust solution`, `unlock your`, `take your productivity to the next level`. I run the same instrument against this blog's prose from a JSON deny-list, and the overlap is not coincidence. Both lists exist because the same generator produces both kinds of copy.

Plus one cross-field check with the best failure message in the set: `manifest and barWidget descriptions tell different product stories`, which fires when the two description fields disagree about what the thing is.

None of that is clever, and it is worth being honest about what it does not do. A length check and a shape check are the same class of instrument, and a determined author can pad four sentences as easily as one. The gate is not proving quality. It raises the floor from "any 500 bytes" to "500 bytes that name the product, show a visible surface, describe an interaction, and state a boundary," and its own comment says where the real work goes: repo-specific contract tests pin the precise claims each plugin is allowed to make.

## The part that actually cost the day

Downstream repos do not import this gate. Each one carries a vendored copy. The lane is declared at `scripts/gates/.lane-manifest`, whose header reads:

```text
# Vendored gate lane. Regenerate with scripts/sync-gate-lane.sh, never hand-edit.
# canonical: contributing-clanker@359a27cde21e60086f95a3ddee99c8920a3d7ca2
```

That header is quoted with its dash normalized to a comma, because the real file uses an em dash and this blog's own lint gate would quarantine the post for reproducing it.

Below the header sit per-file SHA-256 hashes of every gate script. Alongside it, each repo carries `.harness-hash` covering the wider audited surface: `contract.test.js`, `run-plugin-gates.sh`, `stryker.config.json`, `tests/RTM.md`, `tests/TESTING.md`, and the rest.

So the corrected conditional is not a one-line edit. The canonical pin moved from `contributing-clanker@359a27cd` to `@81239c6e`, and in every consuming repo four hashes had to move together:

- the lane manifest hash, in `.lane-manifest`
- the `c43` gate hash, in both `.lane-manifest` and `.harness-hash`
- `run-plugin-gates.sh`, because the gate list it dispatches changed
- `contract.test.js`, because the per-repo contract test that pins the allowed claims changed with the copy

The third and fourth entries are the ones that make this expensive. The gate file itself is one hash. But correcting the gate changed which checks run, so the runner's hash moved, and tightening the copy to satisfy the gate changed each repo's contract test, so that hash moved too. One upstream edit fans out into four hashes per repo, and any repo where they drift fails its own harness verification before it fails the gate. That is the design working, and it is also the bill.

Here is the shape of a single downstream repo's day, using `omarchy-listening-post-entry`, which took four commits:

```text
fix: complete Listening Post marketplace copy
test: pin Listening Post marketplace story
test: enforce marketplace presentation quality
chore: repin audit harness artifacts
```

Read that in order and it is the whole propagation protocol in four steps. Rewrite the copy so the new gate passes. Pin the specific claims this plugin is allowed to make, in its own contract test. Take the corrected gate from the lane. Re-pin the harness hashes so the repo verifies against its new self. Every repo ran some subset of exactly that. The spread runs from four commits down to one: `omarchy-foundry-entry` took a single `test:` commit and no copy commit at all, which is what it looks like when only the gate underneath a repo moves.

Fifteen entry repos took the change: bazaar, capture-conveyor, crew-chief, desk-transition, docket, flow-boundary, foundry, listening-post, loose-ends, mlb-booth, pit-wall, quiet-queue, wait-state, workspace-storyboard, x-files. Twelve of them needed a `fix: complete <Name> marketplace copy`. The other three, desk-transition, foundry, and wait-state, needed only the proof and the re-pin. Counting the template and the canonical lane source itself, the fan-out ran to 48 commits across 17 repos. The whole day, including the freshie epic, came to 112 commits across 19 repos.

The tradeoff is deliberate and I would still take it. Vendoring plus hash pinning means a downstream repo cannot silently run a gate that differs from canonical, and cannot quietly weaken one either. What it buys in tamper-evidence it charges in propagation, and the charge is not proportional to the size of the fix. A one-character change and a rewrite cost the same fifteen-repo sweep, because the sweep is the unit of work, not the edit. The implication is that batching discipline matters more than edit discipline on a lane like this one, though that follows from the design rather than from anything measured on this particular day: both corrected gates here lived in unrelated systems, so nothing rode the same sweep.

## The gate that forced an honesty edit

Twelve repos needed a copy commit, and four of them needed a second pass after it. Those four are the interesting ones, because the gate did not extract more words from them on the second pass, it extracted truer ones:

```text
fix: state MLB Booth data boundary honestly
fix: clarify Loose Ends queue priority
fix: make Bazaar marketplace copy precise
fix: tighten Pit Wall marketplace copy
```

The template's own description went the same direction. One long run-on became shorter sentences. "real-shell screenshot evidence" was softened to "shell screenshot evidence." "plugin-specific SVG banner" became "product-specific SVG banner." A gate asking for four readable sentences and a stated trust boundary got four readable sentences, and the claims came out weaker and truer than they went in. That was not designed. It falls out of asking for a trust boundary at all, because you cannot state one without noticing where yours actually sits.

## A watch that could only see page one

Third thread, and it stays short because it is the same defect wearing different clothes. In `intent-os`, bead `spine-lkb.12` and PR #566 shipped `ops/plane-invite-watch/`, a daily VPS timer that reconciles the Plane workspace invitation list against members and against its own known state, paging Buzz sys-incidents when an invitation is queued with no mail behind it, sits unclaimed past 7 days, or belongs to somebody who is already a member.

Two details earn its place. Its `automations.md` row is marked `NOT-YET-ARMED until deploy receipts`, which is the same call as reporting `retention_percent` as `null`: a row describing a timer nobody has armed yet is a lie in a document people trust. And the review caught that both fetches read only the first page, because "a watch reading only page one would go blind past 100 rows," rated HIGH. Cursor and envelope pagination went in, hermetic drill 9/9 after the change, full `pnpm check` green.

## Three sessions, one steer

Three sessions ran concurrently, and the split is worth one line because it was not arbitrary. The fan-out work ran on Claude Opus 5 with Claude Opus 4.8 alongside it, 754 turns and 171 tool calls across twelve hours, because fifteen near-identical repos is exactly the job where a model holding a long invariant beats a fast one. The `intent-os` watcher ran on Claude Fable 5, 443 turns and zero errors in about an hour.

One steer is worth quoting exactly as typed, because it is the day's thesis arriving as a correction and it arrived before I had written any of the above:

> yes add the auto-stash guard that seems like a band daid whats root cause fix

The model had proposed the thing that makes the symptom go away. The correction was not "that code is wrong," it was "that is the wrong layer." Same shape as the two gates: a check that satisfies the condition in front of it without touching the property underneath. Other steers that day were shorter and in the same register: "rm -rf the decoy dirs," "verify the card shows up on ezekiels board," "and what did u decide ?"

## What the day bought

Two gates that now measure the property instead of a stand-in for it, and one monitor that can see past its first page. That is the cheap half.

The expensive half is the fifteen repos, and what it bought there was a fleet where no consuming repo can run a gate that quietly differs from canonical. The cost of that guarantee is that every correction, however small, is a fifteen-repo sweep with four hashes moving in lockstep per repo. Forty-eight commits to move one conditional is not overhead I would call waste. It is the price of the tamper-evidence, stated in full, which is the number that belongs next to the guarantee whenever the next lane gets vendored.

## Also shipped

An adversarial multi-seat council ran that evening against a proposed company-calendar stack for the estate, reviewing it through fault-tolerance, data-model and source-of-truth, and convention-over-configuration lenses. Separately, an external tool called "no-mistakes" (a Go git-proxy that runs an intent, review, test, docs, lint, push, PR, CI pipeline inside an isolated worktree) was evaluated against the in-house audit-harness.

## Related Posts

- [The Skip That Counted as a Pass](https://startaitools.com/posts/the-skip-that-counted-as-a-pass/)
- [A Green Result Only Covers What It Ran](https://startaitools.com/posts/a-green-result-only-covers-what-it-ran/)
- [Scope the Guard to What the Job Actually Writes](https://startaitools.com/posts/scope-the-guard-to-what-the-job-writes/)
