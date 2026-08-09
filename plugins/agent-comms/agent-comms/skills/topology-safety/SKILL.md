---
name: topology-safety
description: |
  Make a multi-agent communication graph safe to run — detect and break message loops, enforce
  acyclicity, prune redundant edges, and size the rate limits and circuit breakers that stop a
  runaway ring before it burns a budget. Encodes production loop-breaking from a shipped
  multi-agent Slack bridge (per-pair sliding window, channel-wide circuit breaker, self-echo
  filtering, blocked permission-reply injection) alongside published results that graph pruning
  cuts spend by an order of magnitude while also defending two classes of adversarial attack.
  Use when a design has cycles, when agents are amplifying each other, when a bill spiked without
  more work getting done, or when checking whether a second agent can safely join a shared
  channel. Trigger with
  "agent loop", "runaway agents", "circuit breaker for agents", "prune agent edges",
  "detect message cycles", "rate limit between agents".
allowed-tools: Read, Glob, Grep
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code; no runtime dependencies. Analyses any described or discovered communication graph regardless of transport.
tags: [multi-agent, safety, loop-detection, rate-limiting, cost-control]
model: inherit
---

# Topology Safety — Cycles, Amplification, and the Bill

A communication graph with a cycle has no convergence guarantee. That is not a heuristic — it is the
stated reason the multi-agent-learning literature moved to directed acyclic graphs and enforced
acyclicity with an explicit constraint.

Cost follows the same shape. Published pruning work cut spend from roughly forty dollars to under six
on the same workload, a 28–72% token reduction, **and** defended two classes of adversarial attack in
the process. A redundant edge is both a line item and a path an adversarial message can travel.

## Overview

Four defences, applied in this order. Each catches what the previous one misses:

1. **Acyclicity** — remove the cycle at design time. Cheapest, and the only one that eliminates the
   failure rather than bounding it.
2. **Self-echo filtering** — an agent must never consume its own output as input.
3. **Per-pair rate limiting** — a sliding window per ordered agent pair. Breaks the two-agent ping-pong.
4. **Graph-wide circuit breaker** — a ceiling on total agent traffic in a window. Catches rings of
   three or more that the per-pair limiter structurally cannot see.

The fourth exists because of a specific production finding: a per-pair limit set generously enough to
allow normal two-agent conversation never trips on an A→B→C→A ring, because no single pair exceeds its
own budget. The ring is only visible in aggregate.

## Prerequisites

- A described or discoverable communication graph — nodes, directed edges, and what triggers each edge.
- For an existing system, the source tree. Glob and Grep locate send sites and subscription handlers.
- No credentials. This skill reads a graph and needs no authentication to any external service.

## Instructions

### Step 1: Build the directed graph

Enumerate every ordered pair that can produce a message. Read the send sites rather than trusting a
diagram — the edge that causes the outage is usually the one nobody drew.

Include the edges that are easy to forget: retry paths, error handlers that notify a peer, supervisor
callbacks, and any subscription an agent holds on a channel it also writes to.

### Step 2: Find the cycles

Run a depth-first search and report every directed cycle with its full path. Classify each:

| Cycle | Signature | Fix |
| --- | --- | --- |
| Self-loop | A→A | Self-echo filter on sender identity |
| Ping-pong | A→B→A | Per-pair sliding window, or make one direction terminal |
| Ring | A→B→C→A | Graph-wide circuit breaker; break the weakest edge |
| Diamond-with-return | A→{B,C}→D→A | Usually a supervisor callback; make the return a write, not a send |

### Step 3: Break, do not merely bound

Prefer removing the edge. A rate limit converts an infinite loop into an expensive one that terminates;
an acyclicity fix removes it. Bounding is the fallback for cycles that are genuinely required, not the
default treatment.

### Step 4: Prune redundant edges

An edge is redundant when removing it does not change any decision the graph makes. Classify each edge
as **decision-carrying** or **status-carrying**, and route status through a read rather than a send.
Method and caveats: `references/edge-pruning.md`.

### Step 5: Size the limiters

Set the two limits from measured normal traffic, never from a guess. Both are configurable and both
default on; disabling either is a recorded decision, not a convenience. Alternatively, where a cycle is
load-bearing, adapt the design to carry a hop counter so the loop terminates structurally rather than by
rate. Concrete production defaults and the reasoning behind them are in
`references/loop-breaking-patterns.md`.

## Examples

A per-pair sliding window sized for conversation, with a channel-wide ceiling above it. These are the
shipped defaults from a production multi-agent bridge:

```jsonc
{ "peerRateLimit":     { "count": 10, "windowMs": 60000 },   // per (channel, sender) pair
  "channelBreaker":    { "count": 40, "windowMs": 60000 },   // whole channel, all agents
  "allowBotIds":       ["U_OPS_BOT"],                        // opt-in, empty by default
  "selfEchoFilter":    ["bot_id", "app_id", "user"] }        // all three, not just one
```

Why the ring escapes the per-pair limit — three agents, each pair well under its budget:

```text
A→B 9/60s  ✓ under 10    B→C 9/60s  ✓ under 10    C→A 9/60s  ✓ under 10
total 27/60s of pure loop traffic, zero pairs tripped
channel breaker at 40/60s catches it; nothing else in this design can
```

A cycle report, path-complete so the weakest edge is choosable:

```text
CYCLE   supervisor → worker-a → notifier → supervisor
EDGES   3   TRIGGER  notifier posts completion; supervisor subscribes to completions
BREAK   notifier → supervisor   (status-carrying; supervisor can read task state instead)
```

## Error handling

- **Graph cannot be recovered from source** — report which send sites were found and which subscriptions
  are dynamic. An incomplete graph must be labelled incomplete; a cycle-free verdict on a partial graph
  is worse than no verdict.
- **Cycle is load-bearing** — some supervisor patterns genuinely require a return edge. Bound it with
  both limiters, require the return edge to be idempotent, and record why removal was rejected.
- **Limits already tripping in normal operation** — the limits are mis-sized, not the traffic. Measure
  the actual normal rate before raising anything, or the breaker becomes decorative.
- **A limiter is disabled to unblock a demo** — record it as an open finding. A disabled breaker with no
  trace is the state in which the next runaway happens.

## Validation

1. Verify the reported graph includes retry paths, error handlers, and supervisor callbacks.
2. Check every reported cycle carries its full path, not just a pair of endpoints.
3. Verify the self-echo filter matches on every identity field the transport can populate — matching one
   field leaves the others as bypasses.
4. Check that both limiters are set, and that the graph-wide ceiling sits above aggregate normal traffic
   and below the cheapest ring the graph admits.
5. Confirm no peer is trusted by default; cross-agent delivery is opt-in.

## Output

Emit a cycle report (one block per cycle, path-complete, with the recommended break and its rationale),
an edge table classifying each edge decision-carrying or status-carrying with a prune verdict, and the
two limiter settings with the measured traffic they were derived from. State the edge count before and
after pruning as two numbers.

## Boundaries

This skill analyses and recommends. It does not implement a limiter, generate transport code, or make a
guarantee about system behaviour — the pruning results cited above are published evidence from specific
benchmarks, not an assurance property of any particular deployment.

## References

- `references/loop-breaking-patterns.md` — the production defences, their defaults, and their limits.
- `references/cycle-detection.md` — building the graph, finding cycles, and choosing which edge to cut.
- `references/edge-pruning.md` — redundancy, the cost and adversarial-robustness evidence, and caveats.
