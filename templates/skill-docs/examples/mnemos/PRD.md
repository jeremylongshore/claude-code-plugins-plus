# PRD: mnemos

**Author:** André Figueira (Polyx Media)
**Date:** 2026-07-07
**Status:** Active

> Worked example: reconstructed by the marketplace maintainers from the upstream
> `polyxmedia/mnemos` SKILL.md, README, and plugin.json at HEAD. Every number below is an
> upstream-published measurement, not a marketplace claim.

## Problem

AI coding agents forget conventions, corrections, and architectural decisions between
sessions, so users re-teach the same fixes over and over. Worse: even when a persistent
memory store is available as MCP tools, agents almost never record to it unprompted —
upstream measured a 7% baseline capture rate for correction-shaped signals, and the store
itself contains a recorded correction about the exact failure mode ("agent skipped
`mnemos_session_start` on editing tasks"). Without a behavioral layer that forces the
learning loop, the memory store sits empty and every session starts blind.

## Target users

| User                                           | Context                                                                                  | Primary need                                                                        |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| Solo developer on a long-lived repo            | Multi-session Claude Code work where the same corrections and conventions keep repeating | Record a correction once, have it surface automatically next session                |
| Claude Code user with mnemos already installed | The `mnemos_*` MCP tools are wired but the agent silently edits and never calls them     | An external nudge that makes the agent actually record and recall                   |
| Developer working across MCP hosts             | Same project rules re-taught to Claude Code, Cursor, Windsurf, and Codex CLI separately  | One local store the same MCP server serves to every host, plus portable skill packs |

## Success criteria

1. On the upstream `mnemos verify behavior` harness (Claude Code, n=5 paired runs), the
   skill-on arm matches the published result: 25/25 scenario compliance vs 15/25 with
   mnemos off — a +40% overall lift, concentrated on project-specific conventions and the
   recursive "agent forgets to use its own memory tools" case.
2. On `mnemos verify capture`, correction-shaped signals in user prompts are recorded at
   the published 53% (8/15) rate with the UserPromptSubmit capture directive — against
   the 7% baseline without it.
3. No dangling sessions: `mnemos_stats` at the top of a new session shows zero open
   sessions left behind by a skill-guided prior session (every opened session is closed
   via `mnemos_session_end` with a summary and status).
4. The prewarm context block stays inside its 500-token default budget (upstream measured
   ~20 tokens on an empty store, ~460 populated).

## Functional requirements

- **FR-1:** At session start, reuse the `mnemos_session_id` injected by the SessionStart
  prewarm hook; call `mnemos_session_start(project, goal)` only when no ID is present and
  real work is about to happen.
- **FR-2:** Record durable signals with the matching tool: `mnemos_correct`
  (tried / wrong_because / fix) for genuine corrections, `mnemos_convention` for
  project-forever rules, `mnemos_save` for decisions, patterns, and architecture calls.
- **FR-3:** Close every session on a done signal via `mnemos_session_end` with a one-to-two
  sentence summary and a status of `ok` / `failed` / `blocked` / `abandoned`.
- **FR-4:** Run the rumination workflow when stored rules are flagged —
  `mnemos_ruminate_list` → `mnemos_ruminate_pack` → resolve (with a falsifiable
  `why_better`) or dismiss (with an honest reason); never close a candidate silently.
- **FR-5:** Fail loudly when `mnemos_*` tools are not visible: direct the user to
  `mnemos doctor` / `mnemos init` rather than silently proceeding without memory.

## Out of scope

- The memory engine itself — storage, ranking, consolidation, the prompt-injection
  scanner, and the verify harness ship in the separate mnemos Go binary / MCP server, not
  in this skill.
- Installing the binary or wiring agent hosts — `mnemos init` and the installer own that;
  the skill only points at `mnemos doctor` when tools are missing.
- Ephemeral within-session notes — the skill explicitly forbids saving running commentary
  ("I'm reading X now") to the store.
- Retrieval tuning (hybrid alpha, embedding providers, token budgets) — configuration
  surface of the engine, not skill behavior.
