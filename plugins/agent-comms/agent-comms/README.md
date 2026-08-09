<h1 align="center">agent-comms</h1>

<p align="center">
  Six skills that make Claude Code a first-class <strong>Agent2Agent (A2A)</strong> participant and
  treat <strong>coordination topology — not message plumbing — as the product</strong>.<br>
  Multi-agent systems fail in production far more often from coordination defects than from weak
  models. This pack works the layer where those defects actually live.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-10b981?style=flat-square" alt="License: MIT">
  <img src="https://img.shields.io/badge/skills-6%20%C3%97%20grade%20A-8b5cf6?style=flat-square" alt="6 skills, all grade A">
  <img src="https://img.shields.io/badge/A2A-conformant%2C%20not%20a%20spec-0ea5e9?style=flat-square" alt="A2A conformant, not a spec">
  <img src="https://img.shields.io/badge/cards-untrusted%20input-f59e0b?style=flat-square" alt="cards are untrusted input">
</p>

---

## Why this pack exists

Two facts, both checkable.

**One: A2A won, and nobody built the Claude Code layer.** The Agent2Agent protocol sits at 25k+ stars
under the Linux Foundation with official SDKs in seven languages. Its predecessor, ACP, is archived —
its own README now points at A2A's migration guide. So there is exactly **one** agent-to-agent
standard. Searching GitHub for a Claude Code skill covering it returns nothing.

**Two: the hard part was never the wire.** The published failure literature is blunt about where
multi-agent systems actually break:

| Finding | Source |
|---|---|
| Multi-agent LLM systems fail in production at **41–87%**, "mostly due to **coordination defects** rather than base-model capability"; coordination is "a configurable architectural layer, separable from agent logic" | *Coordination as an Architectural Layer*, arXiv:2605.03310 |
| **14 failure modes** over 1,600+ traces; one of three top categories is **inter-agent misalignment** — failures that live in the conversation, not in either agent | MAST — Cemri et al., arXiv:2503.13657, NeurIPS 2025 (~498 citations) |
| Graph pruning held task quality at **$5.6 vs $43.7**, cut tokens **28–72%**, and **defended two classes of adversarial attack** | AgentPrune — *Cut the Crap*, arXiv:2410.02506, ICLR (~121 citations) |
| "Message-passing update in the **undirected graph with cycles cannot guarantee convergence**" — hence directed acyclic graphs with an explicit acyclicity constraint | DHCG, IJCAI 2023 |
| "Local compliance can aggregate into **collective failure** even when every model is individually aligned" | ESRH — *Beyond Single-Agent Safety*, arXiv:2512.02682 |

Read together: the message format is solved (A2A), and the failures are in the **graph**. So this pack
ships conformance to the standard *and* the topology judgment that the standard deliberately leaves
open.

## The six skills

| Skill | What it decides | Anchor |
|---|---|---|
| **`a2a-protocol`** | Which binding to speak, which interaction shape to use, and what a task state actually means | The 11-method A2A service surface; terminal vs interrupted vs live states; the `-32001`–`-32009` error mapping |
| **`a2a-agent-card`** | What a remote agent claims — and what stays a claim | Required fields, per-skill security overrides, three-valued signature honesty. Ships the `a2a-card-auditor` agent |
| **`comms-topology`** | Direct, mailbox, bus, or protocol — the cheapest shape that survives the workload | Eight axes, four elimination rules in cost order, edge counts. Ships the `topology-advisor` agent |
| **`topology-safety`** | Whether the graph is safe to run | Cycle detection, DAG enforcement, edge pruning, and the two-tier limiter that catches rings a per-pair limit structurally cannot see |
| **`agent-mailbox`** | How to hand off durably with zero infrastructure | Atomic-rename writes, `mv`-as-lock claiming, at-least-once with idempotency, and an honest list of when to use something else |
| **`mas-failure-triage`** | What actually went wrong in a failed run | The 14 MAST modes; diagnose at the first divergence, route the fix to the level the category names |

Every skill grades **A (100/100)** at marketplace tier and ships an `eval-spec.yaml` for behavioral
evaluation.

## The differentiator: a per-pair rate limit cannot see a ring

`topology-safety` encodes production loop-breaking from a shipped multi-agent Slack bridge, and the
sharpest lesson in it is structural:

```text
A→B 9/60s  ✓ under 10    B→C 9/60s  ✓ under 10    C→A 9/60s  ✓ under 10
27 msgs/60s of pure loop traffic — and not one pair tripped its limit
```

A per-pair limiter sized generously enough for real conversation **never fires on an A→B→C→A ring**,
because no individual pair exceeds its own budget. Only a graph-wide circuit breaker sees it. The
shipped defaults — 10 per pair per 60s, 40 channel-wide per 60s — sit either side of exactly that gap.

The full stack is six layered defences, each catching what the previous one misses: default-deny on
peer agents → self-echo filtering on every identity field → per-pair window → graph-wide breaker →
approval checked at the gate (so a peer agent cannot inject an approval reply) → non-sticky peers.

## Boundaries — stated, not implied

- **This pack conforms to A2A. It does not author a specification.** No wire format, no version
  number, no registry, no conformance-certification claim. The mailbox is explicitly an
  *implementation*, not a spec: not versioned, not offered for adoption.
- **An agent card never becomes local authority.** Claims are reported; adoption is an operator
  decision recorded outside the card. No trust score is emitted, anywhere.
- **Evidence, not assurance.** The pruning and cost results above are published benchmark findings.
  They are cited as evidence and never restated as a guarantee about any deployment.

## Install

```
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install agent-comms
```

The live-call path additionally wants the [`a2a-client`](../../mcp/a2a-client) MCP server, which
wraps the official `@a2a-js/sdk` and is verified end-to-end against a reference A2A agent. Without it
every skill still works — they answer from `references/` and emit request shapes to run by hand.

## Docs

| Doc | What it proves |
|---|---|
| [`docs/PRD.md`](./docs/PRD.md) | The problem is real, the users exist, success is measurable |
| [`docs/ADR.md`](./docs/ADR.md) | The design was a decision — including why this conforms rather than specifies, and how it sits beside the agent-governance-plane |
| [`docs/ONE-PAGER.md`](./docs/ONE-PAGER.md) | An installer in a hurry can evaluate it from one screen |

## License

MIT
