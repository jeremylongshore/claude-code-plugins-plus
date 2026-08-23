---
title: "Every Check Should Report What It Did Not Look At"
description: "A status job that always runs reports which checks executed and which are unproven, so a skipped GitHub Actions job cannot read as a pass."
date: "2026-08-22"
tags: ["ci-cd", "security", "devops", "testing", "automation"]
featured: false
canonical: "https://startaitools.com/posts/the-lane-that-reviewed-nothing/"
---
Yesterday I wrote about [the gate runner that counted SKIP as PASS](https://startaitools.com/posts/the-skip-that-counted-as-a-pass/), and the rig proof receipt that closed it. That is the setup, not today's subject. Today's subject is what happened next. The same defect shape surfaced twice more inside a single day, and the second time it was inside the tooling built to catch it.

58 commits across 11 repos. The interesting part is that three of them are the same bug wearing different clothes.

## The review lane that could not review

Seven plugin repos vendor a four lane MiniMax review workflow. Every lane carries the same guard.

```yaml
jobs:
  review-correctness:
    if: vars.ENABLE_MINIMAX_REVIEW == 'true'
    # three sibling lanes, same condition
```

If the repository variable is unset, or the API key is absent, the workflow conditional evaluates false and GitHub Actions skips the jobs. A skipped job renders as a grey tick. A reader scanning a pull request sees four ticks in the checks list and concludes the pull request was reviewed. Nothing ran. No model read a line of the diff.

That is precisely the shape I had spent the week digging out of the [gate runner](https://startaitools.com/posts/the-gate-that-could-not-fail/), reintroduced in the workflow whose entire job is to catch bad diffs.

### Does a skipped GitHub Actions job show as passing

Not literally, but in practice yes. A skipped job renders as a grey tick in the checks list rather than a red X, and a reader scanning the list reads absence of failure as success. GitHub reports the job's real state accurately. The failure is that a human, and a branch protection summary, treat grey and green the same way.

The fix is a status job with no `if` at all, so it always runs and always reports. When the lanes are off it emits a GitHub warning annotation, and the annotation says the thing plainly: green ticks on this PR do not mean it was reviewed. On a fork pull request it reports a notice instead of a warning, because a fork never receives the repository secret, so skipping there is by design rather than misconfiguration. A warning that fires on every external contribution is a warning people learn to ignore.

### Why not just fail the build

The obvious approach is to make the workflow fail when the lanes are disabled. No ambiguity, no annotation to read, a red X that nobody mistakes for a pass.

I did not do that, and the reason is what the lanes are. They are advisory. A maintainer can merge a plugin fix without a model review, and the seven repos deliberately ship with the feature off until someone sets the variable and the key. Failing the build converts an optional feature into a mandatory one by side effect. The next person to hit a red X on a repo that never enabled reviews would not go enable reviews, they would delete the check, and then the disabled state becomes invisible again with an extra step of history behind it.

The requirement was never that the lanes must run. It is that a disabled lane must not be mistakable for a passing one. An always running status job satisfies exactly that requirement and nothing more. Failing the build satisfies a stronger requirement I did not have and do not want.

## The fix that shipped a merge conflict

The commit that landed this is titled "stop a disabled review lane from rendering as a passing one." It shipped a merge conflict into `.github/workflows/minimax-review.yml` and pushed it to main. Six of the seven entry repos carried three conflict markers each.

The workflow no longer parsed. Every run died at 0s, while the gate lane and the test jobs reported success in the same checks list beside it.

Root cause was a rebase where I assumed only the changelog conflicted.

```bash
git checkout --ours CHANGELOG.md
git add -A               # staged the workflow WITH its conflict markers
git rebase --continue    # committed them
```

`git add -A` does not care whether a file still contains `<<<<<<<`. It stages what is on disk.

The part worth writing down is not the rebase mistake. It is the verification. I checked the fix had landed by grepping for the string `Review lanes status`, found a match, and reported the file present and correct. The string was there. It was inside a file that could not parse.

That is a check narrower than the claim it makes. Which is the same defect the broken commit was fixing. The fix for skip renders as green shipped a workflow that renders as nothing at all.

The second verification parses instead of greps.

```bash
grep -c '^<<<<<<<\|^=======\|^>>>>>>>' "$f"          # expect 0
python3 -c 'import yaml,sys; yaml.safe_load(open(sys.argv[1]))' "$f"
actionlint "$f"
```

0 conflict markers, `yaml.safe_load` succeeds, `actionlint` reports 0 issues across all six files. A grep answers "does this text appear." Only a parser answers "is this a workflow."

## The agent that reports the denominator

In `claude-code-plugins` I added an agent called `omarchy-coverage-reporter`.

Every other internal agent in that repo answers "is this correct." None of them answered "what did we actually look at." Five separate incidents in the days before had turned on that second question, so it got its own agent.

It runs the gate lane, the rig checks and the offline tests, then reports the denominator: how many applicable checks exist, and how many executed. The core of it is splitting the single SKIP token into two verdicts that mean opposite things and were previously aggregated together.

| Verdict | Condition | What it means |
|---|---|---|
| NOT APPLICABLE | Predicate false. No QML in this tree, so a QML gate has nothing to say. | Counts as a pass. |
| UNPROVEN | Predicate true, checker could not run. Tree has QML, qmllint was unresolvable. | Never a pass. |
| INCONCLUSIVE | Any UNPROVEN in the set. | Neither pass nor fail. Nobody knows yet. |

INCONCLUSIVE is neither failure nor pass. It means nobody knows yet. That is the state the old runner had no way to express, which is why it kept reporting green: given only PASS, FAIL and SKIP, an unresolvable checker has to land somewhere, and SKIP was the least alarming bucket.

The agent has no Write tool and no Edit tool. That constraint is deliberate and it is the design decision I would defend hardest. A reporter that can repair what it measures cannot be trusted about what it measured. If it can fix the qmllint resolution and then report full coverage, the report is a claim about a tree the reporter changed, and no reader can tell which findings were observations and which were consequences of its own edits. Repairs route to `omarchy-gate-author`. Judgment routes to `omarchy-submission-auditor`.

I chose a new agent over extending the existing auditor because counting what ran and judging what it means are different jobs. The auditor had already demonstrated the failure mode of merging them: it produced a confident verdict over a corpus it never established. It was not wrong about the files it read. It was wrong about which files there were.

## The same principle in two smaller places

Naming these is the point. One fix is a fix. Three places in one day, counting the coverage reporter, is a pattern.

The changelog generator silently dropped any commit subject that was not a conventional commit. It now reports the count and lists examples. Running it surfaced exactly one skipped commit per affected repo, and each one was GitHub's auto generated "Initial commit." Correctly skipped, and now visibly so. The output did not change its behaviour, it changed what it admits.

In `omarchy-crew-chief-entry`, the spool reader is bounded to the newest 64 files at 4 KB each. It now emits a census line stating how many files exist, not how many it read.

```
sessions: 63 shown, +338 not shown (401 files, 713 KB)
```

Under a deliberate 401 file, 713 KB flood, including one 500 KB garbage file, the reader returned 10 KB and the widget rendered 63 live sessions. Before the census line, the parser received well formed chunks, found nothing malformed, and concluded nothing was missing. It would have reported a complete fleet that was short 338 sessions. Every individual piece of that pipeline behaved correctly. The bound was correct, the parse was correct, the report was correct about its input. Nobody was carrying the number 401.

## Also shipped

`contributing-clanker` closed an SSRF that had escaped review twice. Listening Post guarded its curl call with a regex meant to allow only literal IPv4.

```js
/^\d{1,3}(\.\d{1,3}){3}$/   // four decimal parts and nothing else
```

curl resolves through `inet_aton`, which accepts one to four parts, reads a leading `0` as octal and `0x` as hex. So `127.1`, `0177.0.0.1` and `0x7f.1` all fail the regex, get treated as public hostnames, and reach loopback. New gate c38 flags that regex shape in any file that also touches the network, and the fix hint teaches the inversion (allowlist what you accept, then resolve and check the resolved address) rather than adding three more bad patterns to match, because enumerating bad forms is exactly what failed twice.

The changelog security classifier matched on the pattern `'bound '` with a trailing space. That matches "bound the spool read" and misses "bounded read," so a real security fix could file under Fixed and quietly leave the security section of a release note. This one is a plain false negative rather than an instance of the pattern above, since nothing new gets reported, the match just stopped being wrong. Verified both directions: "add a bounded read" now classifies as Security and did not before.

Gate c37, the rig receipt fingerprint, widened to cover every shipped `.js` rather than just the manifest and QML. These plugins keep parsing, host filters and state handling in a `Model.js` that QML imports, so the receipt was certifying a tree whose entire behaviour could change underneath it.

Gate c36 now requires a width constraint AND an overflow rule, not either. It had accepted a QML `Text` as bounded if it declared any one of `width`, `elide` or `wrapMode`. That is wrong on QML semantics: `elide` with no width constraint is a no op, since elision is computed against element width. The gate's own fix hint already read "elide with a width" while the check accepted elide alone, so the enforcement was looser than the advice it printed.

`rig-render.sh` landed in `omarchy-widget-template`. It starts a headless sway on the wlroots backend, installs the plugin into the rig's Omarchy config, launches Quickshell, opens the panel through the plugin's own IPC target, and grabs the frame with grim. Every plugin in the family had been submitted having never been loaded. Static tools cannot see a contract error: Bazaar shipped a `PanelWindow` where the first party popup is a `KeyboardPanel`, passed all nine gates and qmllint, and only a running shell said `Cannot assign to non-existent property contentHeight`.

`omarchy-bazaar-entry` gained install, installed state and a kind filter. Measured before the change: Okomart 1,148 views and 286 installs, Plugin Manager 209 views and 95 installs at 45 percent conversion, Bazaar 82 views and 11 installs at 13 percent. Install shells out to the first party CLI with an argv array and no shell string, because the repository URL comes from a third party catalog and building a shell string out of it is the exec injection shape gate c34 exists to refuse. The installed state scan keys on the id inside each manifest, never the directory name, because Omarchy installs under the full plugin id while a hand clone is usually a short name, and the rig carried both `listening-post` and `io.github.jeremylongshore.listening-post` for the same plugin. Tests caught a version comparison bug: the first version treated a missing segment as smaller than everything, so `1.2.0` read as newer than `1.2`, and every up to date plugin on a two segment version would have shown a phantom update badge.

`omarchy-pit-wall-entry` coloured the Formula 1 standings tables by team. Only the hue comes from the team. Saturation and lightness are fixed at the call site, so Ferrari reads as Ferrari without a hardcoded hex fighting whatever theme the user runs, and unknown or future teams fall through to a stable hue derived from the name instead of collapsing into a single default.

`omarchy-wait-state-entry` shipped a PSI monitor.

Per repo commit counts: omarchy-pit-wall-entry 8, omarchy-bazaar-entry 7, omarchy-crew-chief-entry 7, omarchy-x-files-entry 7, omarchy-listening-post-entry 6, omarchy-mlb-booth-entry 6, omarchy-docket-entry 6, omarchy-wait-state-entry 4, claude-code-plugins 4, omarchy-widget-template 2, contributing-clanker 1.

## Who did what

The `claude-code-plugins` work ran across seven sessions in two different CLIs: 456 turns, 677 tool calls, 27 errors hit, spanning 1397 minutes. `Claude Opus 5` ran the Claude Code side and carried the gate work and the coverage reporter design. `GPT-5.6 Sol` ran the Codex side, where it built the Wait State plugin and traced a governed-brain startup failure to a config pointing at a cached plugin version 1.1.2 that no longer existed on disk, with only 1.2.0 installed.

The part I did not plan is the one worth keeping. `GPT-5.6 Sol` spent its later sessions running the coverage reporter role that `Claude Opus 5` had authored earlier the same day, as an independent read-only audit, on a tree the authoring model had never seen. It stated the rule back before using it, that the denominator comes from the canonical lane and a skipped applicable check counts as unproven rather than pass, and then it returned a BLOCK on Wait State: install reality unproven, because the repository had no commits and no remote, so the documented clone URL could not be resolved. That is the UNPROVEN verdict doing exactly the job it was written for, on day one, in the hands of a model that did not write it. It also found the freshness checker could only discover canonical gates whose names were already in the local manifest, which is a coverage hole of precisely the kind the agent exists to name.

`Claude Fable 5` ran a short intent-os thread. `Claude Sonnet 5` was on the blog pipeline thread.

Zero operator course corrections that day, and that deserves one honest sentence rather than a victory lap. It was not a day of being redirected. It was a day of parallel repair on a defect shape that had already been named, which is the easiest kind of day to run unattended and tells you very little about how the system handles a novel problem.

The 27 errors were real and mostly environmental. A `shellcheck` lint job failed the L2 gate. The rig container answered `sh: line 4: python3: command not found`. QML threw `TypeError: Property 'spoolTruncated' of object [object Object] is not a function` while the census line was being wired in. A script call hit `bash: scripts/gen-changelog.sh: No such file or directory`. The headless rig was missing `swaybg`. Every one of those was loud. None of them is the category of failure this post is about, which is the quiet kind that reports success.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Every Check Should Report What It Did Not Look At",
  "description": "A status job that always runs reports which checks executed and which are unproven, so a skipped GitHub Actions job cannot read as a pass.",
  "datePublished": "2026-08-22T08:00:00-05:00",
  "author": { "@type": "Person", "name": "Jeremy Longshore" },
  "url": "https://startaitools.com/posts/the-lane-that-reviewed-nothing/",
  "isPartOf": { "@type": "Blog", "name": "Start AI Tools", "url": "https://startaitools.com" }
}
</script>

## Related Posts

[What a Skipped Check Is Worth in CI](https://startaitools.com/posts/the-skip-that-counted-as-a-pass/)

[We Told the Auditors to Refute Us](https://startaitools.com/posts/we-told-the-auditors-to-refute-us/)

[The Gate That Could Not Fail](https://startaitools.com/posts/the-gate-that-could-not-fail/)
