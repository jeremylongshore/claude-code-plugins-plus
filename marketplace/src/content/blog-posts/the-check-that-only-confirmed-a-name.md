---
title: "The Check That Only Confirmed a Name"
description: "A default transport that only ever failed sent 2-5 fake outage emails an hour while the relay was healthy. Four checks that confirmed a name instead of a fact."
date: "2026-08-03"
tags: ["debugging", "ci-cd", "devops", "observability", "automation"]
featured: false
canonical: "https://startaitools.com/posts/the-check-that-only-confirmed-a-name/"
---
The owner had already asked for the alert emails to stop. A fix shipped. Then another email landed. Then another.

"ong it just ssent me abother email," he said, voice-dictated, unedited. Fifteen minutes later: "go another one."

The system was reporting an outage that did not exist.

## The Transport That Only Ever Failed

A 14-PR merge train had just moved every cron producer's alerting off shared email and onto Buzz, a Nostr-relay team chat. One producer per PR, each with its own liveness contract and a bead receipt. It shipped cleanly. But the library backing those producers carried a default that had only one job: fail.

```bash
AF_BUZZ_CMD="${AF_BUZZ_CMD:-af_default_buzz_post}"
```

`af_default_buzz_post` returned 1 with "no Buzz transport injected". Every caller that sourced the library (which is every cron producer) exhausted its Buzz retries and fell through to the email floor. The system reported a false Buzz outage while the relay was healthy. It did this 2 to 5 times per hour.

Evidence arrived in the logs: 581 dedup markers, a steady stream of "[INTENT ALERT FLOOR: Buzz unreachable]" emails, and `sweep.log` showing `buzz=ok` only for the handful of callers invoked through the CLI entrypoint rather than by sourcing the library. That asymmetry was the bug. The CLI had a one-line fixup swapping in the real transport, annotated in a comment as "the library path is unchanged". The library path did not, and the cron producers all take the library path.

The fix promoted the real transport to the default for both seams. `af_buzz_transport` already discovers the installed `buzz-notify.sh` and already fails closed when it is genuinely missing. The dead CLI fixup was deleted. Fail-closed behavior survives, but now it is conditional on genuine absence rather than on every caller remembering to opt in.

Why not migrate callers one at a time? Because the per-caller route leaves the next new producer to rediscover this the same way. Flipping the default fixes the class, not the instance.

### The Fix Exposed a Second Bug It Had Been Masking

Turning the email floor off by default (now `AF_EMAIL_FLOOR=1` is required to opt in) exposed a real bug in `af_buzz_transport`. It ran transport discovery before the `AF_DRY_RUN` short-circuit, so any caller with a sandboxed `HOME` failed discovery and fell to the floor even in a dry run. The old stub had masked this by returning 0 in dry-run mode.

Promoting the real transport to the default is what surfaced it, and it broke five deterministic-ops lifecycle and drill tests whose notifier sets HOME to a temp state dir. A dry run sends nothing and must not require a real binary to exist, so the short-circuit now comes first.

The break was confirmed to be self-inflicted by stashing the change and re-running the gate at HEAD (0 failures), rather than assuming. The five assertions encoding the old always-on contract were updated deliberately, not bulldozed, pinning the mechanism explicitly with `AF_EMAIL_FLOOR=1`. A new combined test proves the default behavior: same simulated outage, no email, still spooled, dead-man's-switch still fired, receipt never claims delivered. Final state: alert-floor suite 103 passed, 0 failed.

Nothing is silently dropped when the email floor is off. `af_dispatch` still fires the external dead-man's-switch, still writes to the durable spool, and reports status honestly rather than claiming a delivery. Proven live with Buzz forced down:

```text
af_email_floor: disabled (AF_EMAIL_FLOOR!=1)
status=degraded buzz=fail email=fail hc=ok spooled=1
```

The accepted trade: no push notification during a genuine Buzz outage, with the dead-man's-switch keeping that externally observable rather than silent.

## The Gate That Was Gitignored

`.gitignore` line 76 in bobs-big-brain-registrar held a pattern that covered all eval artifacts wholesale, with specific un-ignore lines committed for the ones the repository is supposed to track. A new dense-retrieval floor was added to that directory without an un-ignore line. The file existed in the worktree that measured it. Tracked nowhere.

The nightly eval runs against a dedicated checkout pinned to origin/main. With the floor untracked, that checkout finds no floor file, takes the warn-and-continue branch, and reports ANCHOR PASS on the fused floor alone. Forever. Production would serve dense retrieval while nothing gated it.

The absence of a check is indistinguishable from a passing check unless something makes it loud. The warn branch would have fired every night on a machine nobody reads. No alert, no escalation, no discovery.

Caught by running `git check-ignore` before pushing rather than trusting that a file on disk is a file in the repo.

## The Severity Floor That Would Have Silenced Real Outages

With `AF_MIN_SEVERITY` defaulting to `high`, only high/urgent/critical/security reach a human. But `buzz_post` hardcoded severity `info` for all thirteen of its callers. The floor would have silently swallowed real trouble alongside the routine traffic it was meant to quiet: a Claude API outage posted to sys-incidents by `anthropic-status-monitor.sh` (every 5 minutes), a "teamkb-compile FAILED", census enforcement firing on a deadline, domain expiry from `registrar-expiry-monitor.sh`, automation-registry drift. Every one would have been recorded as `below_threshold` and never seen.

Caught before it shipped. The signature gained a third argument:

```text
buzz_post <text> [topic] [severity]
```

The default stays `info` deliberately, so content feeds stay quiet subscriptions rather than pings. Callers reporting a failure, outage, or deadline pass `high` explicitly, with the contract documented at the function so a future call site reporting something broken without a severity is a visible mistake rather than a silent one.

Why not raise the default to `high`? It would restore the exact per-minute drumbeat the floor exists to stop. Why not drop the floor? Routine traffic pinging the owner was the original complaint.

A suppressed event gets its own honest status, `below_threshold`. It does not claim delivery, does not fire the dead-man's-switch, does not spool as undelivered, and does not consume the dedup or rate budget, so the same condition escalating later is unaffected.

The rate limits themselves were a single global bucket allowing 20 alerts per 60 seconds (no practical limit, wrongly shared) that let a chatty producer burn an unrelated quiet one's budget. With `scorecardecho-uptime-monitor.sh` on `* * * * *`, a flapping endpoint could ping every minute indefinitely. Now one bucket per producer plus topic, at 3 per 15 minutes. The hard rule is untouched: urgent, security, and critical are never limited away, so this cannot hide an emergency.

## The Dated Evidence Record That Refused Rewriting

A per-caller opt-in for the severity floor was first added to `ops/deterministic-ops/{notifier,live_observer}.py` and then reverted, because `live_observer.py`'s file hash is bound into a dated evidence record (`live-runbook-resolution-residual-2026-07-16.json`). Editing the file drifted that binding, and the only way forward would have been re-stamping the record, quietly changing what a past live observation attests. The choice: a library-level dry-run exemption over rewriting dated evidence, because the audit trail is worth more than the convenience.

## The Alert Cards Themselves

Quieting the channel only helps if what survives is readable. The model contract for rendering an alert was one sentence, max 32 words: a headline that said something broke but never what it meant or what to do. Replaced with a three-line briefing (What happened / What it means / Action) written for a reader with no context, plus a jargon glossary ("no heartbeat" becomes "never reported in").

Two bounds worth stating: `Action` is bounded, so the model may never invent a command, a path, or a person. And `Where` is code-generated from `AF_SOURCE`, never written by the model, because estate ownership is not machine-readable. All 3,693 inventory records read `jeremylongshore (admin/operator)`, so a named human in an alert would be a fabrication. The digestion step runs through MiniMax M3, with the deterministic subject line kept as the fallback.

That last bound is the same discipline as the rest of the day, pointed at a model instead of a check. A field that looks authoritative because something filled it in is worth no more than a gate that passes because a file exists.

## Refusing a Verdict Instead of Rendering a Wrong One

Same frozen snapshot, same prebuilt index, measured 2026-08-02:

```text
semantic Recall@10   0.9643   idle box
semantic Recall@10   0.7679   under load 9.5 on 8 cores
```

Zero errors logged. Contention pushed single queries to 25.8 seconds against a 30-second ceiling; queries that crossed it hit `catch { return []; }` in `denseSearch`, contributed no dense candidates, and were scored as genuine misses. In serving, silent fail-open is correct. In measurement, it is wrong. The same code path was doing both.

Fix: an optional `dense.onQueryDegraded` observer fired whenever a query's dense arm fails open (embed failure, timeout, missing vector). Serving leaves it unset. The eval harness sets it, raises its offline embed timeout from 30 seconds to 300 seconds, and returns null when any query degraded, skipping the floor rather than scoring the run. The floor those numbers feed is an overall 0.9762 (lexical 1.0, semantic 0.9643). Committing it against a degraded run would have shipped a flaky gate: red on a busy box, not on a regression. A gate that cries wolf gets ignored. Better to render no verdict than a wrong one.

The negative-control run (floor temporarily raised to prove the gate fails) had overwritten the tracked artifact with its degraded numbers, which were then committed alongside a floor derived from the clean run. The repo contained an artifact contradicting the floor derived from it, with nothing in the file explaining why. Fixed by restoring the clean measurement and adding `degraded`, `degradedQueryCount`, and `degradedReasonSample` so the artifact is self-evidencing. The verbatim reflection: "I called the artifact self-evidencing in the PR body; it wasn't, and now it is."

## The Same Defect, Three More Times

The next three instances all came out of one sequential audit of a single repository, the claude-code-plugins marketplace site that publishes tonsofskills.com. That is worth saying plainly, because it is what a day spent auditing gates produces rather than a spooky coincidence. Three findings from one codebase is a thorough sweep, not four independent systems converging.

**The og:image that never existed.** BaseLayout sets `image = "/og-image.png"` on every page. The site built and published 3,830 pages advertising that URL. `git log --all -- marketplace/public/og-image.png` returned nothing. The file was never committed. Every link preview on X, LinkedIn, Slack, Discord rendered without an image for the entire life of the site.

**Then the gate for it checked only a filename.** The new `--check` mode passed if the PNG merely existed. But a stale PNG, a corrupted file, an incorrectly sized image, or something unrelated entirely would keep the gate green. The fix validates the PNG signature and IHDR chunk, asserts 1200x630 dimensions, and rejects anything under 5 KB. The header read and the assertions:

```javascript
import fs from 'node:fs';

const fd = fs.openSync(pngPath, 'r');
const buffer = Buffer.alloc(24);
fs.readSync(fd, buffer, 0, 24, 0);
fs.closeSync(fd);

if (!buffer.subarray(0, 8).equals(Buffer.from('\x89PNG\r\n\x1a\n', 'binary'))) {
  return false;
}
const width = buffer.readUInt32BE(16);
const height = buffer.readUInt32BE(20);
if (width !== 1200 || height !== 630) return false;
if (fs.statSync(pngPath).size < 5 * 1024) return false;
```

Reading the dimensions straight from the IHDR chunk (an 8-byte signature, an 8-byte chunk header, then two big-endian uint32s) avoids pulling in an image library, and parsing the header doubles as the format check.

A check that confirms a filename rather than its contents gives the appearance of coverage, which is exactly how the missing og:image survived unnoticed.

**And the security headers were meta tags.** A grep of the source would find `<meta http-equiv="X-Frame-Options">` and conclude the site was protected. Browsers ignore those tags entirely. The header was never sent.

The fix does a HEAD request against the live site and asserts the real response headers. A control is only real if verified at the layer that enforces it.

## The Umbrella Remedy: A System Graph With a Sync Gate

bobs-big-brain-umbrella gained `system-graph.yml`, a YAML model of the estate's nodes and edges (depends-on, reads, writes, invokes, gates) across roughly 50 curated nodes spanning engines, serving, data, gates, schedules, coordination. Every edge carries evidence. Edges are tiered derived (mechanically re-checkable) versus semantic (hand-curated invariant naming the guard that enforces it, rendered dotted).

`scripts/render-system-graph.py` validates the model, renders into the doc's AUTOGEN block, sync-checks in CI, and with `--check-local` re-verifies box reality: systemd units, crontab lines, paths. The CI workflow is the architectural fitness function: any PR where doc and model drift apart fails.

This estate's maps rot invisibly when nothing diffs them. The gitignored dense floor and an earlier eval detector that sat quietly skipped for six days were both reality-vs-map drift, where the documentation asserted a guard the box was not running. A YAML model with a sync gate cannot drift that way silently.

The graph immediately caught its own bad claim: it asserted the eval's reproducibility root was in no backup tier. Investigation disproved the strong form (the dev-box borg includes `/home/jeremy` wholesale with no `.teamkb` exclude, replicating to the VPS and then to append-only home-server snapshots). The honest residual is narrower and now stated exactly: the eval anchor is absent from the brain-scoped backup, so the brain restore runbook alone would not restore it.

## Also Shipped

bobs-big-brain-compiler made MiniMax M3 deterministically usable, stripping inline `<think>` blocks and pricing correctly. coastal-realty-ops fixed HEAD requests returning 500 on every dashboard route. The Buzz fork auto-joins invited members and bumped nine RUSTSEC advisories in nostr dependencies.

In the same claude-code-plugins marketplace, the 84 remaining Astro meta-refresh redirect entries became real HTTP 301s served by Caddy. The prior day's 404 repair had taken the site from 3 to 85 instant-redirect pages in a single deploy, and hours later a consumer network-security filter began blocking the domain. Causation was explicitly not claimed: Google Safe Browsing reported the domain clean throughout, and the filter has a known false-positive rate. But a mass of instant meta-refresh pages is the textbook doorway-page signature those heuristics look for, and a permanent redirect belongs in the HTTP status line rather than in markup a crawler has to execute. Better on every axis independent of the block.

## What the Four Have in Common

Line them up and the shape is the same every time. A name was bound, and nobody asked what was behind it.

`AF_BUZZ_CMD` was set, so a transport was configured. The thing it named only ever returned 1. The eval looked for a dense floor file, found no file, and read the absence as a pass. Every page carried `image = "/og-image.png"`, so the site had a social card. The URL 404'd for the life of the site. The source contained `<meta http-equiv="X-Frame-Options">`, so the site was protected. Browsers ignore that tag and the header was never sent.

Four times, something confirmed that a name existed and reported it as a working fact. None of them broke a build. None of them failed a test. Three of the four were found only because somebody went looking on a day set aside for looking, and the fourth was found because the owner kept getting emails and said so out loud.

That is the uncomfortable part. The defect is not that these checks were wrong. It is that a check confirming a name and a check confirming a fact produce identical output when they pass, so the weaker one is invisible until the day it matters. The og-image gate demonstrated it twice in one afternoon: it was written to catch exactly this failure, and its first version passed on a filename.

The fixes that stuck all moved the assertion closer to the thing being asserted. Read the response headers instead of the source. Parse the IHDR chunk instead of the file name. Verify the file is in the repository instead of on the disk. Refuse a verdict when the measurement was degraded instead of scoring the noise. None of that is clever. It is just the difference between asking whether something is named and asking whether it is true.

## Related Posts

- [The Drills Passed. Reality Did Not.](https://startaitools.com/posts/the-drills-passed-reality-did-not/)
- [The Ghost in the Catalog](https://startaitools.com/posts/the-ghost-in-the-catalog/)
- [The Version Number That Only Existed on the Client](https://startaitools.com/posts/the-version-number-that-only-existed-on-the-client/)
