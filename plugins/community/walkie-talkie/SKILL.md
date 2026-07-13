---
name: walkie-talkie
description: Use when two or more agent sessions — same or different platforms (Claude Code, Codex, Gemini CLI, Copilot, Cursor) — work the same repo concurrently, hand off in-flight work, or need to interrogate each other about a handoff. Triggers: "set up comms with the other session", "hand this off to Codex/Gemini", "grill the handoff", "check the mailbox", parallel sessions clobbering shared files, resuming work another agent left half-done.
---

# Walkie-Talkie

## Overview

An append-only file mailbox, committed to the repo, that lets agent sessions communicate across platforms, machines, and time. Any agent that can read and write files can participate — no shared harness, API, or memory required. Git is the transport; the human audits both channels.

**Core invariant: one writer per file, append-only.** Each agent owns exactly one outbox file. Nobody ever edits another agent's outbox, and nobody ever rewrites a past entry. This designs merge conflicts and clobbering out of existence.

**Why a fixed protocol matters:** unaided agents invent *good but incompatible* mailbox formats. The value of this skill is convergence — every session that loads it speaks the same format, so channels compose across sessions that have never met.

## When to Use

- Heterogeneous agents (Claude + Codex + Gemini…) sharing one repo
- Handoff of in-flight work to a session that starts later
- Parallel sessions on the same repo needing to coordinate shared surfaces
- Cross-machine coordination (git push/pull moves the mailbox)

**When NOT to use:** Claude Code sessions in the same harness on the same machine — use Agent Teams / SendMessage instead (push notifications beat polling). One-shot handoff with no return channel and nothing contested — a plain HANDOFF.md is enough, though the Grill (below) still applies on receipt.

## Setup (first agent creates the channel)

1. Create `comms/` next to the work it coordinates (repo-wide: `.agents/comms/`; sprint-scoped: `docs/<area>/comms/`).
2. Copy [PROTOCOL_TEMPLATE.md](PROTOCOL_TEMPLATE.md) into it as `README.md`, filling in the agent handles.
3. Create one outbox per agent, named `<HANDLE>.md` (e.g. `FABLE.md`, `CODEX.md`). Initialize peers' outboxes with a one-line pointer to the README so their first read routes them in.
4. Add a discovery shim to every bootstrap file the participating platforms auto-read — `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`: *"In-repo agent mailbox at `<path>/comms/` — read its README.md and your inbox before changing anything. MANDATORY."*
5. Write your first entry: repo state, in-flight work with exact `file:line` for load-bearing state, known unknowns, and any `ACTION-REQUESTED`.
6. Commit the mailbox together with (or immediately after) the code it describes.

## Message Format

Append to YOUR OWN outbox only:

```markdown
## [2026-07-03 14:05] STATUS: eval-surface rotation half-applied
Re: —

The 7-match gate is now the ONLY confirmation surface (src/ranker.py:4).
build_cache() sort order is stale vs the bounce rule — main outstanding fix.
```

Header: `## [YYYY-MM-DD HH:MM] TYPE: subject`. `Re:` names the entry being answered (by timestamp+subject), or `—`.

| Type | Meaning |
|---|---|
| `STATUS` | What I did / left half-done / decided. The workhorse. |
| `ACTION-REQUESTED` | Peer must act or explicitly decline. Highest priority. |
| `QUESTION` / `ANSWER` | Async request/response. ANSWER always sets `Re:`. |
| `GRILL` | Handoff interrogation — evidence required (see below). |
| `EVIDENCE` | Reply to a GRILL. Command output, SHAs, file:line — not assurances. |
| `CLAIM` / `RELEASE` | Advisory lock on a named surface (exact paths). |
| `ACK` | Received and understood; nothing further. |

## Checkpoint Discipline

Read every peer outbox at: **session start**, **before starting a new slice of work**, **after completing one**. Answer open `ACTION-REQUESTED` and `GRILL` items addressed to you before starting new work. Write whenever you have verdicts, needs, or plans affecting shared surfaces, caches, or artifacts — not just at session end.

## The Grill

On receiving a handoff, do not ACK politely — interrogate. Post a `GRILL` entry with pointed questions; the handing-off agent (this session or its next incarnation) must answer each with `EVIDENCE`, not assurances. Minimum grill set:

1. What did you **verify by running something** vs. merely believe? Show the command and output.
2. What is **half-applied** right now? Exact file:line of every load-bearing edit.
3. What breaks if I touch X? Which surfaces are **claimed**?
4. What do you know that is **written down nowhere** but this mailbox?
5. What would you check first if this were broken tomorrow?

Any grill question that cannot be answered with evidence is recorded as a **RISK** in the answering entry — never silently dropped. Unanswered grills block `RELEASE` of the affected surface.

## Rules

- Append-only. Never edit or delete a past entry (corrections are new entries with `Re:`).
- Never write to another agent's outbox.
- Concise and factual — exact paths, function names, constants. Write for an agent with zero shared context.
- The human audits both channels; write nothing you wouldn't want audited.
- Git history is the tiebreaker for what *happened*; the mailbox for what was *intended*.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Single shared LOG.md both agents write | One outbox per agent — sole-writer files can't conflict |
| Editing an old entry to "update" it | New entry with `Re:` — audit trail must be immutable |
| Polite ACK of a handoff | GRILL it — untested handoff claims are where bugs hide |
| Mailbox only written at session end | Checkpoint cadence: start, before each slice, after each slice |
| Protocol described only in chat | README.md in the comms dir + shims in CLAUDE.md/AGENTS.md/GEMINI.md |
| Committing code without its mailbox entry | Commit them together — a pull must never show unexplained code |
