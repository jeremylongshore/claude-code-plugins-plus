---
name: comms-topology
description: |
  Choose the coordination topology before writing any message plumbing — direct call, durable
  mailbox, shared bus, or a full agent-to-agent protocol. Coordination is a configurable architectural
  layer separable from agent logic, and multi-agent systems fail in production far more often from
  coordination defects than from base-model capability. This skill scores a described workload
  against four topologies on eight axes (coupling, durability, ordering, fan-out, failure
  isolation, observability, cost per edge, and migration cost) and names the cheapest one that
  survives the workload. Use when designing a multi-agent system, checking whether a bus is
  warranted, or debugging a coordination layer that outgrew its shape. Trigger with
  "which topology", "how should my agents talk", "do I need a message bus", "agent coordination
  design", "direct call or mailbox".
allowed-tools: Read, Glob, Grep, AskUserQuestion
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code; no runtime dependencies. Pairs with the topology-safety skill for cycle and redundancy analysis.
tags: [multi-agent, topology, coordination, architecture, system-design]
model: inherit
---

# Comms Topology — Pick the Shape Before the Plumbing

Most multi-agent systems are debugged at the message layer and broken at the topology layer. The
published failure taxonomy is blunt about this: production failure rates for multi-agent systems sit
in the tens of percent, driven mostly by coordination defects rather than by weak models, and
inter-agent misalignment is one of the three top failure categories.

The lever is the graph, not the payload. This skill picks the graph.

## Overview

Four topologies, ordered by cost per edge:

| Topology | Shape | Buys | Costs |
| --- | --- | --- | --- |
| **Direct** | A calls B, in-process or one hop | Zero infrastructure, trivial debugging | No durability; caller blocks; N² wiring |
| **Mailbox** | A writes, B reads when ready | Durability, async, no broker | No fan-out; polling latency |
| **Bus** | Many publish, many subscribe | Fan-out, decoupling, replay | A broker to run; ordering is now a design problem |
| **Protocol** | Typed contract over a network boundary | Cross-org interop, discovery, auth | Full protocol surface to implement and version |

The rule that decides most cases: **choose the leftmost topology that survives the workload.** Every
step right adds an edge class, and every edge class adds a failure mode that must then be defended.

## Prerequisites

- A described workload: how many agents, who initiates, whether work outlives a session, and whether
  any participant is outside the trust boundary.
- For an existing system, the source tree — Glob and Grep locate the current call graph, and Read
  opens the call sites they find.
- No credentials. This skill designs a graph and touches no external service, so no authentication
  applies; auth belongs to the transport skills that implement the chosen shape.

## Instructions

### Step 1: Extract the eight axes

Score the workload on each. Ambiguity here is the real work; use `AskUserQuestion` rather than
assuming.

| Axis | Question |
| --- | --- |
| Coupling | Must the caller know the callee's identity? |
| Durability | Does a message survive a restart? |
| Ordering | Does out-of-order delivery change the result? |
| Fan-out | Does one event have more than one consumer? |
| Failure isolation | Does a slow consumer stall a producer? |
| Observability | Is the full message history reconstructible after the fact? |
| Cost per edge | Tokens, latency, and dollars per hop |
| Migration cost | What breaks when this shape is outgrown? |

### Step 2: Apply the elimination rules

Run these in order and stop at the first match. Details in `references/topology-decision-rules.md`.

1. Check for a trust boundary. Any participant outside the organization forces **protocol** — nothing
   to the left carries discovery, auth, or a versioned contract.
2. Check fan-out. More than one consumer per event forces **bus**; a mailbox fans out only by
   duplicating writes, which drifts.
3. Check durability. Work that outlives a session forces **mailbox** or stronger.
4. Otherwise use **direct**. Two agents in one process that both survive together do not need a broker.

### Step 3: Count the edges before committing

A topology is priced per edge, and edge count is where multi-agent cost quietly explodes. Published
work on communication redundancy showed graph pruning holding task performance while cutting spend
from roughly forty dollars to under six on the same workload — a 28–73% token reduction — and the
pruned graphs also resisted two classes of adversarial attack. Fewer edges is cheaper *and* safer.

Count edges for the candidate shape. Above roughly a dozen live edges, hand the design to the
`topology-safety` skill before building it.

### Step 4: Name the migration path

Every choice is provisional. Record what would force the next step right, and what breaks when it
happens. A design that cannot name its own successor is a design that will be rewritten under
pressure rather than migrated.

## Examples

A two-agent researcher-plus-writer pipeline, same process, no durability requirement:

```text
Trust boundary?  no   → not protocol
Fan-out > 1?     no   → not bus
Outlives session? no  → not mailbox
VERDICT direct — 1 edge. Migration trigger: writer needs to survive a crash → mailbox.
```

A nightly fleet where one discovery run feeds three independent consumers:

```text
Trust boundary?  no
Fan-out > 1?     yes (3 consumers) → bus
VERDICT bus — 1 publisher, 3 subscribers, 3 edges. Ordering: per-key, not global.
Migration trigger: a fourth consumer outside the org → protocol at that seam only.
```

A partner-owned agent doing part of the work:

```text
Trust boundary?  yes → protocol (A2A)
VERDICT protocol at the org seam; direct inside each org. Do not run one bus across both.
```

That last line generalizes: **topologies compose at boundaries.** A system is usually protocol at the
seams and direct in the interior, not one shape everywhere.

## Error handling

- **Workload underspecified** — stop and ask. A topology chosen from guessed durability requirements is
  the expensive mistake this skill exists to prevent.
- **Existing system contradicts the described one** — report the discovered call graph verbatim and
  reconcile before recommending. Grep findings outrank the description.
- **Every topology eliminated** — the workload has contradictory requirements, most often global
  ordering plus unbounded fan-out. Name the contradiction rather than picking the least-bad shape.

## Validation

1. Verify each of the eight axes has an explicit value, not a default.
2. Check that the recommended topology is the leftmost surviving one, and say what eliminated each
   cheaper option.
3. Verify the edge count is stated as a number.
4. Check that a migration trigger is named for the recommendation.

## Output

Emit an eight-row axis table, an elimination trace showing what ruled out each cheaper topology, the
verdict with its edge count, and one migration trigger. Recommend exactly one topology; a
recommendation that hedges across two has not made the decision.

## Boundaries

This skill designs the graph. It does not implement transport, define a message format, or author a
protocol — for the wire, use the `a2a-protocol` skill; for cycles and pruning, use `topology-safety`.

## References

- `references/topology-decision-rules.md` — the eight axes, elimination order, and composition rules.
- `references/failure-literature.md` — the coordination-failure and pruning results cited above.
- `references/topology-patterns.md` — worked shapes: pipeline, fan-out, supervisor, mesh, seam.
