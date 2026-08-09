# Delivery semantics — what the mailbox guarantees and what it does not

## At-least-once, by construction

Delivery is **at-least-once**. Exactly-once is not achievable here and is not achievable in most
distributed handoffs; claiming it would be a lie that costs correctness downstream.

The gap is precise. A reader that claims a message and dies before resolving it leaves the file in
`claimed/`. The sweeper returns it to `inbox/`. A second reader processes it. If the first reader
completed its side effects before dying, those effects happen twice.

**Therefore: handlers must be idempotent.** This is not a recommendation; it is the contract that makes
the rest of the mechanism sound.

## Making a handler idempotent

The envelope's `id` is the idempotency key. Three patterns, in order of preference:

1. **Natural idempotency.** Writing to a path derived from the id — `runs/<id>/output.md` — is idempotent
   for free. The second write produces the same bytes at the same location. Prefer this.
2. **Check-then-act on a durable marker.** Before side effects, check for `done/<id>` or an equivalent
   record. Cheap; racy only if two readers claim the same message, which the `mv` lock prevents.
3. **Idempotency key at the far side.** For external calls, pass the message id as the provider's
   idempotency key. This pushes the guarantee to the only component that can actually enforce it.

The anti-pattern is an append. Appending a line per message turns one duplicate delivery into one
duplicate row, silently, forever.

## Ordering

Filenames sort chronologically, so a reader taking the lexicographically-first file processes in
**write order per writer**. That is the guarantee, and it is narrower than it looks:

- **Across writers** — ordering is by timestamp, and clock skew between hosts reorders messages. Do not
  build a state machine that depends on cross-writer order.
- **Under concurrent readers** — two readers process concurrently. Sequential claiming does not imply
  sequential completion.
- **After a sweep** — a reclaimed message re-enters `inbox/` with its original name, so it sorts back
  into its original position and may be processed after messages that were written later. Reclaim
  breaks strict ordering by design; the alternative is dropping the message.

Need strict global ordering? A mailbox is the wrong shape. That requirement is a bus with a single
partition, or a single reader — and both are worth choosing deliberately.

## Failure modes

| Failure | Observable | Response |
| --- | --- | --- |
| Reader dies mid-processing | File stuck in `claimed/`, age growing | Sweeper reclaims after timeout |
| Poison message | `attempts` climbing, always failing | Cap attempts, move to `failed/`, stop |
| Writer outpaces reader | `inbox/` depth growing without bound | Alert on depth; there is no backpressure |
| Two writers, one filename | A message silently vanishes | Include the writer id in the name |
| Cross-filesystem rename | Truncated reads, intermittent and rare | Keep the tree on one filesystem |
| Sweeper not running | Oldest claim age exceeds the timeout | This is the single best liveness signal |

## No backpressure

A mailbox never slows a writer down. That is the decoupling everyone wants, and its cost is that an
unbounded inbox is the only signal a reader has died.

Monitor **inbox depth** and **oldest claim age**. Depth answers "is the reader keeping up"; oldest claim
age answers "is the sweeper alive". Neither is derivable from the other, and the pair covers every
failure in the table above.

## What a mailbox does not provide

- **Fan-out.** One message, one consumer. Duplicating writes to N inboxes works until someone adds a
  consumer and misses a write site.
- **Replay to new consumers.** `done/` is retained for audit, not for a new reader to catch up from.
- **Sender authentication.** `from` is a self-reported string. Inside a trust boundary that is fine;
  across one it is worthless.
- **Encryption at rest.** Files are plaintext on disk. Do not put secrets in a body — pass a reference to
  something the receiver is separately authorized to read.
- **Transactional coupling.** Writing a message and committing a database change are two operations. A
  crash between them leaves them inconsistent, and no amount of atomic rename fixes that.
