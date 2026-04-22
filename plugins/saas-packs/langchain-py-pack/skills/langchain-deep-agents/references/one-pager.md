# langchain-deep-agents — One-Pager

Build a LangGraph 1.0 Deep Agent — planner + subagents + virtual filesystem + reflection loop — without the state-growth and prompt-inheritance traps that ship with the blueprint.

## The Problem

Two pains bite every team that reproduces the late-2025 LangChain Deep Agents blueprint. **Virtual-FS state grows unboundedly (P51):** the planner and subagents all write scratch notes, plans, and intermediate drafts into `state["files"]`, and nothing ever evicts them. After 50 tool calls the checkpointed state is 8 MB; every `MemorySaver.put()` takes 400 ms; a run that started at 1.2 s per node visit ends at 2.5 s per node visit, and the trace viewer times out loading the thread. **Subagent persona leak (P52):** the default prompt-composition APPENDS the subagent's role message to the parent's system message instead of replacing it. The research-specialist subagent gets "You are a senior planner coordinating subagents…" followed by "You are a research specialist…" — and responds as the planner, producing generic task decomposition instead of the specific lookup you asked for.

## The Solution

This skill pins to LangGraph 1.0.x and walks through the canonical four-component Deep Agent pattern: **planner** (task decomposition, assign-to-subagent, revise-plan), **subagent pool** of 3-8 role-specialized workers constructed with EXPLICIT `SystemMessage` override (no parent-prompt inheritance, per P52), **virtual filesystem** (dict-backed `state["files"]` for small scratch, disk/object store for large artifacts, plus a cleanup node that evicts entries older than N steps — per P51), and a **reflection node** that diffs plan vs actual, decides replan / continue / end / escalate, with typical reflection depth 3-5. Checkpointing only on user-facing boundaries (not every node) to bound state-growth blast radius. Cross-links to `langchain-eval-harness` for trajectory-level evaluation of the full deep-agent loop.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Researchers, PhDs, and senior engineers building long-horizon autonomous agents that plan, delegate subtasks, work against a scratchpad filesystem, and reflect on progress — the "Deep Agent" pattern LangChain's research team published in late 2025 |
| **What** | Four-component architecture (planner / subagent pool / virtual FS / reflection), explicit `SystemMessage(override=True)` for every subagent, virtual-FS eviction policy, bounded reflection depth (3-5), checkpoint-on-boundary strategy, 4 references (architecture-blueprint, subagent-prompting, virtual-filesystem-patterns, reflection-loop) |
| **When** | After `langchain-langgraph-agents` (L26) and `langchain-langgraph-subgraphs` (L30 — subagent ≈ subgraph), when building multi-step autonomous research systems, long-horizon coding agents, or document-synthesis pipelines that require self-critique |

## Key Features

1. **Prompt composition that replaces, not appends** — every subagent built with explicit `SystemMessage(override=True)` so the "You are a research specialist" instruction wins; no planner-persona leak (P52)
2. **Virtual FS with eviction** — dict-backed `state["files"]` with a cleanup node that drops entries older than N steps or marked `done`; disk/object-store fallback for artifacts > 100 KB; checkpointing only on user-facing boundaries keeps `MemorySaver.put()` under 50 ms (P51)
3. **Bounded reflection depth** — the reflection node compares plan vs actual, produces a plan-diff, and decides replan / continue / end / escalate in at most 3-5 rounds before surfacing to a human — no infinite self-critique loops

## Quick Start

See [SKILL.md](../SKILL.md) for the four-component construction walkthrough, the state-growth mitigation checklist, and the subagent handoff format.

## Pain-Catalog Anchors

- **P51** — Virtual FS unbounded growth, megabyte checkpoints, latency doubles over long runs
- **P52** — Subagent inherits parent system prompt, ignores its role-specific instruction
