# ADR: agent-comms — conform to A2A, and make the topology the product

**Author:** Jeremy Longshore
**Date:** 2026-08-09
**Status:** Accepted

## Context

Three forces met at once.

**A standard consolidated.** A2A absorbed its only real rival — ACP is archived and points at A2A's
migration guide — so "which agent-to-agent protocol?" stopped being an open question. At the same
time, a GitHub search across three phrasings found **no** Claude Code layer for it. A settled standard
with an empty adjacent surface is a narrow, time-boxed opening.

**The failures are not in the wire.** The literature (see `PRD.md` for the full citation table) puts
production multi-agent failure at 41–87%, attributes it mostly to coordination defects rather than
model capability, and names inter-agent misalignment as one of three top failure categories. Shipping
a protocol client alone would address the part that was already solved.

**A standing constraint from prior council rulings.** The agent-governance-plane's decision records
lock Q5: do not author or publish a rival spec or RFC — with the explicit carve-out that *conforming
to an existing open spec is not authoring one*. The same rulings ban a set of stronger assurance terms
on public surfaces, and the CISO ruling holds that importing an unsigned external manifest is a
governance-bypass / confused-deputy primitive. **An A2A agent card is exactly such a manifest.**

Doing nothing means the beachhead closes and the coordination layer stays undiagnosable.

## Decision

**We ship an `agent-comms` category anchored by one pack that conforms to A2A and treats coordination
topology — not message plumbing — as the product.**

Concretely:

1. **Conform, never specify.** Every wire shape is read from the published A2A spec. The pack defines
   no format, version, or registry, and makes no conformance-certification claim. The mailbox is
   labelled an implementation in its own skill body, its reference doc, and its eval spec.
2. **Turn the CISO ruling into a product feature.** A fetched agent card is untrusted input. The
   `a2a-agent-card` skill, the `a2a-card-auditor` agent, and every MCP tool **report** claims and
   never convert one into local authority. There is deliberately **no trust score** — a single number
   invites automating the decision that must stay with an operator.
3. **Make topology the defensible middle.** `comms-topology` decides the shape; `topology-safety`
   makes it safe to run, encoding production loop-breaking (per-pair sliding window, graph-wide
   circuit breaker, self-echo filtering on every identity field, approval checked at the gate,
   non-sticky peers) alongside DAG enforcement and redundancy pruning from the literature.
4. **Position beside, not inside, the governance plane.** The agent-governance-plane's unbuilt "Intent
   Graph" slice (agent discovery, message passing, dependency graph) remains its own concern. This
   pack is the client/skill layer. AGP answers *"may this happen, and is it recorded?"*; this pack
   answers *"how does agent A reach agent B?"* AGP's only wire today is a four-kind sandbox↔daemon
   triad with no messaging, addressing, or discovery — the two do not collide.

## Alternatives considered

| Alternative | Why rejected |
| --- | --- |
| Define our own lightweight agent-messaging spec | Violates the Q5 lock outright, and competes with a 25k-star Linux Foundation standard that already won. Conforming is both permitted and strictly better positioned. |
| Ship only the A2A client, no topology skills | Addresses the solved half. The literature puts failure in coordination, not in message format; a client alone leaves the actual defect class untouched. |
| Build on ACP as well, "for coverage" | ACP is archived and redirects to A2A. Dual support would be maintenance cost for a dead standard. |
| Auto-configure from a fetched agent card (adopt capabilities, use declared URLs) | The convenient design, and a confused-deputy primitive. It hands a remote party the local agent's authority via a document they author. Rejected on the CISO ruling. |
| Emit a card trust score | Compresses a decision into a number, which invites automating it. Enumerated claims plus explicit dispositions keep the operator in the loop where the ruling puts them. |
| Fold this into the agent-governance-plane | Different question and different layer. AGP governs whether an action may happen; this routes messages between agents. Merging would blur a boundary AGP's own ADRs draw. |

## Consequences

**Positive:**

- First Claude Code layer for the one surviving agent-to-agent standard, shipped while the surface is
  still empty.
- The security posture is a differentiator rather than a tax: no competitor treats the agent card as
  untrusted input, and the CISO ruling produced a design nobody else has.
- The topology skills are defensible independent of A2A's fortunes — the failure modes they address
  exist in any multi-agent system, protocol or not.
- Every claim in the pack is sourced. The cost, pruning, and failure-mode numbers carry citations, so
  a skeptical reader can check rather than trust.

**Negative / accepted tradeoffs:**

- **Friction by design.** A card audit that requires an operator decision is slower than
  auto-configuring. That is the point, and it will read as friction to someone who wanted one click.
- **Coupled to A2A's evolution.** The spec will move; the reference docs will need re-verification
  against the proto and prose spec each time. Conforming means inheriting someone else's release
  cadence.
- **Push-notification callbacks are unimplemented.** Receiving one needs an endpoint this pack does not
  own, so four of the eleven A2A methods are reachable through the SDK but not exposed as tools.
- **Six skills is a pack, not a micro-skill.** It carries the full submission-doc tier and a larger
  maintenance surface than a single-skill plugin.
- **The literature is evidence, not assurance.** Pruning reduced attack success in one study on one
  benchmark set. Copy must say "evidence" and never drift into a guarantee — which constrains how
  strongly the pack can be marketed.

## Tool-permission scope

| Skill | Tools | Why |
| --- | --- | --- |
| `a2a-protocol` | `Read`, `mcp__a2a-client__{fetch_agent_card,send_message,stream_message,get_task,cancel_task}` | Reads its own references; the MCP tools are the live-call path. No write tools — this skill explains and calls, it does not author. |
| `a2a-agent-card` | `Read`, `Write`, `Edit`, `mcp__a2a-client__{fetch_agent_card,validate_agent_card}` | Authoring a card needs `Write`/`Edit`; auditing needs `Read` plus the two read-only MCP tools. Messaging tools are deliberately absent — auditing a card must not be able to talk to the agent. |
| `comms-topology` | `Read`, `Glob`, `Grep`, `AskUserQuestion` | Recovers an existing call graph from source and asks rather than assumes on unstated axes. No write tools: it designs, it does not implement. |
| `topology-safety` | `Read`, `Glob`, `Grep` | Analysis only. Recommending a limiter is not installing one. |
| `agent-mailbox` | `Read`, `Write`, `Glob`, `Bash(mkdir:*)`, `Bash(mv:*)`, `Bash(ls:*)` | The mailbox *is* directories and renames. Bash is scoped to the three verbs the protocol uses — bare `Bash` would be far wider than the mechanism needs. |
| `mas-failure-triage` | `Read`, `Glob`, `Grep` | Reads traces and artifacts. A diagnostic that can modify the system under diagnosis is a worse diagnostic. |

| Agent | Tools | Why |
| --- | --- | --- |
| `a2a-card-auditor` | `Read`, `mcp__a2a-client__{fetch_agent_card,validate_agent_card}`; `disallowedTools: Write, Edit, WebFetch` | The "report, never adopt" rule is enforced by capability, not by instruction: it holds no tool that could change local state, and `WebFetch` is denied so it cannot resolve a URL the card names. |
| `topology-advisor` | `Read`, `Glob`, `Grep`, `AskUserQuestion`; `disallowedTools: Write, Edit, Bash` | Advisory by construction. |
