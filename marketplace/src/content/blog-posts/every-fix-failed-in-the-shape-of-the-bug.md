---
title: "Every Fix Failed in the Shape of the Bug It Fixed"
description: "An invariant guarded by adjacent checks is only as honest as the checks. Seven commits of corrections, then it moved into a schema that refuses the claim."
date: "2026-08-11"
tags: ["devops", "debugging", "architecture", "testing", "automation"]
featured: false
canonical: "https://startaitools.com/posts/every-fix-failed-in-the-shape-of-the-bug/"
---
The restore drill was right to fail and wrong about why.

It was newly added by `decision-log/050`, and the first snapshot it touched came back bad. It aborted with the loudest explanation it had: the seal has locked us out. The seal was fine. From a sample of one, a brand new verifier reached for the scariest failure mode in its vocabulary and published it as a finding.

That set the pattern for the whole day. Every fix I shipped after it failed in the shape of the bug it was fixing. A shorter timeout that more than tripled the timeouts. A correction that turned a right count into a wrong one. A verifier that manufactured the exact failure it existed to rule out. Each of those got repaired on its own terms, by measurement, not by architecture. What actually changed by the end of the day was where I was willing to put an invariant: not in a check sitting next to the thing, but in a schema that refuses to hold the false claim.

Seven commits and roughly 860 insertions in the intent-os backup fabric between 02:00 and 04:00. Most of what follows is me correcting me.

## The gate that passed every one of them

Off-estate snapshot custody had 43 retained snapshots. 17 of them could not be restored. The nightly health gate had passed every one of them.

Two commands, same snapshot, opposite answers:

```bash
# what the nightly gate ran, every night, and logged as "snapshot OK"
borg check --repository-only "$repo"
# -> exit 0

# what a restore actually needs
borg list "$repo"
# -> exit 2
```

`borg check --repository-only` validates the contents of the segments it finds. It never verifies that the transaction id recorded in the index has a segment sitting behind it. A repo missing its newest segments is internally consistent and completely unrestorable, and the gate reads that as healthy.

The second failure was an interlock that did not exist. Three scripts, three locks:

```
vps-borg-pull.sh        -> flock A
devbox-replica-pull.sh  -> flock B
repo-snapshot.sh        -> flock C   (unrelated to either)
```

Each one guarded against a second copy of itself and nothing else. So the snapshot job rsync'd a replica that a pull was actively rewriting, which is how you get a torn snapshot that opens cleanly enough to fool a content check.

Per repo, measured: VPS 20 of 24 restorable, dev box 6 of 19 restorable.

## The first fix would have skipped the leg entirely

To stop the race I made the snapshot wait for the pull's lock:

```bash
exec 7>"$PULL_LOCK"

if ! flock -w 1800 7; then
    log "pull in progress, giving up"
    return 10
fi
```

Thirty minutes. That number came from an "8 to 12 minute" pull figure that the same pull request had already corrected as wrong. Against measured reality, a snapshot job starting at 07:00 and giving up at 07:30 never gets the lock. Not sometimes. Any day.

I had traded torn snapshots for no snapshots, which is the worse of the two, because a torn snapshot at least exists to be caught.

## The correction that turned a right number into a wrong one

The first measurement said 17 of 43 unrestorable. That was correct. A later three-predicate scan returned 14 dev-box REJECTs, I read REJECT as "unrestorable," and published 18 of 43 as a correction. Then I edited the in-script comment away from the right value to match the wrong one.

The gate refuses on three grounds and only one of them is unreadability. Dev-box snapshot `2026-08-05T0704` carries rsync transfer debris and opens perfectly well in borg. Two measures of similar magnitude, conflated:

```
                 total   borg-list UNREADABLE   has-debris
vps                 24                      4            4
devbox              19                     13           14

17 of 43 UNRESTORABLE   (the damage)
18 of 43 REFUSED        (by the new gate, strictly larger, correctly so)
```

Debris proves the source was not quiescent even when the repo still opens, so refusing more than 17 is the right behavior. It is just a different number with a different meaning, and I published it under the first one's name.

The cleanup after that was a sweep of every "N of 43", "N of 19" and "all N" claim across `repo-snapshot.sh`, `home-server-custody-check.sh`, the home-server README, `000-docs/154`, the index and the CHANGELOG. `pnpm check` clean over 532 markdown files, shellcheck clean at warning level.

The part that stings: the entire thesis of that pull request is that adjacent checks lie to each other. It shipped with a second source of truth sitting next to the code, disagreeing with the record.

## The verifier that manufactured its own failure

The same class of bug was still sitting in ACCEPTANCE 2 of `bootstrap-root-custody.sh`, which is the worst possible place for it. That walk iterates snapshots newest-first looking for one that lists.

Every snapshot in a root carries the same borg repo id. With one shared cache, the newest iteration poisons every later one with "Cache is newer than repository." Measured over the 8 newest snapshots:

```
SHARED cache, newest-first   ->  1 listable,  7 failed
FRESH cache per call         ->  4 listable,  4 failed   <- the true state
```

Half the failures were the walk's own cache. Had it run out of listable candidates, the drill would have reported that no sealed snapshot could be listed, aborted the bootstrap, and blamed the seal. That is precisely the misdiagnosis this walk was rewritten to prevent, in the one test whose entire job is telling a seal problem apart from a torn snapshot.

A verifier that manufactures the failure it is checking for is worse than no verifier, because its output looks like a finding.

## The measurement with no receipt

The whole scheduling redesign rested on one number, and that number had no evidence file behind it. Evidence 00 was titled "pull duration vs the gap before the snapshot" and captured `tail -4` of the log, so it showed nothing but short pulls. That is exactly how the original "8 to 12 minute" figure got made in the first place.

Evidence 06 pairs every start with its finish across the full log:

```
2026-08-06  06:47:01 -> 11:14:31   4h27m   snapshot ran mid-pull  -> torn
2026-08-07  06:47:01 -> 08:17:43   1h30m   snapshot ran mid-pull  -> torn
2026-08-08  06:47:01 -> FAILED        --   snapshot copied debris -> torn

dev box: 88 starts / 76 ok / 12 FAILED
VPS:    118 starts / 108 ok / 10 FAILED
```

Pull duration runs from about 3 minutes to about 4.5 hours and grows with the repo.

## Why not the obvious fix

Three decisions on this day went against the first thing that came to mind. The reasoning is worth more than the code.

**Opportunistic retry, not a longer timeout.** The obvious repair for `flock -w 1800` is `flock -w 5400`. I did not do that, because a longer timeout is the same guess with a bigger number. A fixed start time plus a fixed timeout is unwinnable when the thing you are waiting on spans two orders of magnitude and grows. Any constant chosen today is a guess with an expiry date, and the 07:00 cron was exactly that guess, made when the repo was smaller. The lock is now non-blocking, a held lock returns 0 and skips, and the timer fires every 2 hours.

**Fresh cache per call, not walking oldest-first.** Oldest-first also dodges the poisoning, and it was tempting because it is a one-word change. It hides the hazard rather than removing it, and it tests the least interesting snapshots.

**Pairing start to finish, not quoting a log tail.** The tail is what lied twice already. It is biased toward whatever ran most recently, and the recent pulls happen to be fast. Pairing every start with its outcome makes the distribution visible instead of the last sample.

## The same shape, a different repo

Afternoon, `scorecardecho.com`, the MLB GUMBO poller. Yesterday's known-issues entry had it at 11,319 failed polls in 24 hours behind a green health check.

I shipped a fix, then had to fix the fix. A timing-out poll was overlapping the next tick, so I cut the poll ceiling from 5000ms to 4000ms. The overlap was a real bug. Shortening the timeout was the wrong repair for it, and it regressed the failure mode it was meant to help. Production, steady state, cold start excluded:

```
5000ms ceiling : ~0.75 timeouts/min   (1,080 in 24h)
4000ms ceiling : ~2.6  timeouts/min   (13 in 5 min)
```

Direct latency sampling of the real GUMBO call through the residential proxy explains it exactly: median 1.69s, p90 4.91s, max 7.49s, with 25% of samples over 4 seconds. I had set the ceiling below the p90 of the call I was calling. The ceiling is now 8s, with 0 of 20 samples over.

Four compounding defects total. 8,002 stale-socket errors and 186 breaker trips a day, both now 0.

What is not proven: the poller latches onto a game at first pitch, so everything above was verified in Pre-Game and by direct sampling. The first in-game window is the remaining proof. I nearly reported "0 failures in 5 minutes" as success when it was 0 polls, because the poller was idle. Two items stay open: `sportstalk_atl` 403s, and a cold-start burst that trips the breaker once per deploy.

## None of these corrections were self-generated

This is the part a git log cannot show. I did not catch most of this.

- Both MiniMax reviewer lanes flagged the superseded counts in the in-script comment.
- The MiniMax defect lane caught the `flock -w 1800` bug, which was worse than the one being fixed.
- The adversarial lane did the arithmetic on a gap I had written down as 13 minutes: 06:47 to a 07:06 snapshot is 19.
- The defect lane pointed out that the load-bearing 4h27m measurement had no receipt.
- On the intent-os side, a round-2 adversarial review caught a miscount in the capability matrix, which reported five sourceless capabilities where there were six.

Reviewers produce noise too, and pretending otherwise would be its own kind of lying. One review run flagged a torn-snapshot block that an earlier commit had already fixed. That part was stale, not a live defect. The line next to it was live. You still have to read every finding.

The day ran on Claude Opus 5 for most of the work, with Claude Fable 5, Claude Opus 4.8 and Claude Sonnet 5 in smaller sessions, plus 57 subagent transcripts (one intent-os session spawned nine or more).

## The turn: put the invariant in the schema

The same day shipped three vertical slices in intent-os where the invariant does not live in a check next to the data. It lives in a versioned JSON Schema contract that will not validate a document making the false claim.

- **`deployment-state.v0`** (#453). A failed deploy workflow paired with a non-failure repo state is a schema rejection. The choice on the record: schema-encoding the never-stale-green rule over renderer-only enforcement, because the proof's teeth then show that a doctored collector cannot even write the lie.
- **`health-projection.v0`** (#458). A conditional rejects any document where a non-running container claims healthy. The alarm-to-service mapping is a stated heuristic carried in every projection's `provenance.mapping_basis`, reported rather than silently assumed. The run proof statically asserts that no query-API path exists in the collector.
- **`estate-capability-matrix.v0`** (#462). The D167 truth table as a slice, with 1 valid and 4 invalid fixtures. It composes the settled projections and collects nothing itself (statically asserted: no network or ssh in `compose.py`). Health is capability health, never data greenness, and sourceless live rows render unknown loudly.

Each slice carries its seeded drill as a schema rejection, invalid fixtures, and a run proof. That is the structural answer to a day of adjacent checks lying to each other: the check can be blinded, the renderer can be doctored, the comment can drift, but the document either validates or it does not.

I want to be careful about how far that claim reaches. Those three slices are clean execution and nothing in them broke. They are not vindicated yet. One approach is being tried against a problem the other approach kept losing to, and that is all today proves.

The audit that closed the matrix slice is a fair warning about how much ceremony this costs. `mc-evidence-auditor` refused it because the round that caught the five-versus-six miscount was missing from the "every round disposed" log, and the count fix had landed in the CHANGELOG but not in the pull request body or the bead note. A fix that lands in one copy of a claim while other copies keep the wrong number is the exact failure the audit exists to catch, and it was the second instance of that pattern in one day. Note where that one happened: in the prose describing the schema slice, not in the schema itself.

## What I would do differently

Not "test more." Every one of these had a test. The gate ran nightly, the drill was purpose-built, the timeout was chosen from a measurement, the correction was made from a scan.

The transferable rule is narrower: a check that sits next to the thing it checks shares its blind spots and its state. The nightly gate shared borg's idea of consistency. The drill shared a cache with the thing it was measuring. The in-script comment shared a file with the code and drifted from the record.

The timeout belongs to a neighboring category worth naming separately, because it is the one I keep miscategorizing. It shared no state with anything. It inherited a number from a measurement the same change had already retracted, which is how a constant outlives the evidence that produced it.

When the invariant moves into an artifact that has to validate independently, none of that sharing is available to it. The document either validates or it does not, and no adjacent comment gets a vote.

That is not a claim that schemas are self-correcting. I did not catch most of the corrections above, a reviewer did, and the one drift that did land on the schema side landed in prose that a reviewer still had to read. A contract has to be written correctly by someone first. What it removes is the option of the code and the record quietly disagreeing about what is true.

## Also shipped

- Extended the Carter gate to `/downloads/` after it served a file anonymously, and corrected a stale username in the same config.
- Added a CLAUDE.md to partner-portals recording the same ingress trap that published an ungated file.
- Repaired the wrapped updater lane, which had never been able to run on either host.
- Repaired six stale claims found by an `/init` audit, spanning hosted CI, the grown gate suite, and undocumented directories.
- Restored chronological order in a log after a rebase put an 08-09 entry above an 08-11 one.
- Forwarded `learn.` access requests to the owner's inbox, because the Slack ping had been silently dead.
- diagnostic-pro backlog from 14 open to 5, after checking each one against reality rather than closing on vibes.
- claude-code-plugins untracked 42M of archived inventory snapshots while preserving five cited governance records that had never been tracked.

## Related Posts

- [The Drills Passed. Reality Did Not.](https://startaitools.com/posts/the-drills-passed-reality-did-not/)
- [Nothing Read It, So Nothing Failed](https://startaitools.com/posts/nothing-read-it-so-nothing-failed/)
- [A Dead Socket Is Not a Dead Host](https://startaitools.com/posts/a-dead-socket-is-not-a-dead-host/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Every Fix Failed in the Shape of the Bug It Fixed",
  "description": "An invariant guarded by adjacent checks is only as honest as the checks. Seven commits of corrections, then it moved into a schema that refuses the claim.",
  "author": { "@type": "Person", "name": "Jeremy Longshore" },
  "publisher": { "@type": "Organization", "name": "Start AI Tools", "url": "https://startaitools.com/" },
  "datePublished": "2026-08-11T10:00:00-06:00",
  "mainEntityOfPage": { "@type": "WebPage", "@id": "https://startaitools.com/posts/every-fix-failed-in-the-shape-of-the-bug/" },
  "url": "https://startaitools.com/posts/every-fix-failed-in-the-shape-of-the-bug/",
  "articleSection": "Technical Deep-Dive",
  "keywords": "borg check, borg list, torn snapshot, backup verification, flock, restore drill, JSON Schema contract, timeout tuning, devops, debugging"
}
</script>
