---
title: "A Closed Epic Is a Claim, Not a Fact"
description: "Three agents re-executed 37 closure claims on four shipped epics and refuted three. An audit briefed to refute, not confirm, finds what a review misses."
date: "2026-08-20"
tags: ["ci-cd", "testing", "ai-agents", "devops", "release-engineering"]
featured: false
canonical: "https://startaitools.com/posts/we-told-the-auditors-to-refute-us/"
---
Closing a bead is a claim. Merging a PR is a claim. Writing an after-action record that says
the gate is wired and green is a claim about a claim. None of those are facts. The only way to
turn a claim into a fact is to execute it again, later, with someone whose job is to prove it
false.

That is what happened to four epics I had already closed. Blueprint 727's Epics 1 through 4 went
out across 2026-08-18 and 2026-08-19: 48 merged pull requests in the #1242 to #1289 span, four
after-action records, four closed parent beads. Signed off. Done. The next morning the directive
was one sentence:

> go over the so-called completed epics and beads in detail and make sure the work is really done

"So-called completed" is the whole brief. Not "confirm the work." Not "write a summary." The word
is an accusation, and the right response to an accusation is an adversary, not a reviewer.

So the audit was built as three parallel `Explore` agents, one per epic cluster, each instructed
to **refute rather than confirm**. Execute every claimed gate. Read every bead back from the
store. Check main's live CI, not the record's description of it. All of it pinned to a single
verified state: main at `a9fb4a9f9`, working tree clean, so nothing verified was uncommitted local
work sitting on my box.

They came back with 34 of 37 claims confirmed by execution and three actionable defect classes,
which is the unit the record disposes on: A, B, and C. B covers both of the Epic 1 residual
items, C covers the record drifts. This post is about the three, and then about what I did with
them, because finding a defect is the cheap half. The
expensive half is making that exact defect structurally unable to happen again: a found defect
becomes a gate, and the gate becomes a template.

## How do you audit an epic that is already closed?

Brief the auditors to refute rather than confirm, and pin them to one verified state. Three
parallel agents, one per epic cluster, re-executed every claimed gate against main at `a9fb4a9f9`
instead of reading the closure records. They confirmed 34 of 37 claims by execution and surfaced
three actionable defect classes.

## Refute, not confirm, is a different instruction than it sounds

The distinction matters more than it reads. An agent told to "verify the epic is complete" reads
the closure record, sees the gate name, sees main is green, and confirms. Every one of those steps
is a document lookup. The claim and the evidence for the claim come from the same author.

An agent told to refute has to go somewhere else for its evidence. It runs `npm run
validate:model-id-classifier` itself and reads the exit code. It pulls the branch protection
contexts off the API instead of off the README. It asks when a secret was created and compares that
timestamp to when the record asserted the secret was working. That last one is what caught
Finding B, and no amount of reading would ever have surfaced it.

The three auditors got the same shape of brief and different scope:

- Epic 4, 14 beads. Verdict 14/14 confirmed, 0 refuted. Every gate executed with exit 0 during the
  audit: the gitleaks shape gate with its 10 documented exceptions and no blanket allows, the
  safety ratchet with exact pinned counts, the MCP destructive-policy registry at 14/14 plugins
  with both refusal tests passing, the denylist gate across the 52 first-party skills that carry a
  denylist (not the full skill corpus, which is far larger and shows up again in Finding C), the dolt guard
  suite 6/6, the python suite 55/55. The strongest single proof was that the push leg ran green on
  a real push to main, verified at step-level conclusions rather than at the badge.
- Epics 1 and 2. Closure bodies confirmed. All 12 doc-governance and supply-chain gates exist, are
  wired through `ci-required`, and exited 0 live. Two defects in the Epic 1 residual.
- Epic 3, 10 claims. 9 confirmed, 1 refuted, and the refuted one was red at HEAD while CI had been
  reporting green for two days.

I want the 34 in the record as loudly as the 3. A post where an audit only finds damage is a post
that misrepresents the audit. The epics' bodies were real. The gates existed and had teeth. What
the refutation directive bought was not a demolition, it was three specific things that the
confirm-shaped version of this exercise would have walked straight past.

## Finding A: a gate whose only drift detector reads untracked state

Epic 3 shipped a model-id classifier gate. It keeps a committed exclusion list of bead handles that
look like model identifiers but are not, so that a real unpinned model handle in the corpus goes
red. The list at `schemas/canonical/v0/model-id-exclusions.json` held 393 handles. The live census
counted 394.

The missing one was `claude-or1m`. That is Epic 4's own epic bead.

```
not ok 4 - the exclusion list stays regenerable from the live beads export
  error: 'live handle claude-or1m missing from the committed exclusion list'
```

Epic 4 broke Epic 3's gate simply by existing, and nothing caught it for two reasons that stacked.

**One: the only assertion that could detect drift self-skips in CI.** The census test reads
`.beads/issues.jsonl`, which is an untracked export. It is present on my box and absent on every CI
checkout, so the test skipped, and a skip is not a failure. Main's green CI carried no signal at all
for that gate.

**Two: the gate script never ran.** `validate:model-id-classifier` executed only the test file. It
never invoked `scripts/classify-model-ids.mjs`, which was a reporting tool that always exited 0.
Two independent design choices, each defensible alone, that together produce a gate with no
reachable path to red in the environment where it is supposed to run. That defect class is not new
here. I wrote it up two days earlier in [The Gate That Could Not Fail](https://startaitools.com/posts/the-gate-that-could-not-fail/),
which is the uncomfortable part: I had just published the shape of this bug and still shipped an
instance of it. Knowing a failure mode is not a control. What follows is the control.

This drift class recurs with **every new epic bead** we create. So the fix targeted the class, not
the instance. Pinning `claude-or1m` would have taken thirty seconds and bought nothing.

[PR #1291](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1291) added a census that runs from tracked artifacts alone:

```js
// walk the tracked tree only, so this leg is identical on a CI checkout
// and on a dev box. no untracked export, no skip path.
// pinned is injectable, which is what makes the detection path testable.
export function unpinnedTrackedHandles(pinned = new Set(loadExclusions().protected_handles)) {
  const missing = new Map();                       // prefix -> first "file:line" sighting
  for (const file of trackedTextFiles()) {         // git ls-files, text extensions only
    lines(file).forEach((line, i) => {
      if (!/bead/i.test(line)) return;             // bead-context lines only
      for (const token of line.match(BEAD_ID_SCAN) || []) {
        if (!BEAD_ID.test(token) || MODEL_FAMILY.test(token)) continue;  // claude-opus-5 etc
        if (line.includes(token + '...')) continue;                      // claude-7yz... in prose
        const prefix = token.split('.')[0];
        if (NOT_A_HANDLE.has(prefix) || pinned.has(prefix)) continue;    // claude-code stoplist
        if (!missing.has(prefix)) missing.set(prefix, `${file}:${i + 1}`);
      }
    });
  }
  return missing;
}
```

The reason this works is a property of our own process rather than of the code: a new epic bead
lands in a tracked after-action record almost immediately, as a line reading
``Bead: `claude-<hash>.1` ``. The handle is in the tracked tree before it is anywhere else CI can
see. So the census now has a real signal from a real file, and the drift goes red where it matters.

The gate also grew the two-step shape its sibling gates already used:

```json
{
  "validate:model-id-classifier": "node --test scripts/classify-model-ids.test.mjs && node scripts/classify-model-ids.mjs --check"
}
```

The reporting tool became a gate by gaining a `--check` mode that exits non-zero and names the
offender with a file and line:

Running `node scripts/classify-model-ids.mjs --check` against the pre-fix list exits 1 and prints a
single `model-id-check: FAIL` line to stderr. Paraphrased, because the real string carries
punctuation this blog does not print, it says: handle `claude-or1m`, referenced at
`000-docs/791-AA-AACR-epic-4-safety-register.md:8`, is missing from
`schemas/canonical/v0/model-id-exclusions.json`, regenerate from `.beads/issues.jsonl`.

The failure names the handle, the file, the line, the list it belongs in, and how to regenerate it.
A gate that goes red without telling you which of 394 handles moved is a gate people learn to skip.

Two design decisions inside that PR worth naming, because both had a plausible alternative that
lost.

**List invariants assert always, not conditionally.** Sorted and unique are properties of the
committed file itself. They have no dependency on any export, so there is no defensible reason for
them to sit behind a skip. Anything that can assert from the tracked tree should assert
unconditionally. That is the general form of Finding A.

**`KNOWN_HARNESSES` moved to `scripts/lib/harness-lexicon.mjs`.** Both the portability gate and the
denylist gate needed the same lexicon. The cheap option was to have one gate import the other. I
chose lib extraction instead, because two gate scripts should not share lifecycles: the moment one
imports the other, changing gate A's internals can turn gate B red for reasons that have nothing to
do with what gate B checks. A gate should depend on data, not on another gate.

A Greptile review on that PR asked a good question: does the scan actually surface real handles, or
does it only prove that a correct pin set passes? Fair, and the answer required a new test that
runs the detection path under an **empty** pin set and asserts real handles come back. A gate that
has only ever been observed passing is a gate you are trusting on faith.

The best moment in the whole PR: the tripwire caught its own author. The doc comment I wrote to
explain the scan used `claude-xxxx.1` as an illustrative example, and the scan flagged it. I had to
reword my own documentation to get my own gate to pass. That is not embarrassing, that is the gate
working on the first live input it ever saw.

Evidence, run against the pre-fix list: `--check` exits 1 naming `claude-or1m` at
`000-docs/791-AA-AACR-epic-4-safety-register.md:8`. Simulated CI checkout with the JSONL removed,
as recorded in #1291's verification at merge time: 5 pass, 1 skip, `--check` PASS. The file has
grown a case since.

That one remaining skip is the old live-export parity leg, and it still skips without the untracked
JSONL. I left it that way deliberately. The difference is that it is no longer the only detector:
the tracked-tree census and the `--check` step both run unconditionally on the same checkout, so
the skip now sits behind a leg that cannot skip. A skip is acceptable when something else is
carrying the signal. It was never acceptable as the whole gate.

## Finding B: an OR on a credential is a quieter shade of green

The Epic 1 residual shipped a daily npm stats refresh workflow. It had this in it:

```yaml
token: ${{ secrets.BOT_PR_TOKEN || secrets.GITHUB_TOKEN }}
```

That reads like resilience. It is the opposite. `BOT_PR_TOKEN` is a fine-grained PAT whose pull
requests re-trigger required status checks. `GITHUB_TOKEN` cannot do that: PRs opened by
`github-actions[bot]` do not fire required status checks. That is documented behavior rather than house
lore: GitHub's own [workflow triggering docs](https://docs.github.com/en/actions/using-workflows/triggering-a-workflow#triggering-a-workflow-from-a-workflow)
state that events raised with the default `GITHUB_TOKEN` do not create a new workflow run. So the
fallback path is the zero-checks path.

Token expiry on the first branch does not fail. It silently relocates the pipeline onto a path
where nothing is verified, and every run after that is green because nothing is looking. That
fallback is precisely why the pre-fix scheduled runs had looked healthy.

The auditor then asked the question I would not have thought to ask. When was the secret actually
created? Answer: 87 seconds before the first green run, and that run was a manual dispatch. The
Epic 1 closure record asserted the scheduled trigger was working under the real token at a moment
when the real token had existed for under two minutes and had never been exercised by the schedule
at all.

[PR #1292](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1292):

```yaml
- name: Require BOT_PR_TOKEN (no silent fallback)
  env:
    BOT_PR_TOKEN: ${{ secrets.BOT_PR_TOKEN }}
  run: |
    if [ -z "$BOT_PR_TOKEN" ]; then
      echo "::error::BOT_PR_TOKEN is absent or empty (expired, revoked, or never set). [...]"
      exit 1
    fi
    echo "BOT_PR_TOKEN present."
```

The secret binds through `env:` and the test reads the shell variable, rather than expanding the
secret expression directly into the script body. That is the small habit worth copying: a secret
interpolated into `run:` text becomes part of the script, and scripts get echoed in more places
than people expect.

Both token sites lost the fallback. The network fetch steps gained `timeout-minutes`. And the proof
that was missing got obtained during remediation rather than asserted: the 2026-08-20 00:27 UTC
**scheduled** run `32317409056` completed success in 30.4 minutes and opened [PR #1290](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1290) authored by
`jeremylongshore` via the fine-grained PAT, with `ci-required` reporting on it. That run fired at
00:27 UTC on the pre-#1292 workflow, more than two hours before #1292 merged at 02:43 UTC, so its
30.4 minutes ran without the timeout that section adds. Hold onto that number. That is one
completed run on the real trigger. A manual dispatch is evidence of the code path. It is not
evidence of the schedule.

## The reversal: my corrective timeout broke a healthy pipeline

Proving Finding B produced two corrections to the audit's own findings, which is the part of this
day I would keep if I could only keep one.

The original audit finding described a "~29 minute hang." That was a mischaracterization, and I
wrote the fix against the mischaracterization.

A healthy fetch legitimately takes 25 to 35 minutes. There are 423 candidate packages at four
requests each, roughly 1,700 requests, run strictly serially (`concurrency = 1`) with a 250ms
inter-request sleep. That sleep is a **ceiling** of 4 requests per second, not the achieved rate:
the throttle alone accounts for about 7 minutes, and network round-trip time on the remaining
1,700 calls is what fills the other 20-odd. Measured, the pipeline lands near 1 request per second
end to end, and the last six green runs came in between 29 and 35 minutes. The run the auditor saw
as stuck had actually been killed by the next dispatch's concurrency group, mid-normal-run.

That distinction between the configured ceiling and the measured throughput is the whole reason the
first fix was wrong. I read "4 req/s" off the code comment, did the division, got 7 minutes, and
concluded a 10-minute timeout was generous.

So the 10-minute `timeout-minutes` merged in #1292 was calibrated against the incident instead of
against measured healthy runtime, and it did exactly what a miscalibrated timeout does: it failed a
healthy dispatch. [PR #1293](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1293) raised `timeout-minutes` to 45, which still fails fast against the 6 hour job default
while leaving the real distribution room to breathe.

Same PR, second correction, found while reading the fetch code to figure out why it was serial:

```js
// the parameter is an options object. a positional 4 was accepted
// and silently discarded, so concurrency was always 1.
// signature: collectStats(pkgNames, { concurrency = 1, throttleMs = 250 } = {})
await collectStats(names, 4);   // before: the positional 4 was silently discarded
await collectStats(names);      // after: the defaults are the real behavior, so say nothing
```

The behavior did not change. The honesty did. Code that claims a concurrency of 4 and runs 1 will
eventually cause someone to reason about capacity from a number that was never true.

And a third thing surfaced in the same window: the pipeline could open unmergeable pull requests
by construction. The workflow hardcoded its PR title as a decorated string that predates our
conventional-commit PR-title gate, so `commit-scope-check` fails every PR the automation opens.
This was observed live on #1290. Title generation now emits
`chore(marketplace-site): refresh daily npm download stats`.

Three findings on the corrective work for one finding on the original work. Fixing a defect is
itself a change, and changes need the same skepticism the audit applied. Nobody audits the audit's
remediation, which is exactly why it is a good place for defects to hide.

## Finding C: dated records drift by design

The third class is record drift, and unlike A and B it is not owned by one epic. It is the
disposition bucket the audit record uses for everything that is wrong in a *record* rather than in
a *gate*: two numbers in Epic 2's closure record, a counting basis in an earlier one, and the two
observations Epic 4's auditor filed as designed-behavior rather than defects. One class, several
instances, which is why the headline count is three classes and not three sentences. The
disposition is the part worth transferring.

After-action record 777 states 2 effective authority claimants and 12 canonical-table links. Live
is 3 and 13, because Epic 4's register landed after 777 was written. The pinned test moved with
reality. The dated record did not.

Record 786's "2,700 first-party SKILL.md files" is a file-edit count across duplicated trees:
roughly 1,456 are plugin skills and the rest are curated-mirror copies of the same skills. The
earlier change from 1,454 to 2,700 was a counting-basis change (per-skill to per-file-copy), not a
new round of discoveries. The withdrawal it describes still holds. The number needs a basis note it
never had.

**No source edits to dated records.** The correction mechanism is an addendum, which is what record
802 is. A dated record is a statement of what was believed true on a date. Silently editing it
destroys the only thing it was for. Pinned tests are the surface that must track reality; records
are the surface that must not.

No epic reopens either. The warden standard we run here: deliverables shipped and verified,
corrections are records, not rework. Reopening four epics because three findings landed would have
turned an audit leg that ran in well under two hours into a week of rework, and taught the team
that closing anything is provisional.

## The same principle, applied forward

The audit half of this day was backward-looking. The other half was the same idea pointed at work
that had not shipped yet, and it produced a cleaner demonstration of the ratchet: defect to gate to
template.

Six Omarchy bar-widget repos were built or hardened the same day. Counting only that day's commits:
`omarchy-mlb-booth-entry` went from initial commit to v1.0.0 in 11, `omarchy-pit-wall-entry` took 9
(of 13 in the repo's life), `omarchy-listening-post-entry` 7, `omarchy-x-files-entry` 6,
`omarchy-crew-chief-entry` 3. Four of those commits are review-panel remediation by name, including
`fix: apply the four-reviewer panel findings before submission` on MLB Booth and
`fix: address four-reviewer panel findings (2 BLOCK security, 2 BLOCK correctness, taste, idiom)`
on Listening Post.

The interesting part is not that a review panel found things. It is that the findings became
permanent gates in `contributing-clanker` the same day, which means the next person to write a
widget cannot ship those defects at all.

### c34: the `--exec` command injection nobody would have guessed

A four-agent security review of the Listening Post and X Files entries caught a remote code
execution class that the existing gate c31 did not cover.

Omarchy dispatches a notification click action by running the `--exec` value through a login shell:

```text
// excerpt from the Omarchy shell's Commons/Util.qml singleton, call shape only
execDetached(command)  ->  Quickshell.execDetached(["bash", "-lc", command])
```

So this, in a poller that builds a notification from a feed item (the real line is
`bin/listening-post-poll:154` at `b8316bb`, where the array was still named `args`):

```js
args.push("--exec", "xdg-open " + it.url)
```

is command injection the instant a feed-derived or reply-derived URL carries a `;`, a `$(...)`, a
backtick, a `|`, or `${IFS}`. The URL is attacker-influenced by definition; it came off a network
feed.

The hardened form single-quotes every interpolated segment:

```js
flags.push("--exec", "xdg-open '" + it.url + "'")
```

Gate c34 blocks the absence of that wrap: every double-quoted string literal immediately followed
by a `+` must end in a single quote, and every template-literal `${...}` reaching such a call must
be single-quote-wrapped.

The design decision that mattered was file selection. **I chose a shebang scan over an
extension-only scan**, and the first cut proved why. Filtering by extension silently skipped the
actual vulnerable file, because the real bug lived in `bin/<name>-poll`, an extensionless node
script. The gate false-passed. The historical regression caught exactly that, which is the whole
argument for testing a gate against the real pre-fix commit rather than against synthetic cases
only.

Evidence: 7 synthetic unit cases green, c34 BLOCKs the real pre-fix commit `b8316bb` that shipped
the unquoted concat, c34 PASSes the hardened tree, harness 40/40, lane at 37 gates and 0 BLOCK.

### c35: the runtime that exists on exactly one machine

This class shipped **twice** and would have reached real users.

Two entries were built with a Node.js poller CLI spawned by the QML shell. Both worked on the dev
rig. Both passed every other gate. The dev rig carries a system node at `/usr/bin/node`.

A stock Omarchy install does not. Omarchy installs Node through mise, and mise's shims are exported
only to an interactive shell, never onto the PATH of the graphical session that launches Quickshell. Verified
against a real Omarchy tree: no PATH export in `uwsm/env`, no profile hook, no `environment.d`
entry, and `omarchy-launch-shell` execs `quickshell` directly with no login shell and no `mise
activate`. Node is part of the optional dev environment, so a base user may have none at all.

The user-visible result is the worst shape a defect can take. The plugin installs cleanly. It
enables cleanly. It then silently never populates. Nothing errors, nothing logs, the widget is
just always empty.

The marketplace-validated pattern from MLB Booth and Pit Wall has no extra runtime at all: fetch
with `curl` from a QML `Process`, parse in a plain-JS `Model.js` on Quickshell's own engine,
persist with `FileView { atomicWrites: true }`. Every Omarchy box has a shell, `curl`, and `jq`.

Gate c35 blocks two shapes:

```
BLOCK shape 1: a shipped executable whose shebang names an interpreter
               Omarchy does not guarantee
               #!/usr/bin/env node | deno | bun | python* | ruby | perl

BLOCK shape 2: a .qml spawning one as the first element of a Process
               command array (comments stripped before matching)
               command: ["node", root + "/bin/x-files-poll"]

PASS:          bash, sh
```

The scoping choices are where a gate earns or loses its keep. c35 applies only to trees with a
`manifest.json` declaring `entryPoints`, and SKIPs otherwise, so it does not fire on repos that are
not widgets. `tests/`, `test/`, `docs/`, `*.md` and `node_modules/` are exempt, because a node unit
suite never runs on the user's
machine and blocking it would push authors to delete their tests to satisfy a gate.

Evidence: 8 unit cases green, c35 BLOCKs both real pre-fix trees
(`omarchy-listening-post-entry@fad97bf`, `omarchy-x-files-entry@2829b83`) and PASSes their node-free
current versions, harness 52/52 (c35's 8 cases plus the regressions and fixtures that landed
alongside them, which is why it is not simply 40 plus 8), `[C35] PASS` on all five entries, lane at
38 gates and 0 BLOCK.
Both entries were then re-verified with `node` shadowed by a stub that exits 127, which is the only
honest way to simulate a machine that does not have it.

Those two entries carry commits reading `fix!: remove the node runtime dependency, poll from QML
instead`. That is the same defect c35 now blocks. The fix and the gate landed the same day, and the
ordering is the point: a fix without a gate is a fix for one repo.

### The last click: the template

The final piece was `omarchy-widget-template`, a skeleton carrying the architecture and security
patterns that two shipped entries (Pit Wall and Crew Chief) earned the hard way. A new widget now
starts from a state that already passes the pre-submit gates.

That is the full ratchet:

1. A defect is found in one repo.
2. It becomes a gate, tested against the real pre-fix commit, so it cannot recur in any repo.
3. It becomes a template default, so new work starts past it and the gate never has to fire.

Step 2 without step 3 means every new author meets the gate as a rejection. Step 3 without step 2
means the pattern erodes the first time someone starts from something other than the template.

## Tradeoffs

None of this is free, and some of it is arguably not worth it depending on what you are running.

**Audit time is real time.** Three parallel auditors plus remediation plus the addendum record
consumed most of a working day for work that was already shipped and already paying. If your
closure records are load-bearing for nobody, this is pure cost. Ours are cited by later blueprints
and read by people who were not there, which is what makes a false record expensive later.

**A gate is a permanent maintenance obligation.** c34 and c35 will need updating every time
Omarchy's runtime story or Quickshell's dispatch changes. The census gate needs its stoplist tended
as our bead vocabulary grows. Thirty-eight gates in a submission lane is thirty-eight things that
can develop their own defects, and the census gate is exactly the proof that a gate can be broken
and quiet.

**False positives cost author trust faster than false negatives cost users.** The c34 quote-wrap
rule is a syntactic heuristic, not semantic analysis. It will eventually block a correct
construction that happens not to match the shape. c35's `manifest.json` scoping and `tests/`
exemption exist to shrink that surface, and they shrink detection too. Every scoping decision is a
false-negative decision wearing different clothes.

**The warden standard is a real bet.** "Corrections are records, not rework" keeps a team moving,
and it also means an epic can be marked complete while carrying a known correction. That works
because the corrections are discoverable in the addendum. It stops working the moment addenda stop
being read, and nothing in the system enforces that they are.

**A template can encode a pattern before it is proven.** `omarchy-widget-template` freezes what two
shipped widgets earned. If either of those patterns turns out to be wrong at ten widgets instead of
two, the template has been quietly propagating the mistake the entire time, and templates are much
harder to un-propagate than gates are to change. I took that bet knowingly: the patterns in it are
the ones that survived a four-agent security panel, not the ones that merely worked.

**Adversarial agents are optimizers, and refutation is a target.** An agent told to refute will
find something. Two of the three auditors reported honest observations that were designed behavior
rather than defects (a PR-diff gate passing vacuously on push events, a self-disclosed
`enforce_admins: false` residual), and labeled them as such. That labeling discipline is what keeps
"refute" from degrading into manufactured findings, and it is the thing I would watch closest if I
scaled this pattern up.

## Where this sits in the broader picture

Supply-chain review practice converged on the same idea from a different direction. The industry
answer to "is this dependency safe" stopped being "read the attestation" and became "re-execute the
build and compare," because a record produced by the party under review is not independent
evidence. Reproducible builds, in-toto attestations, and provenance verification are all the same
move: do not trust the claim, re-derive it.

Marketplace review is behind that. Most plugin and extension marketplaces still review submissions
by reading them, and most of the interesting defects in this day's work are invisible to reading.
The `--exec` injection reads as ordinary string concatenation. The absent runtime reads as a normal
shebang. The census self-skip reads as a well-written test. All three are only visible by running
something.

The transferable version, for anyone running gates on their own work:

- Every gate needs at least one leg that runs from tracked artifacts alone. If your only drift
  detector reads untracked state, the gate is blind in the environment it was built for.
- A logical OR on a load-bearing credential converts expiry into silent degradation. If the
  credential matters, its absence is red.
- A closure claim about scheduled automation needs one completed run on the real trigger.
- Calibrate timeouts against measured healthy runtime. The incident is the worst possible baseline
  because it is by definition not the normal case.
- Test every new gate against the real commit that motivated it, not only against synthetic cases.
  Synthetic cases pass on a gate that reads the wrong files.

## The collaboration

Eight sessions on `claude-code-plugins`, 463 turns, 1002 tool calls, 51 errors hit, 1429 minutes of
span, run by Claude Fable 5 and Claude Opus 4.8 across the day. Claude Opus 5 ran a separate
profile-card thread, Claude Sonnet 5, Claude Opus 4.8, Grok 4.5, and Claude Sonnet 4.6 covered
other repos.

The audit phase was the strongest argument I have seen for parallel agents doing something a single
session cannot. Three auditors, three scopes, no shared context, reporting at 00:14, 00:15 and
00:19. They had no way to launder one another's assumptions, which is most of the
value: the Epic 3 auditor did not know that Epic 4's bead existed, so it had no reason to excuse
the census failure as expected.

One human course-correction that day, and it was on the widget work rather than the audit:

> hold on their is some confusino braves booth has nothing to do with crew cchief that is way
> jacked up think about that for a minute then fidx it

Two widget repos had gotten cross-contaminated in the model's working picture, and the fix was not
a code change so much as a re-partition of what belonged to which repo. Worth noting because the
audit and remediation ran the whole way with no steer at all, and the one place a human had to
intervene was where two similar-shaped projects sat side by side. That is where agent context
bleeds, every time.

## Also shipped

`intent-os` took PRs #540 and #541 on mission control: an agent and cohort activity view composed so
that a denied read emits nothing rather than an empty row, plus a settlement fix so nothing in the
receipts ledger can be silently invisible. Same principle as everything above, applied to a
dashboard: absent data has to look absent.

`contributing-clanker` [PR #70](https://github.com/jeremylongshore/contributing-clanker/pull/70) cleared all 21 open Dependabot alerts via `npm audit fix` plus a
puppeteer 25 major bump, which is the boring dependency work that has to land before the gate PRs
([#71](https://github.com/jeremylongshore/contributing-clanker/pull/71), [#72](https://github.com/jeremylongshore/contributing-clanker/pull/72)) are reviewable without noise.

A GitHub profile card generator got built in `github-profile` with Claude Opus 5. The ImageMagick
preview reported overlapping SVG `tspan` columns that librsvg rendered correctly, so the preview
tool was lying and a faithful renderer had to be found before any preview could be trusted. Your
preview tool is also under test. It also caught its own accuracy bug, counting 103 "public sources"
because the token could see private repositories, corrected to 85 to match the REST count.

---

## Related Posts

- [The Gate That Could Not Fail](https://startaitools.com/posts/the-gate-that-could-not-fail/)
- [Every Safety Gate Has a Failure Direction](https://startaitools.com/posts/every-safety-gate-has-a-failure-direction/)
- [Honor the Gate When the Verdict Is Inconvenient](https://startaitools.com/posts/honor-the-gate-when-the-verdict-is-inconvenient/)
