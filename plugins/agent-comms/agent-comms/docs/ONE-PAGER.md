# agent-comms

**Speak Agent2Agent from Claude Code, and design the coordination graph that decides whether your
multi-agent system works.**

## Problem

Multi-agent systems fail in production at 41–87%, and the published analysis attributes it "mostly to
coordination defects rather than base-model capability." One of the three top failure categories is
inter-agent misalignment — defects that live in the conversation between agents, where tuning either
agent's prompt cannot reach them.

Meanwhile the interoperability question closed: A2A won (25k+ stars, Linux Foundation, seven SDKs) and
its predecessor ACP is archived, pointing at A2A's migration guide. As of 2026-08-09 there was **no
Claude Code layer for it** — three GitHub searches, zero results.

## Solution

Six A-grade skills plus a verified MCP client. Three of them make Claude Code a first-class A2A
participant — the 11-method service surface, agent-card authoring and auditing, and a client that
completes a real round-trip. The other three work the layer where systems actually break: choosing the
cheapest topology that survives the workload, detecting and breaking the cycles that make loops
unterminating, and diagnosing a failed run against 14 named failure modes.

## W5

| | |
| --- | --- |
| **Who** | Engineers integrating with a third-party agent, designing a multi-agent system, or debugging one that failed |
| **What** | A2A conformance (protocol, cards, client) plus coordination-topology design, safety, and failure triage |
| **When** | Before wiring agents together; when a partner exposes an agent; when a run loops, stalls, or bills without shipping |
| **Where** | Claude Code, any repo. Live A2A calls go through the `a2a-client` MCP server; everything else runs with no dependencies |
| **Why** | The wire format is solved and the graph is not — this ships conformance to the standard *and* the judgment the standard leaves open |

## Stack

| Layer | Choice |
| --- | --- |
| Skill runtime | Claude Code `SKILL.md` — 6 skills, 18 reference documents, 2 agents |
| Protocol | Agent2Agent (A2A) v1.0 — conformed to, never redefined |
| Live-call path | `a2a-client` MCP server wrapping the official `@a2a-js/sdk@1.0.1` |
| Behavioral eval | `eval-spec.yaml` per skill, for j-rig |
| External services | None. The topology, mailbox, and triage skills have zero runtime dependencies |

## Differentiators

1. **The agent card is untrusted input — and that is a feature, not a caveat.** Every other agent-comms
   package treats a fetched card as configuration. This one treats it as a confused-deputy primitive:
   claims are enumerated and reported, private-range and plaintext interface URLs are flagged, per-skill
   security overrides that weaken the agent-level baseline are surfaced, an unverifiable signature is
   reported `unverified` and never `valid` — and no trust score is ever emitted, because a single
   number invites automating the decision that must stay with an operator. The auditing agent holds no
   write tools and cannot fetch a card-named URL, so the rule is enforced by capability rather than by
   instruction.

2. **A per-pair rate limit cannot see a three-agent ring.** With a limit of 10 messages per pair per
   minute, an A→B→C→A loop can sustain 27 messages a minute of pure loop traffic without tripping a
   single pair. Only a graph-wide circuit breaker catches it. `topology-safety` ships that two-tier
   design with the production defaults either side of the gap (10 per pair, 40 graph-wide, per 60s), on
   top of DAG enforcement and edge pruning — pruning that published work shows cuts spend from $43.7 to
   $5.6 **and** defends two classes of adversarial attack. Fewer edges is cheaper *and* safer.

3. **Every claim is sourced, and the boundaries are stated rather than implied.** Failure rates,
   failure modes, cost figures, and the convergence argument all carry citations a skeptic can check.
   The pack conforms to A2A and says plainly that it authors no specification; the mailbox is labelled
   an implementation, not a spec; benchmark results are cited as evidence and never restated as a
   guarantee. Verification is the same: 6/6 skills at 100/100 marketplace grade, and 22/22 end-to-end
   assertions against a reference A2A agent — not "verified," but verified against a named target with
   a stated result.
