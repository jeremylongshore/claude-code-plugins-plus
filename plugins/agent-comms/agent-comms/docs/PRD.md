# PRD: agent-comms

**Author:** Jeremy Longshore
**Date:** 2026-08-09
**Status:** Active

## Problem

Multi-agent systems built in Claude Code fail at the coordination layer, and the tooling to reason
about that layer does not exist.

Two gaps, both verified rather than assumed.

**The interoperability gap.** Agent2Agent (A2A) is the surviving open agent-to-agent standard —
25,261 stars, Linux Foundation, official SDKs in seven languages. Its predecessor ACP is **archived**;
its README now redirects to A2A's migration guide, so there is exactly one standard rather than a
contested field. Searching GitHub on 2026-08-09 for "a2a claude code skill", "agent2agent claude
code", and "a2a agent card claude" returned **zero results** across all three. A 25k-star protocol had
no Claude Code layer.

The apparent competition does not close it: the packages a survey pointed at were either nonexistent
(`elijahmuraoka/agent-comms` — 404), one day old with single-digit stars (`getbeb/beb` at ★0,
`aimebu` at ★4, both created 2026-08-08), or a different problem entirely (`smux`, ★1,504, terminal
multiplexing).

**The coordination gap, which is the larger one.** The failure literature is consistent about where
multi-agent systems break:

- *Coordination as an Architectural Layer* (arXiv:2605.03310): production failure rates of **41–87%**,
  "mostly due to **coordination defects** rather than base-model capability."
- MAST (Cemri et al., arXiv:2503.13657, NeurIPS 2025, ~498 citations): 14 failure modes over 1,600+
  traces; **inter-agent misalignment** is one of three top categories — failures that live in the
  conversation, where tuning either agent cannot reach them.
- AgentPrune (arXiv:2410.02506, ICLR, ~121 citations): communication-graph pruning held quality at
  **$5.6 vs $43.7**, cut tokens **28–72%**, and **defended two classes of adversarial attack**.
- DHCG (IJCAI 2023): message passing on a cyclic graph "cannot guarantee convergence."
- ESRH (arXiv:2512.02682): "local compliance can aggregate into collective failure even when every
  model is individually aligned."

Local scar tissue agrees. In a shipped multi-agent Slack bridge, a per-pair rate limit sized correctly
for two-agent conversation never fired on a three-agent ring — no single pair exceeded its budget
while the aggregate ran away. That bug is invisible at the message layer and obvious at the graph
layer.

## Target users

| User | Context | Primary need |
| --- | --- | --- |
| Integrator connecting to a third-party agent | A partner exposes an A2A agent; the card is theirs, the risk is ours | Speak the protocol correctly, and audit the card without letting it widen local authority |
| Engineer designing a multi-agent system | Three-plus agents, unclear whether a broker is warranted | A decision, not a survey: the cheapest topology that survives the workload, priced in edges |
| Operator whose run failed or whose bill spiked | Agents looped, ignored each other, or returned confident garbage | A named failure mode with a fix routed to the right level, and the cycle broken rather than bounded |
| Agent author publishing a card | Wants other agents to discover real capabilities | Author a card that does not over-claim, since over-claiming reads as an outage on every caller |

## Success criteria

1. Every skill grades **A at marketplace tier with zero errors** under
   `validate-skills-schema.py --marketplace`, and both agents pass `--agents-only`. **Met: 6/6 skills
   at 100/100.**
2. The MCP client completes a full A2A flow against a reference agent — card fetch, `SendMessage`
   round-trip, streamed call, `GetTask` to a terminal state, and `CancelTask` on a live task — with
   errors surfaced verbatim rather than swallowed. **Met: 22/22 assertions against a reference agent
   built on the official `@a2a-js/sdk` server module.**
3. No public surface of the pack contains a banned assurance term, and no text describes the mailbox
   as a specification.
4. A card audit never mutates local configuration, and never emits a trust score — asserted by test,
   not by convention.

## Functional requirements

- **FR-1:** Cover the 11-method A2A service surface, the task-state classes (terminal / interrupted /
  live), the three protocol bindings, and the `-32001`–`-32009` error mapping, sourced from the
  published spec rather than paraphrase.
- **FR-2:** Author and audit agent cards, treating every fetched card as untrusted input — enumerate
  claims, flag private-range and plaintext interface URLs, detect per-skill security overrides that
  weaken the agent-level baseline, and report signature status three-valued.
- **FR-3:** Choose a topology by scoring eight axes and running four elimination rules in cost order,
  committing to exactly one shape with a stated edge count and a named migration trigger.
- **FR-4:** Detect cycles, classify each by shape, prefer breaking the edge over bounding the loop,
  prune redundant edges, and size both a per-pair window and a graph-wide circuit breaker.
- **FR-5:** Diagnose a failed run against the 14 MAST modes from the **first divergence**, and route
  the fix to the level the failure category names.

## Out of scope

- **Authoring a specification.** This pack conforms to A2A. It publishes no wire format, version
  number, or registry, and invites no conformance. The mailbox is explicitly an implementation.
- **Any conformance-certification claim**, including toward Microsoft's Agent Control Specification.
- **Governance.** Policy verdicts, audit journals, and approval gates belong to the
  agent-governance-plane. This pack answers "how does agent A reach agent B?", never "may this happen,
  and is it recorded?"
- **Running a broker, a registry, or a signing service.** The mailbox is a directory; the client is a
  client.
- **Push-notification callback receipt.** An inbound callback needs an endpoint this pack does not own.
