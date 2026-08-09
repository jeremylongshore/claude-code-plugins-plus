# Loop-breaking patterns that survived production

These defences come from a shipped multi-agent Slack bridge where several Claude Code instances and
third-party bots share channels. Each is stated with what it stops **and** what it does not — the limit
is part of the mitigation, not a footnote.

## 1. Default-deny on peer agents

Bot-authored messages are **dropped at the gate by default**. A channel opts in to specific peers by
listing their IDs in an `allowBotIds` array. Empty list means no cross-agent delivery at all.

*Stops:* an unexpected third bot joining a channel and immediately participating in a loop.
*Does not stop:* a peer that was legitimately opted in and then started misbehaving. Opt-in
authenticates identity, not intent.

**Design rule:** cross-agent delivery is a decision someone makes, not a default someone inherits.

## 2. Self-echo filtering on every identity field

An agent must never consume its own output. The transport may express sender identity in more than one
field depending on the payload variant, so the filter matches on **all** of them — in the Slack case
`bot_id`, the bot profile's `app_id`, and the plain `user` field against the bot's own user id.

*Stops:* the trivial A→A loop, in every payload shape the platform emits.
*Does not stop:* an echo laundered through a third party. If B mirrors A's message verbatim, A sees a
message from B, and self-echo filtering correctly does not fire.

**Design rule:** match every identity field the transport can populate. Matching one is a bypass
waiting for a payload variant.

## 3. Per-pair sliding window

A sliding-window rate limit keyed on the ordered pair `(channel, sender)`. Production default:
**10 messages per 60 seconds**.

*Stops:* the two-agent ping-pong — A→B→A→B — which is the most common runaway and the one that
escalates fastest.
*Does not stop:* a ring of three or more. This is the structural limit that motivates the next defence.

**Sizing:** set it above observed normal conversational rate and below the rate at which a loop becomes
expensive. Ten per minute per pair is generous for agents and tight for a loop.

## 4. Graph-wide circuit breaker

A second sliding window over **all** agent traffic in a channel, regardless of sender. Production
default: **40 messages per 60 seconds**.

*Stops:* the A→B→C→A ring that the per-pair limiter cannot see, because no individual pair exceeds its
own budget while the aggregate runs away.
*Does not stop:* a slow loop deliberately paced under the ceiling. A breaker bounds cost; it does not
prove termination.

**Sizing:** above aggregate normal traffic, below the cheapest ring the graph admits. With a per-pair
limit of 10, a three-agent ring can sustain 27 per minute without tripping any pair — so a ceiling of
40 catches the ring while leaving headroom for a busy channel.

Setting both windows to `{ count: 0, windowMs: 0 }` disables them. Default-on is deliberate: the state
in which a runaway happens is almost always the state in which someone turned a limiter off to unblock
something and left it off.

## 5. Permission replies blocked at the gate

The approval mechanism — a short reply code that authorizes a pending tool call — is checked **at the
inbound gate**, before a peer message can reach the agent. A peer agent therefore cannot emit text that
matches the approval pattern and auto-approve a pending call.

*Stops:* privilege escalation by text injection between cooperating agents. This is the escalation path
that makes an agent loop dangerous rather than merely expensive.
*Does not stop:* a compromised human approver. Identity is authenticated, intent is not.

**Design rule:** approval must be checked at the trust boundary, not by the component reading the
message. A gate that delivers first and validates later has already lost.

## 6. Non-sticky peers

A peer agent's message does not mark a conversation as engaged for follow-ups the way a human's does.
Every peer message passes the full gate again.

*Stops:* one authorized peer message opening a durable channel that subsequent unauthorized traffic
rides through.
*Does not stop:* repeated authorized messages. Non-stickiness bounds authority in time, not in volume —
which is why it composes with the rate limiters rather than replacing them.

## Composition

The six are layered deliberately, each catching what the previous misses:

```
default-deny → self-echo → per-pair window → graph-wide breaker → gate-checked approval → non-sticky
   identity      A→A          A→B→A            A→B→C→A            escalation             persistence
```

Removing any one leaves a specific, nameable hole. The most commonly removed is the graph-wide breaker,
because it never fires in a two-agent system — right up until a third agent joins.
