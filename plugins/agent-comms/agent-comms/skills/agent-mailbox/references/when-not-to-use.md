# When a mailbox is the wrong answer

A skill that only argues for its own mechanism is marketing. These are the cases where a mailbox loses,
stated plainly enough to act on.

## Use something else when…

### The participants are in one process and die together

A direct function call is simpler, has better failure signals, and costs nothing. Durability is
worthless when nothing survives the crash anyway. **Use a direct call.**

The tell: "we might need durability later" with no scenario in which one agent outlives the other.
Migrating direct-to-mailbox later is cheap — the call site changes, the logic does not — so building it
early buys nothing.

### More than one consumer needs the same message

A mailbox is one message, one consumer. Fan-out by duplicating writes to N inboxes works on the day it
is written and breaks on the day someone adds consumer N+1 and misses a write site. **Use a bus.**

### The consumer set is not known in advance

New subscribers catching up from history is replay, and `done/` is an audit trail, not a replay log.
**Use a broker with retention.**

### Strict global ordering is required

Per-writer ordering holds; cross-writer ordering is subject to clock skew, and reclaim after a sweep
reorders by design. **Use a single-partition bus, or a single reader.**

### The counterparty is outside the trust boundary

`from` is a self-reported string. There is no authentication, no discovery, no versioned contract, no
typed errors. A shared filesystem across an organizational boundary is not a trust model.
**Use A2A** — see the `a2a-protocol` skill.

### Latency below a second matters

A mailbox is polled. Poll interval is the floor on latency, and tightening it trades cost for
responsiveness in exactly the way a push would not. **Use a direct call or a real broker.**

### The storage layer has no atomic rename

Object stores implement rename as copy-then-delete. Both the atomic write and the claim lock depend on
atomic rename, so on an object store neither works, and the failures are intermittent rather than
loud. **Use a real queue.**

### The payload contains secrets

Files are plaintext on disk with filesystem permissions as the only control. Put a reference in the
body and let the receiver fetch the secret through a path it is separately authorized for.

### There is already a broker running

If the infrastructure exists, is monitored, and the team knows it, the mailbox's main advantage — no
infrastructure — is already paid for. **Use what is running.**

### A purpose-built agent store or inbox already covers it

This mailbox is a directory and a rename. That is its whole claim, and the field is not empty:

| Prior art | What it is | Prefer it when |
| --- | --- | --- |
| **Turso AgentFS** (`tursodatabase/agentfs`, ~3.3k stars, Rust) | "The filesystem for agents" — filesystem ops, key-value storage, and automatic tool-call tracking in a single database file; part of Turso's database-per-agent model with optional sync | State outgrows message-passing — durable agent memory, queryable history, or a store that syncs beyond one host. A rename-based directory has no query layer and no sync |
| **AgentMail** (YC S25) | API-first email inboxes for agents; API-key auth rather than OAuth, so an agent operates without a human behind the mailbox | The counterparty is outside the org, needs a **routable address**, or a human may have to read the thread. Email is the one transport that already routes everywhere |

Taking each seriously:

- **AgentFS solves durability better than this does.** If the handoff is really shared state rather than
  a message, a purpose-built embedded store beats a hand-rolled directory — it has a query layer, a
  sync story, and someone else maintains the atomicity.
- **AgentMail solves addressing, which this does not attempt.** A filesystem mailbox has no address a
  stranger can reach. That is the trust-boundary rule from another angle: cross-org handoff needs
  either a real protocol (A2A) or a routable transport (email), not a shared volume.

What is left for this mailbox after both: **zero dependencies, zero accounts, zero network, and `ls`
as the debugger.** Inside one trust boundary, on one filesystem, when adding a dependency is the cost
you are trying to avoid — that is the niche, and it is narrower than "durable agent messaging."

## Honest comparison

| | Direct | Mailbox | Bus | Protocol |
| --- | --- | --- | --- | --- |
| Infrastructure | none | none | broker | server + auth |
| Durable | no | yes | configurable | yes |
| Fan-out | no | no | yes | via subscriptions |
| Cross-trust-boundary | no | no | no | yes |
| Latency floor | call | poll interval | push | network |
| Inspectable after an incident | logs | files | broker console | logs + traces |
| Backpressure | immediate | none | configurable | protocol-level |

The row that decides most real cases is **fan-out**. The row that decides the rest is
**cross-trust-boundary**. Everything else is tuning.

## The migration trigger

Record what would force the next step, because it will arrive:

- A second consumer for the same message → bus.
- A participant outside the organization → protocol.
- Sub-second latency → direct or push.

A mailbox that has outgrown one of these and is being extended to cope — duplicated writes, a tighter
poll, a shared volume mounted across a boundary — is a system on its way to an incident. Migrate rather
than extend.
