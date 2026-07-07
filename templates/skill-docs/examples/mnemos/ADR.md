# ADR: mnemos — dependency-free Go binary, hook-driven capture, local-first storage

> Worked example: this decision record is reconstructed from the upstream
> `polyxmedia/mnemos` repository (README "Design" and "Architecture" sections, SKILL.md,
> and decisions the store itself records) — the design as shipped, read back as the
> decision it was.

**Author:** André Figueira (Polyx Media)
**Date:** 2026-07-07
**Status:** Accepted

## Context

A memory layer for coding agents only works if it is present at every session start with
near-zero friction, if anything actually gets _written_ to it, and if what is written can
be trusted when it re-enters context later. Three forces shape the design: (1) the engine
must install and run identically across five agent hosts (Claude Code, Claude Desktop,
Cursor, Windsurf, Codex CLI) on Linux/macOS/Windows without a language runtime on the
user's machine; (2) agents skip optional tool calls — upstream measured a 7% baseline
capture rate, so prompting alone demonstrably does not produce a learning loop; (3) a
memory store is a write-time prompt-injection attack surface, and anything non-local or
non-deterministic makes the pipeline unauditable.

## Decision

Ship the engine as a **single static, CGO-free Go binary** (~15 MB) exposing MCP tools
over stdio, with state in a **local SQLite + FTS5 database** (`~/.mnemos/mnemos.db`,
pure-Go `modernc.org/sqlite` driver, bi-temporal schema). Make capture **structural, not
optional**: a Claude Code SessionStart hook (`mnemos prewarm`) injects a token-budgeted
context block and opens the session, and a UserPromptSubmit hook pattern-matches
correction-shaped prompts and emits a `[mnemos: capture required]` directive. This
SKILL.md is the behavioral layer that tells the agent which tool answers which signal.
Consolidation (three clustered corrections → one promoted skill) is deterministic
clustering + templating — no LLM inside the memory layer. Nothing leaves the machine by
default.

## Alternatives considered

| Alternative                                       | Why rejected                                                                                                                                                                                                                                 |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Node or Python MCP server                         | Adds a language runtime + dependency tree to every user machine; install friction and version drift defeat "memory is always there." A static binary wired by `mnemos init` needs neither.                                                   |
| Skill/prompt-only capture (no hooks)              | Measured insufficient: capture sat at 7% baseline and tuning trigger phrases gained only a few points. The UserPromptSubmit directive — a structural fix — moved it to 53%.                                                                  |
| LLM-in-the-loop consolidation and memory curation | Non-deterministic and unauditable: a model deciding "what counts as similar enough" gives different skills from the same corrections. Deterministic clustering + templating yields the same output for the same input, end-to-end auditable. |

Within the binary itself, the CGO SQLite driver (`mattn/go-sqlite3`) was also rejected —
the repo records this decision verbatim: the pure-Go driver "keeps the binary CGO-free
and cross-compilable to linux/darwin/windows without a toolchain on the install path";
zero-CGO is a hard invariant.

## Consequences

**Positive:**

- One-command install (curl script or Homebrew), one binary serving five agent hosts;
  `mnemos update` self-updates with sha256 verification.
- Capture becomes structural: the hook path raised recorded corrections from 7% to 53%,
  and the paired-run behavior harness shows +40% overall lift (25/25 vs 15/25).
- Deterministic, auditable pipeline — same corrections always promote the same skill; the
  write-time prompt-injection scanner sanitizes or flags hostile content before it can
  re-enter context.
- Local-first by default: no network calls unless the user opts into OpenAI embeddings or
  the HTTP transport.

**Negative / accepted tradeoffs:**

- The hook mechanism is Claude Code-specific; other hosts fall back to skill-instructed
  `mnemos_session_start`, a weaker capture path. Accepted: Claude Code is the primary
  target and the MCP tools still work everywhere.
- Capture is not solved — 53% overall, and architectural decisions buried inside larger
  task prompts still sit at 0/3 even with the directive. Accepted and documented openly
  upstream as an open problem.
- Pure-Go SQLite trades some raw performance against the CGO driver; cross-compilation
  without a toolchain was judged worth more.
- Retrieval falls back to pure FTS5 (BM25) when Ollama is unreachable, so paraphrased
  queries rank worse without embeddings. Accepted: fine for most projects.

## Tool-permission scope

The skill's frontmatter declares exactly one entry — least privilege in its strictest
form: no `Bash`, no `Read`/`Write`, no filesystem or shell access at all.

| Tool          | Why it's needed                                                                                                                                                                                                                                                                                                                       |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mcp__mnemos` | The entire skill surface is the mnemos MCP server's tools (`mnemos_session_start/end`, `mnemos_save`, `mnemos_correct`, `mnemos_convention`, `mnemos_search`, `mnemos_ruminate_*`, …). All persistence crosses the MCP boundary, where the write-time prompt-injection scanner runs — the skill never touches disk or shell directly. |
