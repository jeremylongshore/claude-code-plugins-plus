---
title: "A Dead Socket Is Not a Dead Host"
description: "When two facts share one value, the signal cannot tell them apart. A socket race is not a host failure."
date: "2026-08-10"
tags: ["typescript", "debugging", "ci-cd", "release-engineering", "architecture", "devops"]
featured: false
canonical: "https://startaitools.com/posts/a-dead-socket-is-not-a-dead-host/"
---
## The measurement

Over 24 hours on the Braves production backend, the GUMBO poller failed 11,319 times. That is roughly 8 failures per minute, continuous, for a full day. It tripped the circuit breaker 186 times. The health endpoint reported `status: ok` the entire time, so nothing reached a human and the uptime monitor stayed green.

The poller runs every 5 seconds and requests timed out after 5 seconds. The three largest failure buckets:

- Terminated, other side closed: 8,002
- Circuit-open, which is a consequence rather than a cause: 2,232
- Timeout: 1,080

The defect was not a single thing. It was four things compounding, each one plausible in isolation, each one invisible when stacked. And the strangest part of the debugging was that the codebase had already diagnosed two of them: one in a comment predicting the exact race, one in a branch two lines from the bug making the exact distinction the bug failed to make. The answers were in the file. What follows is the order in which they turned up.

## Defect 1: A socket is not a host

Keep-alive connection pools race their peer by construction. You can pick a socket in the instant between the peer closing it and you noticing. When undici tries to reuse such a socket it reports `UND_ERR_SOCKET / "other side closed"`. That means the socket is dead, not the host, and the next request on a fresh connection succeeds.

Nothing retried. Worse, it counted toward the circuit breaker, and five stale sockets were enough to open the circuit for 60 seconds. So a benign race manufactured 2,232 additional real failures per day on top of the 8,002 it caused directly. Roughly a fifth of the day's failure count was the breaker reacting to a race that never needed to be a failure at all.

The fix is narrow: retry once on a fresh connection, exclude the race from the breaker, and stop.

The part worth sitting with is that the code already knew this distinction. The 4xx branch, two lines away, carries a comment saying "the host is up, the query is rejected". That is the same separation, already reasoned through, already written down. It was never extended one layer down to the socket. The category error was not an oversight in principle, it was an oversight in scope.

```typescript
// Excerpted from the poll error handler in http-client.ts, illustrative shape.

// Before: every socket death counted toward the breaker
async function handlePollErrorBefore(error: PollError) {
  if (error.code === "UND_ERR_SOCKET") {
    circuitBreaker.recordFailure(); // 8,002 times in 24h
  }
}

// After: a dead socket and a dead host are different facts
async function handlePollError(error: PollError) {
  if (error.code === "UND_ERR_SOCKET") {
    // The socket raced the peer. Try once on a fresh connection.
    const retried = await pollOnFreshConnection();
    if (retried.ok) return retried;
    // Only a failure on a FRESH connection says anything about the host.
    circuitBreaker.recordFailure();
  } else if (isTimeout(error) || is5xx(error)) {
    // Upstream is struggling. Never retry these. Record and move on.
    circuitBreaker.recordFailure();
  }
}
```

Why not retry on timeout or 5xx? Because re-issuing those is exactly what produced the 2026-07-17 storm. A timeout and a 5xx both say the upstream is already struggling, and the correct response to a struggling upstream is fewer requests, not more. A stale socket says something different: nothing is wrong upstream, our own pool handed us a corpse. Only the third case earns a retry, so only the third case gets one.

## Defect 2: The pool was tuned to maximize the race

ProxyAgent was constructed with no options, so undici's default `keepAliveTimeout` sat at 4 seconds, just under the 5-second poll interval. Every poll reused a socket that was idle right at the edge of expiry. We could have held sockets longer. Instead, we chose to close our side first.

We set `keepAliveTimeout` to 2 seconds, well below the poll interval. On paper that costs one CONNECT per poll. In practice the proxy log showed that CONNECT was already happening on nearly every poll, because the sockets were expiring anyway. So the tradeoff was cheap: we formalized a cost we were already paying, and in exchange correctness stopped depending on the peer's idle timeout, which we do not control.

## Defect 3: The poll could overlap itself

`setInterval` does not wait for the previous tick to finish, and the request timeout was 5000ms against a 5000ms interval. Any slow poll ran concurrently with its successor: two in-flight requests to the same upstream, each making the other likelier to time out. The old code had already called this shot. A comment in the file warned about the request timeout becoming "a 5s timeout that races the next poll tick". It sat there, correct and unactioned, while the race it described ran 8 times a minute.

We added a single-flight guard and dropped the timeout to 4000ms to give each poll headroom:

```typescript
const POLL_TIMEOUT_MS = 4000; // strictly below the 5000ms interval

let currentPoll: Promise<GameState> | null = null;

async function pollWithSingleFlight() {
  if (currentPoll) {
    return; // a poll is already in flight; skip this tick
  }
  try {
    currentPoll = fetchGameState({ timeout: POLL_TIMEOUT_MS });
    await currentPoll;
  } finally {
    currentPoll = null;
  }
}

setInterval(pollWithSingleFlight, 5000);
```

A skipped tick costs nothing here. The next poll arrives in at most 5 seconds, and GUMBO state does not change meaningfully inside one interval. Two concurrent polls, each degrading the other, cost plenty.

## Defect 4: Health could not report any of it

The health endpoint exposed a single boolean: `isStuck`, which only fires when `gameStatus === "In Progress"`. Between games, the poller could fail every single poll and health would still report ok. The signal was so under-specified that it could not represent the truth even in principle.

We rewired health to expose:

- `consecutivePollFailures` (number)
- `lastPollError` (string or null)
- `healthy` (boolean)

The `status` field now becomes `"degraded"` after 3 consecutive failures (roughly 15 seconds of darkness) or when stuck. A stopped poller between games is idle, not unhealthy, so `status` stays `"ok"` when gameStatus is not "In Progress".

Note what that last clause protects. A stopped poller is idle, not unhealthy. If the definition of degraded had been "the poller is not returning data", every night between games would page someone, and a monitor that cries wolf nightly gets muted inside a week. The enum has to distinguish not running from running badly, or the fix reintroduces the original problem from the other direction.

### The deploy contract changed, and that is the risky part

This is the piece worth flagging before copying any of it. `deploy.yml` runs a smoke validation of `.status == "ok"` after each deploy, and until now that assertion was decorative. It passed over 11,319 failed polls, because `status` was a constant. Making `status` honest silently gave that smoke test teeth it never had.

A deploy whose live feed cannot reach MLB will now fail smoke and roll back. That is intended, and it fails closed, which is the right direction: rollback restores the prior image. But it means a change to a health endpoint quietly altered deploy behavior, and an upstream outage at MLB can now block shipping unrelated frontend work. Off-hours deploys are unaffected, since an idle poller reports ok. I made that dependency on purpose and wrote it into the commit as a contract change, because the alternative was finding out during an incident that the smoke gate had grown a third-party dependency nobody chose.

## The same error in four more costumes

Defects 2 and 3 are ordinary tuning and concurrency bugs. They amplified the damage but they are not the interesting part. Defects 1 and 4 are, because neither is a monitoring gap. Nothing was missing. A value existed, it was being read, and it was under-specified: two genuinely different facts had been assigned the same representation, so the signal could not express the truth even in principle. Add another dashboard and you get the same wrong answer on a second screen.

The rest of the day, over on intent-os, was the same mistake in other places.

**Observed zero is not failed observation.** B4.1 is a per-repo CI and release status projection over 145 active repos. The bead asked, literally, for a repo with no CI to render as `unknown`. That is wrong, and shipping it as written would have poisoned the page. "I asked GitHub and it has run zero workflows" is a positive observation. "I asked GitHub and the call failed" is the absence of an observation. Both mean never green, which is the requirement's real substance, but they are not the same fact. The closed enum keeps `none` and `unknown` apart, and `unknown` always carries a reason. The live sweep came back 63/17/1/62/2: seventeen genuinely red repos rendering red, two genuinely unobservable ones rendering unknown with a reason attached.

The shape it produces is small. The enforcement lives in the `ci-release-status.v0` contract (a closed verdict enum, with `reason` required on `unknown`), and the point of it is that "we do not know" can never be written down as cheaply as "there is nothing here":

```json
{
  "repo": "intent-solutions-io/intent-os",
  "ci": { "verdict": "passing", "observed_at": "2026-08-10T05:40:12Z" },

  "//": "no CI runs exist. positively observed. never green, but not a failure to look.",
  "ci_none_example": { "verdict": "none", "observed_at": "2026-08-10T05:40:12Z" },

  "//2": "the observation itself failed. a reason is structurally required here.",
  "ci_unknown_example": {
    "verdict": "unknown",
    "reason": "gh api timeout after 20s",
    "observed_at": "2026-08-10T05:40:12Z"
  }
}
```

That `observed_at` is per class, not per document. Registry fields carry the registry's clock and the CI fields carry their own, because a fresh registry read tells you nothing about how stale the CI observation beside it is. Anything older than 48 hours is flagged loudly.

The renderer also refuses to emit a projection whose counts disagree with its own rows, so a doctored summary cannot quietly hide a red repo. A projection is never a source of truth, and the fastest way to forget that is to let it round off its own inconsistencies.

**A matching name is not a shared identity.** B4.2 joins the repo registry against the service inventory to produce blast-radius edges. The join is a name-match heuristic, and the entire design question is what to do with that fact. The answer was to report it rather than launder it: exact case-insensitive match only, ambiguity excluded and listed rather than resolved by guess, gaps counted on both sides, no fabricated identity written anywhere. First live run produced 26 edges, 68 bindings, and 5 real orphans (the vendored twenty stack). The orphan class had production examples on day one.

**A schema-valid document does not prove its endpoints exist.** This was the sharp finding out of four on that PR, and it is the one worth stealing. Every edge validated against `catalog-relationship.v0`. Every edge was also potentially pointing at nothing, because schema conformance says a field is well-formed, not that the thing it names is real. A slug-convention divergence between producer and catalog would have made the entire blast radius fictional, and no amount of schema validation could have noticed. The proof now asserts that every live edge endpoint actually resolves in the materialized catalog, same inventory, same run.

**A recorded rehearsal is not a re-executable one.** The settlement audit on B4.1 pulled the rollback receipt out of the shipped evidence bundle and found its caption mislabeled the executed command and cited the wrong base commit. Re-run as written, it did not work. The underlying claim was true, the rollback genuinely worked, and the artifact still failed to prove it. That is the category error applied to evidence itself: "I did this" and "here is something you can run to confirm I did this" had been collapsed into one document. It was regenerated verbatim against the real parent commit, captured output and all.

Every fix is the same move. Find the two facts sharing one value, name them separately, and make the system structurally incapable of rendering them as one.

## The collaboration beat

The intent-os work spanned three sessions, 178 turns, 560 tool calls, and 1003 minutes across Claude Fable 5 and Claude Opus 5. It opened with `/init` on an already-strong CLAUDE.md. Instead of rewriting, the model did a drift-repair audit. It checked every checkable claim and fixed six false ones. The most dangerous was a CI section still claiming a self-hosted dev-box runner when all four GitHub Actions jobs had run on ubuntu-latest since 2026-07-27. An agent following that text would reason about runner serialization and systemctl commands that no longer exist.

Then came a blunt voice-dictated steer, mid-session. The command was rough (voice-to-text had roughed it up), the instruction was not: finish the B3 synchronization spine before touching B4. Non-negotiable architecture: reconciliation is truth. Events are acceleration signals. A dropped, duplicated, delayed, or reordered event must never permanently make Mission Control wrong.

The model entered plan mode, dispatched three Explore agents and one Plan agent, wrote the plan, then executed it. The 26 errors along the way included Exit code 8, Exit code 128, a Traceback, a failed string replacement, and a harness block on a 45-second sleep (the instruction was to use Monitor with an until-loop instead). Each one was recovered in place.

On the Braves side, the useful moment was two poller tests going red after the single-flight guard landed. The tests were wrong, not the code. In `gumbo-poller.ts`, the poller's `start()` fires an unawaited poll immediately, so the hand-driven polls those tests injected were correctly skipped by the new guard. That is the failure mode you want from a guard, arriving disguised as a regression. The tests gained a `drain()` helper that waits for the in-flight poll before asserting, and went green.

The last check was the one easiest to skip. ProxyAgent's object form was verified live, constructed for real with a request through the home-server proxy returning 200, rather than trusted because `tsc` was clean. Typechecking proves a shape, not a behavior, which is the same distinction this entire post is about.

## Also shipped

Verified: 359 tests pass across 58 files. No TypeScript or ESLint errors. Refs #114, #115, #116, #118.

On intent-os: B3.5 (conflict/drift queue) and B3.6 (replay/dedup/missed-event recovery proof with drills for missing/delayed/reordered events) shipped the same day. Also: a fix for treating malformed prior snapshot as absent. A corrupted state file must never become a daily-sweep denial-of-service.

17 beads closed 2026-08-10. Notable: the estate-graph projection fallback was claiming verified health without ever querying the database, which is this post's thesis restated as a bug title. The Kilo review bot had been dead on every intent-os PR for 10 snapshots (its configured model no longer exists). The github_pat_intentsolutions_vps token in production SOPS returned 401 Bad credentials. An ungated download shipped to the partner portal because Caddy's PATH allow-list had not been updated for the new prefix. Each one a gap between "we checked this" and "this is actually true".

---

## Related Posts

[The Check That Only Confirmed a Name](https://startaitools.com/posts/the-check-that-only-confirmed-a-name/). A gate that validated the label instead of the thing behind it. The F2 finding here is the same shape.

[Nothing Read It, So Nothing Failed](https://startaitools.com/posts/nothing-read-it-so-nothing-failed/). What it costs when absence and success are indistinguishable to the consumer.

[The Ghost in the Catalog](https://startaitools.com/posts/the-ghost-in-the-catalog/). A record asserting work that never happened, then read downstream as truth. The same collapse, applied to provenance.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "A Dead Socket Is Not a Dead Host",
  "datePublished": "2026-08-10T08:00:00-05:00",
  "author": {
    "@type": "Person",
    "name": "Jeremy Longshore"
  },
  "url": "https://startaitools.com/posts/a-dead-socket-is-not-a-dead-host/"
}
</script>
