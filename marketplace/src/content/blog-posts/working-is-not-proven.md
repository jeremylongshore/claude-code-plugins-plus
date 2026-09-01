---
title: "Every Claim Needs a Shipped Source and an Executable Proof"
description: "Every claim needs a shipped source and an executable proof. What a six-hour audit that closed nothing found out about code that was already finished."
date: "2026-08-31"
tags: ["testing", "ci-cd", "automation", "devops", "claude-code"]
featured: false
canonical: "https://startaitools.com/posts/working-is-not-proven/"
---
I told GPT 5.6 Luna, running through Codex, to `finish teh epics and beads` on the plugins repo. It ran for about 361 minutes across 2 sessions and 187 turns, and it closed nothing. No file mutated, no Beads record touched, no GitHub state changed. Its closing line was that the worktree was clean at `origin/main` `3c5be4a5981ed5089deedff53d18136b9848a18c`.

That is not a failure report. Asked to finish three epics, the honest deliverable turned out to be an inventory of what "finished" would actually require, and the five open beads had five different meanings of "not done". Two of them are closable by writing code. The other three need an owner clicking a setting, a calendar to run out, and a record corrected to match reality.

The same gap kept showing up until the day ended, and three of the day's fixes were to [proof machinery that could not be trusted](https://startaitools.com/posts/a-green-result-only-covers-what-it-ran/) about its own state: a gate runner manufacturing false failures, a render check poisoned by its own output, and a liveness marker that could not tell quiet from dead.

## Five ways a finished feature is still not done

The audit read Epics 6, 7 and 10 against Blueprint 727, the live Beads Dolt database, `origin/main` code, tests, workflows, branches and PRs. Read-only throughout. What came back was a taxonomy.

**Code live, acceptance failing at the platform.** `claude-nfzl.6` ships in `242d8e051`: `validate-plugins.yml`, `check-marketplace-compliance-baseline.py`, `.github/CODEOWNERS`, and 13 focused tests. Then `gh api repos/.../branches/main/protection` returns `required_approving_review_count=0` and `require_code_owner_reviews=false`. The gate is written, committed and switched off. Nothing in the repository can close that bead. It needs an owner clicking a setting.

**Calendar-gated, not code-gated.** `claude-nfzl.7` has PR #1384 merged as `b786149e1`, R2 and R4 code live, and a full-corpus run passing in about 58 seconds across 2053 live triples with zero newcomers. The only thing outstanding is a mandatory two-week R1 observation window and a flap receipt. Time closes that one. Code cannot.

**Complete but stale.** `claude-jqvw.11` runs `check-mirror-licenses.mjs` green at 36 of 36 configured sources and 36 of 36 `.source.json` mirrors, with sync hard-failing on a missing license include. Blueprint and Beads still carry the historical 63/63 denominator. The record is wrong, not the code.

**Green suite, missing red run.** `claude-jqvw.1` has the whole chain working: tag, GitHub Release, reassertion, npm publish, with `npm-publication-lock.test.mjs` passing 11 of 11. What it does not have is the required fault-injection RED run proving no orphan npm publication and retained signed evidence-row proof. A passing test says the happy path holds. It says nothing about the failure mode you built the lock for.

**Flag exists, workflow never calls it.** The evidence emitter supports `--certification-report`. `.github/workflows/emit-evidence.yml` never generates or passes a real one, so only catalog, unicode and required-context rows get signed. `claude-snmr.5` is open because of that, and `claude-snmr.6` is explicitly blocked behind it.

The audit also decomposed a 79-entry corpus shrink (2132 pinned against 2053 live) into 78 `E-MISSING-REQUIRED-SECTION` plus 1 `E-FRONTMATTER`, rather than treating it as one bot-authored rule change. Last baseline commit was bot PR #1367 on Aug 27. And mid-run another agent modified `freshie/scripts/promote-to-curated.py` and moved the branch to `fix/curated-promotion-cohort-parity`. The auditor refused to reset or touch it and took all its Epic 6 evidence from read-only Git views of `origin/main` instead. That is the correct call in a shared working tree, and it is a call I have watched agents get wrong.

Merged in that repo the same day anyway: PR #1401 (`3c5be4a59`, secure projections and Snowflake, the same commit the auditor later signed off as its clean baseline), PR #1403 (Snowflake operator skills), and `d6d14da83` unifying the freshie curated promotion cohort.

### Why not just close the beads

Because a closed bead that traces back to switched-off branch protection is worse than an open one. An open bead is a question. A closed bead is an answer, and nobody re-audits an answer. Convert the first into the second and you have not finished the work, you have deleted the only record that the work is unfinished. Six hours of audit output that closes nothing is cheaper than one wrong close, because the wrong close comes back as a production surprise with no bead pointing at it.

## Writing the requirement down as an enforced file

While that audit ran, the Omarchy fleet moved: `omarchy-widget-template` plus 15 `omarchy-*-entry` repos: docket, quiet-queue, foundry, loose-ends, bazaar, capture-conveyor, listening-post, crew-chief, desk-transition, flow-boundary, wait-state, workspace-storyboard, x-files, mlb-booth and pit-wall. The commit shapes repeat: `test: certify <X> on Buzz`, `chore: sync canonical Omarchy gates`, `fix: bind <X> marketplace claims`, `test: refresh <X> Buzz proof`.

The artifact worth naming is 18 lines of markdown in the template, `contracts/marketplace.md`, from commit `0607dcc`:

```markdown
# Marketplace claim ledger

Replace this template ledger before calling a generated plugin submission-ready.
Every meaningful listing claim needs a shipped source and an executable proof.
Do not infer behavior from a mockup, README, test name, or intended design.

| Claim | Shipped source | Executable proof |
|---|---|---|
| Visible bar outcome and primary panel action | `BarWidget.qml`, `Panel.qml` | plugin-specific contract and interaction tests |
| Data source, scope, cadence, and bounds | service QML, `Model.js`, or shipped helper | fixture-backed unit, boundary, and failure tests |
| Local writes, network use, credentials, and explicit exclusions | every shipped runtime path | security contract tests plus canonical gates |
| Marketplace image tells the same product story | `assets/banner.svg`, deterministic E2E fixture | hash-bound Buzz render receipt and visual approval |
```

Two columns per claim, and both are mandatory. A test name is not a proof. A mockup is not a source. The ledger also fixes the description rule so it stops being a matter of taste: the final listing description and `barWidget.description` must be identical, exactly 500 characters, name the product, explain what appears in the bar or panel, state what the user can do, and disclose the material trust boundary.

A markdown file nobody enforces is a wish. The same commit added six lines to `tests/contract.test.js`, five assertions plus the read, so the ledger cannot be quietly deleted or hollowed out into a heading with nothing under it:

```javascript
const marketplaceContract = read("contracts/marketplace.md")
assert.match(marketplaceContract, /\| Claim \| Shipped source \| Executable proof \|/)
assert.match(marketplaceContract, /exactly\s+500 characters/)
assert.match(marketplaceContract, /bar or panel/)
assert.match(marketplaceContract, /trust boundary/)
assert.match(marketplaceContract, /hash-bound Buzz render receipt/)
```

The commit touched `.harness-hash` (+8/-7), `README.md`, `contracts/marketplace.md` (+18), `tests/RTM.md`, and `tests/contract.test.js` (+6). Small diff. It is the same move the audit was asking for, applied one layer earlier: state the requirement in a file, and make the test suite fail if the file stops saying it.

## Two bugs where the proof machinery broke its own preconditions

Both of these landed the same day, in the same fleet, and they are the same shape: the thing that verifies work was interfering with the work it verified.

### A gate runner racing its own input

`scripts/run-plugin-gates.sh` in omarchy-docket-entry fed each gate a small JSON envelope through a pipe. A gate that exits before reading stdin races the producer into SIGPIPE, exit 141. So a deterministic invalid-verdict check became an intermittent gate crash, dependent on scheduling. Commit `240b2d6` swaps the pipe for a here-string:

```bash
INPUT="$(jq -nc --arg c "$TARGET" '{candidate:$c, action:"omarchy-submit", env:{repo:""}}')"
for gate in "$GATES"/c*.sh; do
  # Feed the small JSON envelope with a here-string. A pipe lets a gate that
  # exits before reading stdin race the producer into SIGPIPE (141), turning a
  # deterministic invalid-verdict check into an intermittent gate crash.
  verdict="$(bash "$gate" 2>/dev/null <<< "$INPUT")"
  # A gate that emits nothing has crashed hard. Fail closed rather than
  # silently counting it as clean, which is how a broken gate becomes theater.
  if [[ -z "$verdict" ]]; then
    # (excerpt: the loop goes on to print CRASH, set blocked=1, and continue)
```

The fail-closed-on-empty branch and that comment about theater were already in the file. Somebody had already thought carefully about a gate emitting nothing. What was broken was that the runner could manufacture the empty verdict itself, and then correctly fail closed on a condition it had caused. This is the inverse of the audit's problem: there the evidence was missing, here the evidence was lying. A safety check firing on its own noise is still a false alarm, and false alarms are how people learn to ignore gates.

### A render that dirtied the source it was proving

`scripts/rig-render.sh` in the template will only issue a render receipt if the source tree is clean, which is the entire point of a receipt: it binds an image to a specific source state. The glob of files whose modification marks the tree dirty included `preview.png`, the render's own output.

So a failed render left a stale `preview.png` behind. That file marked the source dirty. No retry could ever produce a clean receipt. One bad render poisoned every attempt after it. Commit `52a9d42` removes the artifact from the precondition: the pathspec used to carry `preview.png` between `manifest.json bin` and `README.md`, and after the fix it reads:

```bash
SOURCE_DIRTY=false
if [[ "$SOURCE_COMMIT" == "unknown" ]] || \
   [[ -n "$(git -C "$TARGET" status --porcelain --untracked-files=all -- \
     '*.qml' '*.js' manifest.json bin README.md assets/banner.svg \
     e2e scripts/rig-render.sh 2>/dev/null)" ]]; then
  SOURCE_DIRTY=true
fi
```

The obvious fix is to delete `preview.png` at the top of every run. That fix is wrong, and the reason is worth stating. The receipt exists to distinguish a render of clean source from a render of dirty source. If the script scrubs the output first, every dirty-source failure gets laundered into a clean run and the distinction the receipt sells is gone. Removing the output from the precondition is a smaller change and it keeps the signal. The same class of fix landed in two other entries that day: "keep failed Capture renders retryable" in capture-conveyor (`04ca3ae`) and "allow clean render retry after failed capture" in loose-ends (`88054b8`).

## A dead-man that could not tell quiet from dead

At 22:12 I asked for something unrelated: `i need ezekiel to start recievinf the emails like he does withe blog backfill skill that runs the blog work u know what i mean`. Ezekiel does the social posting. The blog pipeline already emails him a per-post packet. The real-estate content machine behind comehomealabama.com, run out of coastal-realty-ops, had been soaking unattended for 11 days and it was time to point it at him too.

Claude Fable 5 ran a health check before flipping anything, on the reasoning that Ezekiel should not start receiving packets from a broken producer and should not get 11 days of backlog dropped on him in one morning. The soak verdict: five posts landed on Aug 21, 24, 26, 28 and 31, all Monday/Wednesday/Friday, every prior post packeted, liveness green, and the ledger showed exactly one unsent packet. He would start with one email.

The flip itself was five minutes and nine tool calls, shipped as coastal-realty-ops PR #50 (`17394b3`): `packet.env` `PACKET_TO` set to `ezekiel@intentsolutions.io` with me on CC. The file is sourced per run, so no restart, effective at the next 05:15 sweep. That commit also banked 5 lines of `decisions.jsonl` and 3 lines of `topics-queue.jsonl` the producer had accumulated during the soak.

The health check is what found the bug. `scripts/journal/mandy-posting-packet.sh` had three clean no-op exits (no ledger, no packets due, no digest week) and all three returned 0 without touching `mandy-posting-packet.ok`. The estate dead-man sweep reads a fresh `.beat` with a stale `.ok` as running-but-failing. So a perfectly healthy pipeline with nothing due for two days would page. It was already visible in the wild: `.ok` stuck at Aug 29 (the Aug 28 post's packet fired that morning) while `.beat` kept advancing.

The commit message for comehomealabama PR #8 (`d87bada`) carries the rule in one line: a clean no-op IS a successful run. Change was +5/-3 in one shell script, verified with `shellcheck -S warning`, `bash -n`, and a live `--sweep` against the current ledger that logged "no packets due" and refreshed `.ok`.

The tempting shortcut is to touch `.ok` at the top of the script and stop thinking about it. That reports healthy before doing any work, which is precisely the failure the dead-man exists to catch. The marker belongs on every path that legitimately completes, no-ops included, and on no path that does not. Quiet and dead have to be distinguishable, and the only place that distinction can live is in the script that knows which one it is.

The part I keep coming back to: nothing was on fire. The two-day quiet window that would have false-paged had not happened yet. It got found because Claude Fable 5 checked the system before trusting it with a person's inbox.

## Also shipped

**Retiring a carried patch in the Buzz fork.** `cb633a0c4` plus PRs #30 and #31 emptied `CARRIED_PATCHES` in `scripts/fork-gates/check-additive-only.sh`, deleted the carried 311-line e2e spec `desktop/tests/e2e/manual-invite-join.spec.ts`, replaced FORK.md's carried-patches exception with `None - empty by design`, and filed a 131-line audit at `000-docs/009-AA-AUDR-fork-contract-breach-2026-08-16.md`. PRs #26 and #27 had carried an invite-to-default-channel patch on fork main, the same class of fork-contract breach as the earlier PR #16 incident already documented in `000-docs/007`. Production now runs the upstream published image (`ghcr.io/block/buzz@sha256:fe092cf9...`), enrollment moved to an ops-side watcher in the private ops repo, and the real fix is tracked upstream as `block/buzz#4307`. Merge-and-restore beat revert because the upstream sync supersedes the carry without rewriting history. Both `check-additive-only.sh` and `check-must-survive.sh` pass with `CARRIED_PATCHES` empty, gate output pasted into the PR body. A large upstream sync (`91452d823`) landed about 15 upstream commits the same day.

**A discovery that ended in deliberate non-adoption.** Starting 02:10, Claude Fable 5 ran a discovery on the third-party `no-mistakes` tool against the Intent Solutions testing SOP. It is a Go git-proxy: you push to a `no-mistakes` remote instead of origin and it runs intent, rebase, review, test, docs, lint, push, PR and CI in an isolated disposable worktree, with an LLM review stage that falls back across agents and a CI repair loop with guarded force-push. We did not adopt it. What came out was `worktree-run.sh` built into `audit-harness`, a verification of the read-only-test rule, and the non-adoption recorded as a decision instead of an unwritten "we looked at it once". Two incidental findings: `yamllint` was not installed on this box, and the escape-scan expectation was inverted, since the test expects a non-zero exit (a REFUSE) when policy is being weakened.

**A $0 calendar stack, decided in conversation, no commits.** The one item of the day with neither a shipped source nor an executable proof, recorded here as the exception it is. With a Buzz VPS bill due the next day I asked what was free, then `im so confused whata the most texhnically sound optiin that would be most respected by underground linux users as my teams set up`. Answer: Radicale on the VPS that already exists. One Python process, and the team calendar is a directory of plain `.ics` text files you can grep and diff, backed up by borg like any other directory. khal plus vdirsyncer for the terminal, Cal.com's free tier for outward booking. The part worth recording is the refusal. Fastmail was rejected as a mail viewer, because a calendar decision should not quietly turn into a second mail migration one month after the MXroute cutover.

## What the day cost

The session analyzer logged 19 failure-to-fix arcs and 2 course-corrections across four models (Claude Opus 5, Claude Sonnet 5, Claude Fable 5, GPT 5.6 Luna), over sessions spanning 1169 minutes of wall clock. GPT 5.6 Luna took `claude-code-plugins` for 2 sessions, 187 turns, 361 minutes. Claude Fable 5 took `intent-eval-platform` for 3 sessions, 27 turns, 8 errors and both course-corrections. Claude Opus 5 and Claude Fable 5 split the home layer across 3 sessions and 273 minutes with 9 errors. Claude Fable 5 did coastal-realty-ops in 5 minutes and 9 tool calls.

The two ends of that range are the same instinct at different scales. GPT 5.6 Luna was told to finish the epics and spent six hours producing an audit that closed nothing, because closing them honestly was not on the menu. Claude Fable 5 was told to switch Ezekiel on, checked the pipeline's health first, and then did exactly what it was asked. Only one of the two delivered the literal request, and it delivered it last. Both started from the same place: find out whether the thing is true before writing down that it is.

## Related Posts

- [A green result only covers what it ran](https://startaitools.com/posts/a-green-result-only-covers-what-it-ran/)
- [Scope the guard to what the job writes](https://startaitools.com/posts/scope-the-guard-to-what-the-job-writes/)
- [One corrected check, fifteen repos](https://startaitools.com/posts/one-corrected-check-fifteen-repos/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Every Claim Needs a Shipped Source and an Executable Proof",
  "description": "Every claim needs a shipped source and an executable proof. What a six-hour audit that closed nothing found out about code that was already finished.",
  "url": "https://startaitools.com/posts/working-is-not-proven/",
  "datePublished": "2026-08-31T10:00:00-06:00",
  "dateModified": "2026-08-31T10:00:00-06:00",
  "author": {
    "@type": "Person",
    "name": "Jeremy Longshore"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Start AI Tools",
    "url": "https://startaitools.com"
  }
}
</script>
