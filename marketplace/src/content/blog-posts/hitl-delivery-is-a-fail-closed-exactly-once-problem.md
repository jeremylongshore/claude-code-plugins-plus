---
title: "Human-in-the-Loop Is a Delivery Guarantee, Not a UI Feature"
description: "Human-in-the-loop agent delivery is exactly-once, fail-closed. Two repos shipped the same four-move discipline the same day — convergence, not coincidence."
date: "2026-06-07"
tags: ["ai-agents", "typescript", "architecture", "slack", "distributed-systems"]
featured: false
---
Two repos. One missing guarantee.

In `agent-governance-plane`, a human's approval was cryptographically signed with Ed25519 and written to a tamper-evident journal. Solid. Except the only `InteractionSource` wired into the system was an in-memory test stub. A human could see an Allow/Deny prompt — but the click had no way home. The signed approval was a letter with no mailbox.

In `claude-code-slack-channel`, an agent's reply to a Slack thread was a synchronous tool call. If the process died between "decide to send" and "send," the reply vanished. No turn-terminal flush, no retry, no record that an obligation ever existed. The user just waited.

Different repos, different directions of travel — one inbound (receive a human's decision), one outbound (deliver an agent's reply). Same hole: the part where a human and an agent actually hand work to each other was the part nobody made durable.

On 2026-06-07 both repos closed that hole. They shipped the **same four-move discipline**. And one repo's spec was lifted, by name, from the other's pattern. That is the part worth your attention.

## The reframe: this is distributed systems, not UI

Human-in-the-loop gets filed under "product" — a button, a modal, a confirmation dialog. That framing is why it breaks in production. The moment a decision has to survive a crash, an ack-loss, or a dropped socket, you are no longer building UI. You are building a durable message system, and the well-known failure modes apply.

The receiver and the reply path are both solving **exactly-once delivery**, **message deduplication**, and **fail-closed defaults**. Strip away Slack and the problem is identical to any outbox or any consumer that must not lose, must not duplicate, and must not silently double-act.

Four moves fall out of that framing:

1. **Record the obligation before the send.** Crash-before-send must be safe — the obligation outlives the process.
2. **Stamp an idempotency key into the message** so a later scan can recognize "already delivered."
3. **Redeliver idempotently from a poller** — a background drain that reconciles from disk, so ack-loss redelivery is a no-op.
4. **Fail closed on no-decision.** Timeout, dropped socket, no lease → deny and journal, or queue. Never crash, never silently double-act.

Hold those four moves. They recur on both sides.

## The reply outbox: CCSC's durable delivery pattern

CCSC has an inverted architecture, and the inversion is exactly why durability is hard: **a reply is a synchronous tool call, not a turn-terminal event.** There is no natural "end of turn" to flush at. That is what the **outbox pattern** is for: record the obligation durably *before* attempting the send, so a crash can't lose it. The agent calls a reply tool mid-reasoning and expects delivery to just happen. So the durability machinery has to live behind the tool, invisible to the caller.

The reply-delivery contract (ADR-002 addendum, "Option A: a safety-net behind the reply tool") is deliberately narrow: **single-message text replies only.** One obligation equals one message, so the idempotency is exact. Chunked, file, and streaming replies stay best-effort and do not enqueue — zero double-send risk, durability deferred to later beads. Scope discipline is part of the design, not a shortcut.

The machinery lives in `slack-delivery.ts` — a side-effect-free sibling module, deliberately *not* inline in `server.ts`, so it is testable without dragging in server module-load side effects. The center of it is `deliverReplyDurably`:

```typescript
// Record the obligation BEFORE the send (move 1).
// Crash here is safe — the poller will find the pending obligation and drain it.
async function deliverReplyDurably(deps: IdempotentSendDeps, reply: ReplyObligation) {
  const obligation = await deps.recordPending(reply); // UUID id == idempotency key
  try {
    const ts = await deps.send(obligation);           // one inline attempt
    await deps.markDelivered(obligation.id, ts);
    return { status: "delivered", ts };
  } catch (err) {
    if (isTransient(err)) {
      // Queued — the poller redelivers idempotently. Tell the agent "queued"
      // so it does NOT retry and double-post (move 4: never double-act).
      return { status: "queued" };
    }
    await deps.markDead(obligation.id, err);           // non-retryable → recorded dead
    throw err;
  }
}
```

The obligation id is a fresh UUID per reply call, and that id *is* the idempotency key. So when the poller later redelivers the same obligation, it dedups against itself. That is move 2, and it lives in the message metadata:

```typescript
// The single site that stamps delivery metadata onto the outbound message.
async function postReply(client: WebClient, obligation: ReplyObligation, key: string) {
  return client.chat.postMessage({
    channel: obligation.channel,
    thread_ts: obligation.thread,
    text: obligation.text,
    metadata: {
      event_type: DELIVERY_METADATA_EVENT_TYPE,
      event_payload: { idempotency_key: key },
    },
  });
}
```

Move 3 is the scan. Before sending, or when redelivering, `findDelivered` walks the destination thread via `conversations.replies` with `include_all_metadata: true`, looking for a message *we* posted carrying our delivery `event_type` and a matching `idempotency_key`. A hit returns the existing `ts` — so an ack-loss redelivery becomes a no-op instead of a duplicate.

```typescript
// A redelivery after ack-loss finds the prior post and returns its ts. No second message.
async function findDelivered(client: WebClient, channel: string, thread: string, key: string) {
  const res = await client.conversations.replies({
    channel, ts: thread, include_all_metadata: true,
  });
  const hit = res.messages?.find(
    (m) => m.metadata?.event_type === DELIVERY_METADATA_EVENT_TYPE
        && m.metadata?.event_payload?.idempotency_key === key,
  );
  return hit?.ts ?? null;
}
```

The poller itself (PR #228) is a `deliveryTimer` tick calling `supervisor.drainOutbox()` on an interval — `SLACK_DELIVERY_POLL_MS`, default 15s, the timer `unref`'d so it never holds the process open. A **boot-time drain** recovers crash-pending obligations on startup, and the timer is cleared on shutdown before the supervisor drain, mirroring the existing idle-reaper exactly.

Fail-closed also means degrading gracefully when the outbox itself is unavailable. `DurableUnavailableError` is thrown *before* any obligation is recorded — the outbox isn't activated, or there's no lease. The caller catches it and falls back to the prior direct send. Nothing is persisted, nothing needs redelivery, and there is zero regression versus the old path. Durability is additive; its absence degrades gracefully to what shipped before.

## Why not the obvious approach?

**Why not just retry inline?** Because inline retry only survives failures the process is alive to handle. The crash-before-send window — record nothing, send nothing, die — is exactly the window inline retry can't cover. The obligation has to exist on disk before the attempt, or there is nothing to retry from.

**Why not best-effort fire-and-forget?** Because "the reply usually arrives" is not a contract a human can build on. In a HITL loop the reply *is* the work product. Best-effort means the agent thinks it answered and the human is still waiting — the worst failure, because nobody knows it failed.

**Why is fail-open the dangerous default for an approval gate?** This is the load-bearing one. If a receiver times out and the system fails *open*, the gated action proceeds without a human decision. An approval gate has to act *exactly once* on a real human decision; failing open makes it act on *no* decision at all. The entire reason the gate exists is to stop unapproved actions; failing open deletes the gate precisely when it matters. For anything guarding an action, no-decision must mean **deny**, not **proceed**.

## The approval receiver: AGP's Socket Mode pattern

AGP comes at the same four moves from the inbound side. PR #66 builds the production receiver per spec **033-AT-SPEC — which is explicitly "lifted from the CCSC pattern, completes the HITL round-trip."** This is the keystone. What transferred wasn't code: CCSC delivers outbound and AGP receives inbound, so the two share not a single line. What transferred was the discipline — record the obligation, key it, reconcile it, fail closed — restated as a spec for an inbound approval channel. The convergence is not two teams independently reinventing a wheel; one read the other's pattern and applied it to the mirror-image problem.

The transport is Socket Mode: an **outbound** WebSocket from the control plane to Slack. No public ingress — which honors AGP's "no public surface until defensible" P0 decision. You get durability *and* no inbound attack surface. That combination is the design point.

Parsing is a pure function, so it is trivially testable and impossible to make stateful by accident:

```typescript
// parseBlockAction — pure. block_actions payload → SlackInteraction, or null for noise.
function parseBlockAction(payload: SlackPayload): SlackInteraction | null {
  const action = payload.actions?.[0];
  if (!action || payload.type !== "block_actions") return null; // ack-and-ignore
  return {
    nonce: action.value,
    approved: action.action_id === "approve",
    userId: payload.user.id,
    isBot: Boolean(payload.user.is_bot),
  };
}
```

The receiver holds a **pending-by-nonce promise Map**, acks every envelope first (Slack drops you if you're slow), then resolves the awaiting `awaitInteraction(nonce)` on a matching click. A `resolved` Set makes replay detection explicit — a click that arrives for an already-settled nonce is *reported as a replay*, never acted on a second time:

```typescript
class SocketModeInteractionSource {
  private pending = new Map<string, Deferred<Decision>>();
  private resolved = new Set<string>();

  // Surface a stray/replayed click via onRejected — report it, never act on it.
  private reject(nonce: string, reason: string) { /* onRejected({ nonce, reason }) */ }

  onInteraction(i: SlackInteraction) {
    if (this.resolved.has(i.nonce)) {
      // move 4: a replayed click is a no-op, surfaced as a reason — not a second approval.
      this.reject(i.nonce, "nonce already used (replay)");
      return;
    }
    const d = this.pending.get(i.nonce);
    if (!d) { this.reject(i.nonce, "unknown nonce"); return; }
    this.resolved.add(i.nonce);
    d.resolve({ approved: i.approved, userId: i.userId });
  }

  // Timeout defaults to the nonce TTL (5 min) — the receiver never out-waits the nonce.
  awaitInteraction(nonce: string) { /* register + arm TTL timer */ }
}
```

That replay-detection guard is move 4 again, mirrored: the outbox's never-double-*send* rule becomes the receiver's never-double-*act* rule. Same principle, opposite direction of travel.

Fail-closed shows up in three places, and all three matter:

- `stop()` closes the socket and **fails closed on every still-pending approval** — a shutdown mid-decision denies, it does not hang.
- In `run.ts`, `AGP_CHANNEL=slack` plus `AGP_SLACK_LIVE=1` constructs the live receiver. **Unset `AGP_SLACK_LIVE` fails closed** — the system refuses to post a prompt that nothing can answer. A prompt with no receiver is worse than no prompt; it implies a decision is being collected when none can be.
- In `daemon.ts`, a no-decision — receiver timeout or socket drop — now **fails closed (deny + journaled reason) instead of crashing the loop**, in both `mediate()` and `gate()`. It reuses the existing `approval.denied` journal kind, so there is no schema change: a fail-closed deny is indistinguishable, downstream, from an explicit human deny. The action does not happen, and there is a signed record of why.

The `FetchWebSocketDialer` (`apps.connections.open` → `wss`) injects both `fetch` and the socket constructor, so the response and adapter logic is CI-tested; only the real `new WebSocket` seam runs off-CI under `AGP_SLACK_LIVE`. The same testability discipline as CCSC's side-effect-free module — extract the seam, test everything up to it.

## The transferable rule

If you are building any human-in-the-loop agent — Slack, email, a web approval, a CLI prompt — these four moves are your checklist:

1. **Record the obligation before the send.** Crash-before-send must be safe.
2. **Stamp an idempotency key into the message.** A later scan must be able to recognize "already done."
3. **Redeliver idempotently from a poller.** Reconcile from durable state; make redelivery a no-op.
4. **Fail closed on no-decision.** Timeout, dropped socket, no lease → deny and journal, or queue. Never crash, never silently double-act.

Move 4 is the non-negotiable one. Anything that gates an action must treat the absence of a human decision as a *no*. Fail-open turns a safety gate into a rubber stamp the instant the network hiccups.

The convergence is the evidence. When two systems built for mirror-image roles — one delivering replies out, one receiving approvals in — arrive at the same discipline, and one explicitly cites the other, that is not a local trick. It is the shape of the problem. And the discipline it demands is non-negotiable: an agent you can't trust to fail safely is an agent you can't deploy.

Both shipped clean. CCSC's `slack-delivery.ts` hit 100% line coverage; the test suite grew from 1127 to 1133 tests across the three PRs with all nine gates green each time, and the durable path was extracted to `executeReplyDurablePath` to keep `executeReply` under CRAP 30. AGP landed at 88.89% function / 91.43% line coverage — over the repo's configured floor — with typecheck, Biome, claim-scan, harness verify, and escape-scan all green. The PR sequencing in CCSC is itself the lesson: #228 wired the poller into the runtime without touching the reply tool path ([machinery live but dormant](/posts/ship-dormant-wire-later-multi-agent-slack/)), #229 added the tested building block plus the ADR (design-first), #230 flipped `executeReply` to route through it. The security-sensitive change got its own isolated PR. Ship dormant, wire later.

## Also shipped

The same day, `claude-code-plugins` landed a deterministic-CI grading track: a `pr-classifier` doing file-level PR component detection, feeding per-domain lint workflows plus actionlint and a path-routing test, then a PR-level grade coordinator with golden fixtures — alongside the public 100-point grading rubric at `/grading`, a 176-test pytest harness for the penetration-tester pack, and a switch of the PR pre-screen LLM from Groq to DeepSeek. And `contributing-clanker` added two gates: C24 (engagement-frame) and C25 (maintainer-URL leakage).

## Related Posts

- [Ship Dormant, Wire Later — A Multi-Agent Slack Production Day](/posts/ship-dormant-wire-later-multi-agent-slack/)
- [Making Agents Reliable on Real-Device Clouds](/posts/making-agents-reliable-on-real-device-clouds/)
- [Safety Model First: 16-Tool Ops MCP, One Day](/posts/server-ops-mcp-safety-before-tools/)

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Human-in-the-Loop Is a Delivery Guarantee, Not a UI Feature",
  "description": "Human-in-the-loop agent delivery is exactly-once, fail-closed. Two repos shipped the same four-move discipline the same day — convergence, not coincidence.",
  "datePublished": "2026-06-07T08:00:00-05:00",
  "author": {
    "@type": "Person",
    "name": "Jeremy Longshore",
    "url": "https://startaitools.com/about/"
  },
  "publisher": {
    "@type": "Organization",
    "name": "StartAITools",
    "url": "https://startaitools.com"
  },
  "articleSection": "Technical Deep-Dive",
  "keywords": "ai-agents, typescript, architecture, slack, distributed-systems",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://startaitools.com/posts/hitl-delivery-is-a-fail-closed-exactly-once-problem/"
  }
}
</script>
