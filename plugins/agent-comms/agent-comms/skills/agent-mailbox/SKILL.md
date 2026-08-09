---
name: agent-mailbox
description: |
  Durable asynchronous handoff between agents with zero infrastructure — no broker, no daemon, no
  service to run. A mailbox is an append-only directory of atomically-written message files that
  survives a restart, gives every handoff an inspectable audit trail, and turns a status push into
  a pull so the sending edge disappears from the agent graph entirely. Covers the directory
  layout, atomic-write and claim protocols, at-least-once delivery with idempotency, retention,
  and the exact conditions under which a mailbox is the wrong answer. An implementation, never a
  specification. Use when work must outlive a session, when two agents run on different schedules,
  or when checking how to hand off without standing up a queue. Trigger with "agent mailbox",
  "durable handoff between agents", "async agent messaging", "queue without a broker",
  "file-based agent inbox".
allowed-tools: Read, Write, Glob, Bash(mkdir:*), Bash(mv:*), Bash(ls:*)
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code; requires only a POSIX filesystem with atomic rename. No broker, daemon, or network service.
tags: [multi-agent, async, durability, handoff, zero-infra]
model: inherit
---

# Agent Mailbox — Durable Handoff Without a Broker

A mailbox is a directory. A message is a file. Delivery is an atomic rename. The absence of moving
parts is the feature: nothing to deploy, nothing to monitor, nothing that can be down while the agents
are up.

**This is an implementation, not a specification.** It is not versioned as a protocol, defines no wire
format for anyone to adopt, and invites no conformance. Crossing an organizational boundary calls for a
real protocol — see the `a2a-protocol` skill.

## Overview

Three properties earn the mailbox its place between a direct call and a bus:

- **Durability.** A message written before a crash is there after it; a direct call loses it.
- **Schedule independence.** Sender and receiver never have to be alive at the same time.
- **Inspectability.** The history is files, so reconstruction is `ls` rather than a broker console —
  which matters most when a broker console is hardest to reach.

A fourth is structural: it converts a push into a pull, so the agent-to-agent edge leaves the graph —
and an edge that does not exist cannot amplify or close a cycle.

## Prerequisites

- A filesystem both agents can reach, with atomic rename within one filesystem. Local disk or a shared
  volume — not an object store, where rename is a copy.
- A shared understanding of message shape. The mailbox transports opaque payloads and does not validate
  them.
- No credentials. Access control is filesystem permissions; there is no authentication layer here.

## Instructions

### Step 1: Lay out the directories

Four states, one directory each. State is the directory a file is in, so no file needs a status field:

```text
mailbox/<recipient>/
  inbox/       delivered, unclaimed
  claimed/     a reader has taken it
  done/        processed successfully
  failed/      processing failed; retained for inspection
```

### Step 2: Write atomically

Never write directly into `inbox/`. A reader can see a partially-written file and consume half a
message. Write to a temporary name in the same directory, then rename:

```bash
mkdir -p mailbox/writer/inbox
printf '%s' "$payload" > mailbox/writer/inbox/.tmp-$$-msg
mv mailbox/writer/inbox/.tmp-$$-msg mailbox/writer/inbox/20260809T120000Z-a3f9.json
```

Rename within one directory is atomic. The dot prefix keeps the temporary file out of a reader's glob
during the window before the rename lands.

### Step 3: Claim before processing

Two readers on one inbox both see the same file. `mv` is the lock — exactly one rename succeeds:

```bash
mv mailbox/writer/inbox/20260809T120000Z-a3f9.json mailbox/writer/claimed/ 2>/dev/null \
  && process mailbox/writer/claimed/20260809T120000Z-a3f9.json
```

A failed `mv` means another reader won. Move on; do not retry the same file.

### Step 4: Make handlers idempotent

Delivery is **at-least-once**. A reader that claims a message and dies leaves it in `claimed/`, and
recovery re-processes it. Carry a stable message id and make the effect of processing it twice equal to
processing it once. Reasoning and recovery details: `references/delivery-semantics.md`.

### Step 5: Sweep and retain

Configure a sweeper that returns stale `claimed/` files to `inbox/` after a timeout and prunes `done/`
on a retention window. Both timeouts are optional parameters with no safe universal default; derive
them from measured processing time. Keep `failed/` longer — it is the audit trail. Alternatively, adapt
the layout to one tree per correlation id when a run's messages are inspected and pruned as a unit.

## Examples

A message file. Envelope fields are the mailbox's; `body` is opaque to it:

```json
{ "id": "20260809T120000Z-a3f9",
  "from": "research-agent", "to": "writer-agent",
  "createdAt": "2026-08-09T12:00:00Z", "attempts": 0,
  "body": { "sourceCount": 12, "digestPath": "runs/2026-08-09/digest.md" } }
```

Note what the body carries: a **path**, not the digest. Passing a reference rather than a payload keeps
the mailbox small, keeps the receiver's context free, and lets the receiver decide what to read.

Reading an inbox, oldest first — lexicographic timestamp names do the ordering, and Glob over
`mailbox/*/inbox/*.json` enumerates every recipient at once:

```bash
set -e
ls mailbox/writer-agent/inbox/*.json 2>/dev/null | head -1
```

Sweeping a claim that a dead reader abandoned:

```bash
set -e
find mailbox/*/claimed -name '*.json' -mmin +30 -exec mv {} ../inbox/ \;
```

## Error handling

- **Rename across filesystems** — not atomic; it degrades to copy-then-delete and a reader can observe
  a partial file. Keep the mailbox on one filesystem, and check that before trusting the layout.
- **Reader dies mid-processing** — the message stays in `claimed/` and the sweeper returns it, which is
  why handlers must be idempotent; without that, the sweep is a duplicate-work generator.
- **Poison message** — fails every attempt. Cap attempts, move to `failed/`, stop.
- **Inbox growth** — the reader is dead or slower than the writer. Alert on depth; a mailbox has no
  backpressure, which is the price of the decoupling.

## Validation

1. Verify writes land via rename and never as a direct create in `inbox/`.
2. Check that claiming uses `mv` as the lock and that a losing reader proceeds instead of retrying.
3. Verify processing a message twice produces the same end state as processing it once.
4. Check that the sweeper's timeout exceeds the longest legitimate processing time, and that
   `failed/` retention outlives `done/` retention.

## Output

Report a mailbox as a four-line state census — inbox depth, claimed count with the oldest claim age,
done count, failed count — plus the id of every message in `failed/`. Oldest claim age is the leading
indicator: a claim older than the sweep timeout means the sweeper is not running.

## Boundaries

A mailbox is not a bus. No fan-out, no subscriptions, no replay to new consumers — for those, use a
broker, and price the edges first with `comms-topology`. It is also not a protocol: opaque payloads, no
discovery, no auth, no version negotiation. Across a trust boundary, use A2A.

It is also not the only zero-ceremony option, and the niche is narrow: purpose-built agent stores hold
durable state with a query layer and a sync story, and agent inbox services give a routable cross-org
address. What remains here is zero dependencies, zero accounts, zero network, and `ls` as the debugger.

## References

- `references/mailbox-protocol.md` — layout, envelope fields, naming, sweeper design.
- `references/delivery-semantics.md` — at-least-once, idempotency, ordering, failure modes.
- `references/when-not-to-use.md` — when a mailbox is the wrong answer, and the prior art to use.
