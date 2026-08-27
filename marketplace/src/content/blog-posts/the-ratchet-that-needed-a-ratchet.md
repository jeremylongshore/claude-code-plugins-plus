---
title: "A Ratchet Is Only as Strong as Its Re-Baseline Rule"
description: "Pinning compliance violations in CI is the easy half. Eight iterations in one day to build a gate that refuses unauthorized baseline growth."
date: "2026-08-26"
tags: ["ci-cd", "claude-code", "release-engineering", "testing", "automation"]
featured: false
canonical: "https://startaitools.com/posts/the-ratchet-that-needed-a-ratchet/"
---
The claude-code-plugins marketplace carries thousands of skill and agent markdown files, contributed over a long stretch by a lot of different hands. A schema validator, `scripts/validate-skills-schema.py`, grades them at a strict marketplace tier where a missing required field is an ERROR, not a warning. The corpus fails that grading in bulk. It always has.

That leaves two bad options and one good one. Fail CI on the whole corpus and nothing merges again. Ignore the findings and the debt compounds quietly. Or ratchet: pin what exists today, fail on anything new.

I built the ratchet on 2026-08-26, across 424 commits on the mainline of that repo. It took eight iterations, and only two of them were about the debt itself.

## How do you ratchet compliance debt without blocking merges?

You pin the current violation set as a baseline and fail only on what is new. Existing debt is tolerated; a new (path, rule, field) triple fails the gate. That stops silent growth without blocking every merge. The other half, and the harder one, is making the pinned baseline itself impossible to grow without a reviewed, single-file change.

## The compliance ratchet mechanism

`scripts/check-marketplace-compliance-baseline.py`. Its docstring states the whole contract:

```text
Fail closed when marketplace compliance debt grows beyond the pinned baseline.

Blueprint 727 E6.3, phase R1: compare the validator's triple-keyed marketplace
findings with ``scripts/.marketplace-compliance-baseline.json``. Existing baseline
debt is tolerated; a new (path, rule, field) triple fails the gate.
```

The pinned artifact is `scripts/.marketplace-compliance-baseline.json`. The final capture of the day, `ef7b666f2` at 23:05, held schema_version 4.1.0, 2,132 pinned violation triples, and a rule_inventory of 19 rule ids.

A pinned entry is exactly this shape:

```text
plugins/ai-agency/hyperflow/agents/accessibility-reviewer.md :: E-MISSING-REQUIRED-FIELD :: author
```

Path, rule, field. Three keys, one line, sorted. Nothing clever, and the lack of cleverness is the point: a diff on that file is human readable, so a reviewer can see what someone is asking to forgive.

The file also carries a corpus block and a separate quality reading, and the two must not be confused with each other:

```json
"corpus_definition": "resolveCorpus('graded')",
"corpus": { "agent_files": 357, "command_files": 373, "plugin_dirs": 593, "skill_files": 3628 }
```

In the final capture `grade_A_plus_B` is 2979 and `grade_A_plus_B_pct` is 82.1114. That percentage is 2979 over the 3628 graded skill files. It is the share of graded files scoring A or B. It is not a ratio involving the 2132 errors, and it does not move in lockstep with them: one file can carry several violation triples, and a file can score a B while still contributing to the pinned set. Two quantities, two denominators, one artifact. The percentage moved during the day, from 81.6428 in the first capture to 82.1114 in the last, which is a second and independent signal that the docs work was landing. I am labouring this because the post's own argument is that a number is untrustworthy until you can prove what it measures, and I would rather be tedious than do the thing I am complaining about.

The debt is concentrated rather than scattered, which is what makes paying it down tractable at all. These are the top 6 of the 19 rule ids in the final capture, so they do not sum to 2132:

| Rule | Pinned count |
|---|---|
| E-MISSING-REQUIRED-SECTION | 840 |
| E-MISSING-REQUIRED-FIELD | 805 |
| E-FRONTMATTER-9c196f479e69 | 222 |
| E-TIER2-TOOL-SAFETY-5d322e66e4de | 185 |
| E-TIER2-ORCHESTRATION-BOUNDS-31b9cdf7bcb8 | 30 |
| E-REFERENCE-ESCAPES-SKILL-DIRECTORY | 19 |

Two rules account for 1,645 of the 2,132. That is a writing project, not an engineering project, and I will come back to it. Only two rows moved all day. E-MISSING-REQUIRED-SECTION went from 956 in the first capture down to 840. E-MISSING-REQUIRED-FIELD jumped from 580 to 805 at the +237 capture and then held flat for the rest of the night. The other four rows in the table never moved at all.

## Eight iterations, each closing the hole the last one left

Grouped by what each one addresses, not by when it landed. The real mainline order follows the walkthrough.

**1. `166a1fad5` ci: add marketplace baseline capture workflow.** A new `.github/workflows/capture-marketplace-compliance-baseline.yml`, 59 lines. Something has to produce the baseline before anything can compare against it.

**2. `cf7410df0` feat(ci): ratchet marketplace compliance debt.** The check script itself at 80 lines, `tests/test_marketplace_compliance_ratchet.py` at 51 lines, and 7 lines wiring the job into `validate-plugins.yml`. At this point the ratchet works, in the sense that it does what the docstring says.

**3. `d809b9a34` fix(ci): ratchet full marketplace compliance corpus.** The ratchet was only seeing part of the corpus. The fix was inside the validator, `validate-skills-schema.py`, at +61/-33, plus +28/-1 of baseline tests and two lines in `validate-plugins.yml`.

**4. `cc7e49683` feat(ci): isolate marketplace compliance ratchet.** The ratchet was sharing a job with the legacy checks, so its verdict was buried in their output. Pulled apart in `validate-plugins.yml` at +22/-13, with CLAUDE.md updated in the same commit at +1/-1.

**5. `22d621efa` fix(ci): detect untracked compliance baseline.** +3/-2. A baseline file that was never `git add`ed still let the workflow report success. The gate was comparing against a file that, from the repository's point of view, did not exist.

**6. `d7d233297` fix(ci): pin marketplace baseline contract metadata.** +39 lines to the check script, +16 to its tests. The `metadata_drift()` docstring is the heart of the whole day:

```text
Return baseline-contract changes that require a conscious re-baseline.

Triple comparison alone cannot distinguish an intentional validator-rule
change from legacy debt. The emitted schema version and rule inventory are
therefore part of the pinned contract: either changing them must fail the
ratchet until the dedicated baseline-capture transaction has been reviewed.
```

Comparing sets of violations is not enough, because you can shrink the set by changing what counts as a violation. A ratchet built only on triples treats "we fixed 300 files" and "we stopped checking for that" as the same event. So `schema_version` and the 19 rule ids became part of the pinned contract. Move either one and the gate fails until a human has looked at the re-baseline.

**7. `242d8e051` fix(ci): forbid unauthorized baseline growth.** The E6.6 rule, implemented in `baseline_growth_error()`. Baseline growth is legal only when the pull request touches exactly one file, `scripts/.marketplace-compliance-baseline.json`, and the head branch is prefixed `automation/compliance-baseline-`. Anything else is a violation. The commit touched `.github/CODEOWNERS` (+1), `validate-plugins.yml` (+12), the check script (+68/-1), and the tests (+25). The CODEOWNERS line is one line:

```text
/scripts/.marketplace-compliance-baseline.json @jeremylongshore @blueandyellow44
```

That routes any change to the pinned file to two named owners. It requests review; whether review is mandatory depends on branch protection, which is configuration and not code. The claim I am willing to make from the repository alone is the E6.6 one: a growing baseline is rejected outright unless it arrives as a single-file change on an `automation/compliance-baseline-` branch. That rule lives in the script, so it holds regardless of settings.

**8. `f53930446` fix(ci): run marketplace ratchet before legacy checks.** Ordering, +13/-7 in `validate-plugins.yml`. A gate that runs after the noisy checks gets read after everyone has stopped reading.

Sort those by what they actually address and the shape of the day comes out. Three of the eight (5, 6, 7) exist to make the pinned file un-quietly-editable. Two more (4 and 8) exist to make its verdict legible: where the result is reported, and in what order. Iteration 1 builds the file, and only 2 and 3 are about the violation set itself. A quarter of the day's work on a compliance ratchet was about compliance.

### The order the mainline actually saw them

The grouping above is thematic. This is `git log --first-parent --reverse`, with the capture commits interleaved, all times normalized to the automation host's fixed UTC-6. The mainline is linear: the eight ratchet commits are direct single-parent pushes with committer equal to author, and only the captures are squash-merges, which is why those carry a GitHub committer.

| Time (-0600) | Commit | What |
|---|---|---|
| 20:36 | `166a1fad5` | add capture workflow (walkthrough 1) |
| 20:39 | `22d621efa` | detect untracked baseline (walkthrough 5) |
| 20:43 | `885890505` | capture: 2011 |
| 20:45 | `cf7410df0` | ratchet compliance debt (walkthrough 2) |
| 20:51 | `d809b9a34` | ratchet full corpus (walkthrough 3) |
| 20:53 | `19e4af810` | capture: 2248 |
| 20:57 | `f53930446` | run ratchet before legacy checks (walkthrough 8) |
| 21:04 | `cc7e49683` | isolate the ratchet (walkthrough 4) |
| 21:08 | `d7d233297` | pin contract metadata (walkthrough 6) |
| 21:11 | `242d8e051` | forbid unauthorized growth (walkthrough 7) |
| 21:24 | `eb281e0d6` | capture: 2231 |
| 21:29 | `eaeb0e5b9` | capture: 2216 |

Three things in that column that the thematic grouping hides. The untracked-baseline detection landed second, before the check script it protects existed at all. The ordering fix landed before the isolation it was ordering. And the causal claim survives intact: the +237 capture sits directly on top of the corpus widening, and pinning the contract metadata came three commits later.

## Why comparing violation counts proves nothing

Twenty one captures changed the baseline file that day, one per capture pull request, numbered #1346 through #1367 (#1363 was dependabot). The first four:

| Capture commit | Time (-0600) | Pinned entries | Change |
|---|---|---|---|
| `885890505` | 20:43 | 2011 | first capture, 12 rule ids |
| `19e4af810` | 20:53 | 2248 | +237, 19 rule ids |
| `eb281e0d6` | 21:24 | 2231 | -17 |
| `eaeb0e5b9` | 21:29 | 2216 | -15 |

The remaining seventeen took it down in steps: sixteen captures removed exactly five each, reaching 2136, and the last one removed four, ending at 2132 in `ef7b666f2` at 23:05. Five off, sixteen times running, is what a docs push landing one vendor at a time looks like from the ratchet's side.

The day started at 2011 and ended at 2132. Net, the debt grew by 121, after peaking at 2248 and giving back 116.

It grew because of iteration 3. Widening what the validator inspected made 237 pre-existing problems visible for the first time. No file got worse and no contributor added anything.

The artifact says so directly, and this is the part I would not have believed without the file in front of me. The 2011 capture carried a rule_inventory of 12 rule ids. The 2248 capture carried 19. Seven ids appeared between those two captures: `E-INVALID-FIELD`, three `E-AGENT-*` ids, `E-FATAL-9a99b10dfdaf`, and two `E-VALIDATOR-*` ids.

Those seven account for 12 of the 237. The other 225 are E-MISSING-REQUIRED-FIELD triples on files the validator had simply not been grading before, which is why that row jumps 580 to 805 in the same capture.

So the number moved for two different reasons in one step: new rule categories, and old rule categories applied to new files. A count alone cannot separate those, and neither can a diff of the triples. The pinned rule inventory is what makes them distinguishable, which is `metadata_drift()` in one sentence.

Reading it back from the artifacts, the commit order tells the rest: the widening in iteration 3 lands before the metadata pin in iteration 6, and iteration 6 exists at all because triple comparison alone cannot separate the two cases its own docstring names. I cannot tell you what I was thinking when I saw the jump. I can tell you the fix arrived three commits later and that its docstring describes exactly the ambiguity the jump created.

## The result

The fail-closed gate ended the day as its own top-level job in `.github/workflows/validate-plugins.yml`:

```yaml
marketplace-compliance-ratchet:
  name: marketplace-compliance-ratchet
  runs-on: ubuntu-latest
  timeout-minutes: 2
```

It is listed in the `ci-required` aggregate job's `needs:` array alongside validate, verify, test, and 19 others, for 23 entries in all, so it is a required check rather than an advisory one. It runs two steps: "Refuse unauthorized marketplace baseline growth" (pull_request only, calling the script with `--check-growth-only --base --head-ref`) and "Reject marketplace compliance debt outside the pinned baseline", which is the plain full check.

The comment above that job explains iteration 4 better than I did:

```text
Blueprint 727 E6.4: R1 needs an independently visible, always-reporting blocking
job.  It is listed in ci-required below rather than being folded into `validate`,
so a pre-existing failure in an unrelated validation lane cannot obscure the
compliance-ratchet result.  The validator emits the complete
skills/commands/agents/manifests corpus; observed runtime is about 70 seconds,
bounded here at two minutes.
```

About 70 seconds observed, bounded at two. That budget is what makes the isolation affordable: a lane this cheap can afford to report on its own rather than sharing a job with something slower.

## The unglamorous half

The mainline carries 336 hand-written `docs(...)` commits from that day, 150 of them across these 26 vendors, governing the example sections of their skills: vercel, salesforce, perplexity, mistral, retellai, lokalise, klingai, juicebox, instantly, ideogram, hootsuite, hex, granola, grammarly, glean, gamma, framer, fondo, flyio, flexport, fireflies, firecrawl, finta, fathom, anthropic, anima.

That work is what chips at E-MISSING-REQUIRED-SECTION, and the row moved 956 down to 840, which is the whole 116 the baseline gave back after the peak. Every entry that came off the baseline that night came off this one rule.

The timing explains why the pinned count and the commit count do not line up. Read from the commit timestamps: most of those vendor commits had landed before the first capture at 20:43, so they were already inside the 2011 and never showed as a decline at all. A smaller number landed between the 2248 and 2216 captures. The remainder landed after 21:29, and those are what the seventeen later captures were recording.

The ratchet and the docs push are the same project seen from two ends. One stops the bleeding, the other closes the wound. Only one of them is automation. The other is a person reading a skill file, understanding what it does, and writing an example section that is true. There is no version of this where the 840 goes to zero because a script ran. It goes down because someone spends a Wednesday writing.

## The same shape, on a different system

The other thread that day was supply-chain evidence, six commits in dependency order:

- `880812321` feat(supply-chain): generate pnpm CycloneDX publication sboms. `scripts/generate-publication-sbom.mjs`, 129 lines, with a 28 line test file from the first commit.
- `304d3028f` feat(supply-chain): build SBOM-backed publication reports. `scripts/build-publication-report.mjs`, 69 lines, plus 17 lines of tests.
- `8111e5b12` fix(release): bind CLI evidence to SBOM and package identity. `cli-publish.yml`.
- `a838b4860` feat(release): attach SBOMs to npm publication reports. `publish-all-packages.yml` and `publish-changed-packages.yml`.
- `3c1a53f68` feat(mcp): attach SBOMs to registry publication evidence. `publish-mcp-registry.yml`, `ci/emit-evidence/emit-evidence.ts`, and a two line edit to `scripts/build-publication-report.mjs`.
- `cf5c14a71` feat(evidence): require SBOM digests for every publication. The fail-closed clasp: `release.yml`, `emit-evidence.ts`, and both generators moved together.

That chain sits on top of `80763cac1` feat(evidence): attest required contexts and publications, 9 files at +671/-27, which added `.github/workflows/emit-publication-evidence.yml` (128 lines) and grew `emit-evidence.ts` by +254/-17, a net of 237 lines.

An SBOM you can attach but are not required to attach is the same shape of problem as a baseline anyone can re-pin. In both chains the last commit on the mainline is the one that removes the choice: `242d8e051` for the ratchet, `cf5c14a71` for the evidence. In the SBOM chain that ordering is the tell, because the first five commits each felt like they were already enough.

## Also shipped

`00b71ba66` added kernel coupling violation alerts (`kernel-vendor-hash.yml`, +53/-4) and `a60a2da48` stood up a strict v2 kernel shadow lane (`kernel-shadow-validation.mjs`, +115/-33).

cad-dxf-agent merged three pull requests: #192 repairing real-world persona fixtures, #193 resolving non-breaking frontend audit alerts, and #194 migrating the frontend to React Router 7, which was a security-driven major version bump rather than an upgrade anyone wanted. `285df17f4` registered the cad-dxf-agent plugin in the marketplace.

Six Omarchy submission repos each got presentation assets and a manual validation run. Two carried real fixes: `8aa49e3` preserve unusual repository paths in scanner output, and `d07e6b4` tolerate missing Hyprland session.

## How the day ran with the models

The blog pipeline itself ran on Claude Opus 5 (348 assistant turns) with Claude Sonnet 5 (29 turns), for 377 turns and 207 tool calls with 4 tool errors, pushing the previous day's Tier 3 post through its gate agents. One coordinator message is worth quoting, because it is what a working gate sounds like from the inside:

```text
Five gate agents ran on your draft. Code review PASS, global fact-check PASS,
but both consistency checkers and the skill-local fact-checker returned REVISE.
```

Claude Opus 5 also ran a 180 turn session on the governed second brain, 24 `brain_search` calls and 15 `brain_capture` calls, running the memory-distiller. Claude Fable 5 ran two short sessions: a cad-dxf-agent skill check (15 turns, 7 tool calls, 5 errors, and the same instruction had to be issued twice before it stuck) and a read-only partner-roster query over the EULER MCP that also needed a second push:

```text
Continue. Use only EULER, complete the read-only roster query, and return the
requested JSON now.
```

Now the part that belongs here because it is the same lesson as the rest of the day.

There is no local transcript for the claude-code-plugins thread at all. Not a short one. None. The 424 mainline commits are the only surviving evidence of the largest piece of work I did that day. Earlier drafts said 435, because that count swept in the frozen feature branch and a handful of dependabot heads. Everything above about why iteration 6 followed iteration 5, and what iteration 3 exposed that made iteration 6 necessary, was reconstructed from commit ordering and diffs.

This post also got its own numbers wrong on the first three drafts, because they were read off a feature branch frozen at 21:35 while origin/main went on to record seventeen more captures, and the only thing that caught it was a checker that went back to the mainline artifacts instead of trusting the draft.

A day spent building gates that refuse to accept unwitnessed changes ended with its own best work unwitnessed. The commits are real and the diffs are real, but the reasoning that produced them survives only because it happened to be legible in the order the commits landed. That is luck, not a system.

<script type="application/ld+json">
{"@context":"https://schema.org","@type":"BlogPosting","headline":"A Ratchet Is Only as Strong as Its Re-Baseline Rule","datePublished":"2026-08-26T08:00:00-05:00","dateModified":"2026-08-26T08:00:00-05:00","author":{"@type":"Person","name":"Jeremy Longshore"},"publisher":{"@type":"Organization","name":"Start AI Tools","url":"https://startaitools.com"},"url":"https://startaitools.com/posts/the-ratchet-that-needed-a-ratchet/","image":"https://startaitools.com/images/og-image.png","description":"Pinning compliance violations in CI is the easy half. Eight iterations in one day to build a gate that refuses unauthorized baseline growth."}
</script>

## Related posts

- [A Green Result Only Covers What It Ran](https://startaitools.com/posts/a-green-result-only-covers-what-it-ran/)
- [The Gate That Could Not Fail](https://startaitools.com/posts/the-gate-that-could-not-fail/)
- [The Skip That Counted as a Pass](https://startaitools.com/posts/the-skip-that-counted-as-a-pass/)
