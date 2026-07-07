# mnemos

**Persistent memory for Claude Code — corrections, conventions, and decisions that survive the session, with a harness that measures the lift instead of claiming it.**

## Problem

Claude Code forgets conventions, corrections, and architectural decisions between
sessions, and even with a memory store wired in as MCP tools, agents almost never record
to it on their own — upstream measured a 7% baseline capture rate. The store sits empty,
and every session starts blind.

## Solution

The mnemos skill is the behavioral layer over the mnemos memory engine (a single static
Go binary serving MCP tools). A SessionStart hook prewarms a token-budgeted context block
of conventions, corrections, and hot files; a UserPromptSubmit hook turns
correction-shaped prompts into a non-skippable capture directive; the skill tells the
agent which tool answers which signal — record corrections as structured
tried / wrong_because / fix entries, save decisions, close sessions with summaries, and
hostile-review stale rules through the rumination workflow. Three clustered corrections
auto-promote into a skill deterministically, so the next session starts smarter.

## W5

|           |                                                                                                                                                                       |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Who**   | Claude Code users running the mnemos MCP server (the same server also works in Claude Desktop, Cursor, Windsurf, and Codex CLI)                                       |
| **What**  | Makes the agent actually use its memory: open/reuse sessions, record corrections, conventions, and decisions, close with summaries, and review flagged rules          |
| **When**  | Every session — at start (reuse the prewarm session ID), on any genuine correction or architectural call, and at session end                                          |
| **Where** | Claude Code with `mnemos serve` wired by `mnemos init`; all state local in `~/.mnemos/mnemos.db` (SQLite), nothing leaves the machine by default                      |
| **Why**   | Agents skip optional memory calls (7% capture baseline); the skill + hooks raise recorded corrections to 53% and deliver a measured +40% behavior lift on paired runs |

## Stack

| Layer         | Choice                                                                                          |
| ------------- | ----------------------------------------------------------------------------------------------- |
| Skill runtime | Claude Code SKILL.md (single skill, no bundled scripts)                                         |
| Memory engine | mnemos — single static, CGO-free Go binary (~15 MB), MCP over stdio                             |
| Storage       | SQLite + FTS5 via pure-Go `modernc.org/sqlite`, bi-temporal schema, local `~/.mnemos/mnemos.db` |
| Capture hooks | Claude Code SessionStart (`mnemos prewarm`) + UserPromptSubmit capture directive                |
| Retrieval     | BM25 + optional cosine similarity via Reciprocal Rank Fusion (Ollama auto-detected)             |
| External APIs | None by default (opt-in: Ollama/OpenAI embeddings, HTTP transport)                              |
| Tool scope    | `mcp__mnemos` only — no Bash, no filesystem tools                                               |

## Differentiators

1. **Measured, not claimed.** Ships `mnemos verify`: Claude run twice on a fixed scenario
   set, on vs off — 25/25 vs 15/25 behavior compliance (+40%), capture 7% → 53%. The
   fixtures and runner are in the repo; the numbers are reproducible, including the ones
   that are still ugly (architectural-decision capture: 0/3).
2. **Deterministic learning loop.** Three corrections clustering on the same agent,
   project, and topic promote into a skill by clustering + templating — no LLM inside the
   memory layer, same input always yields the same output — and revising a flagged rule
   requires stating a new falsifiable prediction (a Popperian guard at the tool boundary).
3. **Zero-dependency and local-first.** One curl or brew install, no runtime, five agent
   hosts wired by `mnemos init`; a write-time prompt-injection scanner guards the store,
   and no network calls happen unless you opt in.
