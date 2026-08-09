# The eight axes, the elimination order, and composition

## The eight axes in full

**Coupling.** Does the sender need the receiver's identity at send time? Direct and mailbox say yes;
bus and protocol-with-discovery say no. Identity coupling is what makes an N-agent system an N² wiring
problem.

**Durability.** Does a message survive a process restart? Direct: no. Mailbox: yes, by construction.
Bus: depends entirely on broker configuration — an in-memory bus is a direct call with extra steps and
a false sense of safety.

**Ordering.** Does out-of-order delivery change the result? Global ordering is expensive and usually
unnecessary; per-key ordering is cheap and usually sufficient. Systems that demand global ordering
across unbounded fan-out are asking for a contradiction, not a topology.

**Fan-out.** How many consumers per event? One means mailbox suffices. More than one means a bus, or
duplicated writes that will drift the moment a consumer is added and one write site is missed.

**Failure isolation.** Does a slow or dead consumer stall the producer? Direct calls propagate
backpressure immediately, which is a feature in a two-agent system and a cascade in a ten-agent one.

**Observability.** Can the full message history be reconstructed after an incident? A mailbox backed by
files is trivially inspectable. An in-memory bus is not, and that difference shows up at exactly the
wrong moment.

**Cost per edge.** Tokens, latency, and dollars per hop. Every edge is a model call somewhere. This is
the axis that surprises people, and it is why edge count belongs in the design, not the invoice.

**Migration cost.** What breaks when this shape is outgrown? Direct-to-mailbox is cheap: the call site
changes, the logic does not. Bus-to-protocol is expensive: the contract becomes public and versioned.

## Elimination order

Run in this order and stop at the first match. The order encodes cost — each rule that fires forces a
more expensive shape, so the earliest-firing rule dominates.

1. **Trust boundary → protocol.** Any participant outside the organization needs discovery, auth, a
   versioned contract, and typed errors. Direct, mailbox, and bus all assume shared trust and provide
   none of those.
2. **Fan-out > 1 → bus.** More than one consumer per event. A mailbox can fan out only by duplicating
   writes, which is correct on the day it is written and drifts on the day a consumer is added.
3. **Outlives the session → mailbox.** Work that must survive a restart needs a durable handoff. This
   is the most commonly skipped rule, because durability requirements surface after the first crash.
4. **Otherwise → direct.** Two agents that live and die together do not need a broker between them.

Two rules can fire at once — trust boundary plus fan-out is common. The earlier rule wins, but the
later one becomes a constraint on the design rather than disappearing.

## Composition at boundaries

Topologies compose. A system is rarely one shape:

```
[interior: direct]  ──seam: protocol──  [partner interior: their business]
       │
   [fan-out inside the org: bus]
```

The productive framing is: **protocol at the seams, cheapest viable shape in the interior.** Running one
bus across an organizational boundary is the classic error — it exports internal event shapes as a de
facto public contract without any of the versioning that a real protocol provides.

## Anti-patterns

- **Bus by default.** A broker introduced before fan-out exists pays the ordering and observability
  cost with none of the benefit.
- **Mailbox as a queue for one consumer that is always up.** A direct call with a retry is simpler and
  has better failure signals.
- **Protocol inside one process.** Serialization, discovery, and auth overhead to reach a function in
  the same address space.
- **Mesh.** Every agent talking to every agent is N² edges, and every edge is a token cost and a
  potential cycle. Mesh is not a topology choice; it is the absence of one.
- **Choosing on team familiarity.** Familiarity is a real input to migration cost. It is not an input to
  any of the other seven axes, and it should never override rule 1.

## Recording the decision

A topology decision that is not written down is re-litigated every quarter. Record: the eight axis
values, which rule fired, the edge count, and the migration trigger. The migration trigger is the part
that decays fastest and matters most — it is the tripwire that turns a rewrite into a planned move.
