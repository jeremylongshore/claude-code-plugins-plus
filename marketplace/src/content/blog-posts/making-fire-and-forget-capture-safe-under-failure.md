---
title: "Making a Fire-and-Forget Writer Safe Under Failure"
description: "Five properties an unattended capture hook needs before you turn it on: idempotent intake, durable outbox, backpressure, atomic receipts, consent gate."
date: "2026-07-11"
tags: ["architecture", "idempotency", "ai-agents", "claude-code", "distributed-systems"]
featured: false
---
There is a hook that distills a finished Claude Code session into a few durable learnings and proposes them to a shared team brain. It runs on `SessionEnd`. Nobody watches it. That last sentence is the entire problem.

The manual counterpart — a `/brain-save` command a teammate types when they want to keep something — has been safe for months. Not because the write path was safe, but because a human was standing over it. A human notices when a capture fails. A human doesn't hit save twice in a panic. A human sees the error toast and shrugs. The forgiving hands were attached to a person, and the person was the safety system.

An unattended hook has no hands. It fires when the session ends, whether or not the network is up, whether or not the same session already fired, whether or not one teammate's token has gone berserk. So the hook could not ship until the write path underneath it earned five properties. Skip any one and "convenient automation" becomes silent data loss, a duplicate flood, or governance drift nobody can see. Here is each property, why the obvious version of it was wrong, and the fifth one that governs the on-switch itself.

## The five properties

Before an unattended capture hook is safe to turn on, its write path needs all five:

1. **Idempotent intake** — retries collapse into a single record, never a duplicate flood.
2. **Durable outbox** — a network blip queues the write instead of losing it.
3. **Per-actor backpressure** — one runaway identity can't flood the queue.
4. **Atomic governance receipts** — a state flip and its audit record commit together or not at all.
5. **Consent-gated opt-in** — the on-switch stays a deliberate human decision.

## Property 1 — Idempotent intake

A retry must not fan out into duplicates. This has two halves, because the client and the server can each betray you.

The client half was the id. Team mode was minting candidate ids with `randomUUID()`. A re-send — a flaky network retry, a hook that fires twice, a drained backlog item going back out — arrived as a brand-new row every time. The fix is to make the id a pure function of the content:

```ts
import { createHash } from "node:crypto";

// UUIDv5 over (tenant, title, content) — same input, same id, forever.
function deriveCandidateId(tenant: string, title: string, content: string): string {
  const NS = "6ba7b810-9dad-11d1-80b4-00c04fd430c8"; // DNS namespace
  const hash = createHash("sha1")
    .update(Buffer.from(NS.replace(/-/g, ""), "hex"))
    .update(`${tenant}\n${title}\n${content}`)
    .digest();
  hash[6] = (hash[6] & 0x0f) | 0x50; // version 5
  hash[8] = (hash[8] & 0x3f) | 0x80; // RFC 4122 variant
  const h = hash.toString("hex");
  return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20,32)}`;
}
```

Deriving from `node:crypto` SHA-1 keeps team mode dependency-free — no `uuid` package pulled in for one function. The handler was extracted into an exported `capture()` alongside `deriveCandidateId`, `outboxDir`, and `drainOutbox`, so the whole path is unit-testable instead of buried in a request handler.

The server half is the guard behind the id. `CandidateService.intake` now calls `findByContentHashAndTenant(contentHash, tenantId)` before it inserts. On a hit it returns the existing candidate and skips writing a second `proposed` receipt, instead of inserting a duplicate row. The id and the server's content hash are two layers, not one key: the UUIDv5 guarantees a *retry* re-sends the byte-identical row, while the tenant-scoped content-hash lookup is the server's own backstop, collapsing same-content proposals within a tenant even if two ids ever diverged. The id dedups retries; the hash dedups content.

Why not reuse the repo's existing `findByContentHash`? Because that one is cross-tenant — `WHERE content_hash = ? LIMIT 1`, no tenant clause. Dedup against it and tenant A's re-send matches tenant B's identical row, leaking cross-tenant state and deduping to the wrong record. The new lookup is tenant-scoped on purpose. The behavior change is intended and narrow: a same-content re-send **within** a tenant returns the existing candidate (201); identical content across two tenants stays two independent rows. The old test that asserted "POST accepts duplicate candidates" was rewritten to assert the new idempotent contract. store 224 and api 323 tests pass.

## Property 2 — A durable outbox

A network blip must not silently lose the write. Team mode had no spool fallback. Local mode already wrote to a spool via `writeToSpool`; team mode, under an unattended hook, would throw on a dropped connection and the capture would evaporate. That was the one true "captures lost" blocker — a hard prerequisite for turning the hook on.

Now a `fetch` throw or a 5xx queues the candidate to a flat `~/.teamkb-outbox/` directory (mode 700, override with `TEAMKB_OUTBOX_DIR`) and reports `queued` rather than an error. The next successful capture drains the backlog:

```ts
async function capture(candidate) {
  try {
    const res = await postCandidate(candidate);
    if (res.status >= 500) return queue(candidate, "server-5xx");
    if (!res.ok) throw new HttpError(res.status);   // 4xx: real rejection, surface it
    await drainOutbox();                             // success → flush the backlog
    return res.json();
  } catch (err) {
    if (err instanceof HttpError && err.status < 500) throw err; // never queue a 4xx
    return queue(candidate, "network");             // throw / 5xx → durable spool
  }
}
```

The direction of the split is the whole design. A 5xx or a thrown socket is transient — keep it and retry. A 4xx is a real validation, auth, or disclosure rejection — queuing it would loop forever against a request that will never be accepted, so it is surfaced immediately. Drop-on-4xx, keep-on-5xx. A permanently-invalid item can never wedge the outbox, and a transient outage never loses a capture.

The two properties compose because of the id. Since the queued row carries its UUIDv5, the drain re-sends the *exact same* row — same id — and Property 1's server guard collapses it back to one candidate. The outbox can retry as aggressively as it likes and never manufactures a near-duplicate. Six new tests in `remote-server.test.ts` pin it down: id determinism and format, same-id-on-retry, outbox-on-throw, queue-on-5xx-not-4xx, drain-on-next-success, drain-stops-while-down. Full suite: 69 pass.

## Property 3 — Per-actor backpressure

One runaway identity must not flood the queue. A new capture-quota middleware — an `onRequest` hook registered after auth on the intake path — caps how many candidates a single token identity (`request.actor`) may POST to `/api/candidates` per window. Default 60 per 60s, tunable via `captureQuotaMax` and `captureQuotaWindowMs`. Intake only; promote and reject stay admin-gated and uncapped; reads are untouched.

The obvious answer is "there's already a rate limiter, use that." The existing limiter is per-source-IP, and on a tailnet that is worthless. Every teammate device is its own `100.x` address, so a per-IP cap gives every token effectively its own private quota — there was no real per-token limit at all. One compromised token, one runaway loop, or one over-eager auto-capture hook could bury the inbox, and the only tripwire was a DB-size canary that doesn't warn until 200 rows.

```ts
app.addHook("onRequest", async (req, reply) => {
  if (req.method !== "POST" || req.url !== "/api/candidates") return;
  const key = req.actor;                         // follows the TOKEN, not the IP
  const now = Date.now();
  const bucket = quota.get(key)?.filter(t => now - t < windowMs) ?? [];
  if (bucket.length >= max) return reply.code(429).send({ error: "capture quota" });
  bucket.push(now);
  quota.set(key, bucket);
});
```

Making the limit follow the token instead of the network address is the fix. The test proves the (N+1)th intake gets a 429 while reads and other paths never touch the counter.

## Property 4 — Atomic governance receipts

A state flip and its audit record must commit together or not at all. The nightly auto-govern sweep writes a single batch `governed` receipt covering the candidates it processes. Some of those flips — `quarantine` and `duplicate` — have no individual receipt; the batch event is the *only* on-chain record they exist. And they were autocommitting inside the loop, while the batch receipt got inserted afterward in a try/catch that logged to stderr on failure.

Walk that failure through. The loop flips a candidate to `quarantine` and commits. The batch receipt insert throws. The catch logs a line to stderr. Now the candidate is out of the inbox with no on-chain record of why it left. That is chain-invisible governance — silent drift, discoverable only by noticing something is missing.

The fix defers the receipt-less flips and applies them in one non-swallowing transaction with the receipt insert:

```ts
const deferred = [];
for (const c of batch) {
  if (c.decision === "promoted") {
    applyPromotion(c);            // already carries its own transactional receipt + memory
  } else {
    deferred.push(c);             // quarantine / duplicate — no individual receipt
  }
}
db.transaction(() => {
  insertGovernedReceipt(batchEvent);          // the ONLY record of the deferred flips
  for (const c of deferred) applyFlip(c);      // commit them WITH the receipt
})();                                          // throws → everything rolls back, error propagates
```

`promoted` stays in-loop deliberately, because a promoted row already writes its own transactional `promoted` receipt and curated memory — it is never chain-invisible. On a receipt failure the quarantine and duplicate flips roll back, those candidates stay `inbox` and get retried idempotently on the next run, the promoted rows persist with their receipts, and the error propagates so `runGovern` surfaces it and the nightly wrapper's fail-loud path alerts. Atomic rollback over best-effort retry: a governance action you can't record is a governance action you don't take.

## Property 5 — Consent-gated opt-in

Four properties made the write path safe. The fifth governs the switch, and it is the one thing you cannot automate.

The hook (`hooks/session-end-capture.mjs`) is the automatic twin of manual `/brain-save`. It carries three hard guards, and any unmet guard is a silent no-op: an opt-in marker file `~/.teamkb/autocapture.enabled`, team mode configured, and not a recursive child. It runs the distiller detached — it never blocks or fails the session — and the distiller holds a **member** token, so it can only propose to the inbox, never write durable state.

```js
if (!fs.existsSync(markerPath())) return;        // (a) opt-in marker absent → no-op
if (!teamModeConfigured()) return;               // (b) team mode off → no-op
if (process.env.TEAMKB_RECURSIVE) return;        // (c) recursive child → no-op
spawnDetached(distiller, { env: memberTokenEnv() }); // detached, member-scoped, never blocks
```

**Why isn't this just a `plugin.json` hooks entry?** Because a `plugin.json`-declared hook auto-installs the instant the plugin installs. That is exactly the silent push that was forbidden — a teammate updates the plugin and their sessions start shipping distilled learnings to a shared brain they never agreed to feed. The constraint that shaped the design was blunt: *"I don't want them to ship it and be like wtf."* So the hook is deliberately not plugin-declared. Installing the plugin enables nothing.

The only way to turn it on is a consent-gated enable script (`hooks/enable-autocapture.mjs`) that prints the full disclosure — what it does, what it does not do, how to pause, how to purge, and why — then requires typing `I CONSENT`. Only then does it register the hook in the teammate's own `~/.claude/settings.json` (backing the file up first) and write the marker. `--off` pauses, `--off --purge` deletes local logs, `--status` shows state.

Consent is the property you cannot make idempotent or durable. It has to be a deliberate human act, performed once, by the person whose sessions will be read. Even then the hook stays a silent no-op unless all three guards pass — and the distiller it spawns only does real work on a real transcript, so a hook that fires on an empty session burns nothing. A 5/5 hook-guard smoke test pins that whole no-op envelope against a stub `claude` on PATH, with zero model invocation. Verification across the change: `node --check` on both scripts, typecheck + lint + build exit 0, and `remote-server.test.ts`'s 69 tests green — with store 224 / api 323 still clean.

## The boring bugs that would have eaten the captures anyway

Two footguns fixed the same day, both the kind that lose data quietly:

- **Default DB path drift.** The API defaulted to `~/.teamkb/data/teamkb.db` while the plugin and brain used `~/.teamkb/teamkb.db`. A no-override deploy would write every teammate capture to a database the govern sweep never reads. Aligned the default via `resolveTeamKbPath('teamkb.db')` — chosen over assert-and-warn, because a warning still loses the capture. The live deploy already overrides `TEAMKB_DB_PATH`, so it was never hit; the next fresh deploy would have been.
- **No-op anchor skip.** `appendAnchor` now returns the last record unchanged when both the chain head and the row count match the last anchor. A nightly run that changed nothing was still appending to the tamper-evidence log and to git history for zero evidentiary gain. A real new head still anchors — the never-rehash-the-chain rule holds.

## Also shipped

The same "make an unattended watcher safe to cron" theme ran through the secondary repos. **agent-governance-plane** got a release-watcher meaningfulness filter (draft and prerelease releases dropped by default, `includePrereleases` to opt in — the skip runs *before* tag validation, so a tagless GitHub draft is skipped rather than crashing the watcher), a notify-mode one-way webhook that needs no human in the loop, and a one-command installer plus an extraction-readiness ADR, with three irreversible doors — public flip, npm publish, external reply — kept explicitly human-gated. **intentsolutions-vps-runbook** and **intent-os** got a torn-datadir backup fix: consistent DB dumps plus a restore-verification drill, correcting an over-optimistic single-host restore claim.

## The pattern behind safe unattended writes

A best-effort, fire-and-forget writer is a distributed system wearing a convenience costume. The moment the human leaves the loop, every property the human was silently providing has to be built into the write path: dedup so retries collapse, a spool so blips don't vanish, a per-actor cap so one identity can't flood, atomic receipts so governance can't drift invisibly, and a consent gate so the on-switch stays a human decision. Four of those you can engineer. The fifth you have to refuse to engineer.

## Related Posts

- [Adversarial Review: The Six Lenses That Halted a Rollout](/posts/adversarial-review-before-team-rollout/) — the governance review that gated this same team-brain rollout.
- [Every Safety Gate Has a Failure Direction](/posts/every-safety-gate-has-a-failure-direction/) — why drop-on-4xx / keep-on-5xx is a direction choice, not a detail.
- [Liveness Without Health Is Theater](/posts/liveness-without-health-is-theater/) — the sibling lesson for unattended systems: running is not the same as working.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Making a Fire-and-Forget Writer Safe Under Failure",
  "description": "Five properties an unattended capture hook needs before you turn it on: idempotent intake, durable outbox, backpressure, atomic receipts, consent gate.",
  "author": {
    "@type": "Person",
    "name": "Jeremy Longshore"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Start AI Tools"
  },
  "datePublished": "2026-07-11T10:00:00-05:00",
  "dateModified": "2026-07-11T10:00:00-05:00",
  "url": "https://startaitools.com/posts/making-fire-and-forget-capture-safe-under-failure/",
  "keywords": ["architecture", "idempotency", "ai-agents", "claude-code", "distributed-systems"],
  "articleSection": "Technical Deep-Dive"
}
</script>
