---
name: bridge
description: |
  Use when the user wants hyperflow's behavioral rules to apply outside the terminal CLI — in Claude Code Desktop, claude.ai web, or IDE extensions that don't load CLI plugins. Writes a managed doctrine block into the project's CLAUDE.md so autonomy + intent-routing + commit cadence + tier split + file-first rules carry over. Lossy (no slash commands, no actual skill dispatch) but useful.
  Trigger with /hyperflow:bridge, "make hyperflow work in desktop", "make hyperflow work in claude.ai", "embed hyperflow doctrine in CLAUDE.md", "portable hyperflow rules".
allowed-tools: Read, Write, Edit, Bash(cat:*), Bash(ls:*), Bash(date:*)
argument-hint: "<generate|refresh|remove|status>"
version: 4.10.1
license: MIT
compatibility: Designed for Claude Code · Output works in any surface that loads CLAUDE.md
tags: [portability, desktop, web, claude-md, bridge]
---

# Bridge

Embed the portable subset of hyperflow's doctrine into the project's `CLAUDE.md` so it applies in surfaces that don't load CLI plugins (Claude Code Desktop, claude.ai web, IDE extensions). The doctrine block is managed via fenced markers, so refreshing it on plugin updates is idempotent and never touches your own `CLAUDE.md` content.

Source template: [`templates/claude-md-doctrine.md`](../../templates/claude-md-doctrine.md). Doctrine background: [DOCTRINE.md](../hyperflow/DOCTRINE.md).

## Subcommands

| Subcommand | Description |
|---|---|
| `generate` | Write the doctrine block into the project's `CLAUDE.md` (create the file if absent, append the block if not present, refresh if already present) |
| `refresh` | Same as `generate` — alias for clarity when the block already exists |
| `remove` | Remove the doctrine block from `CLAUDE.md` (preserves your own content; if the file becomes empty after removal, leave it as an empty file rather than delete) |
| `status` | Show whether the doctrine block is present, its version, when it was generated |
| `mode <auto\|manual\|off>` | Set the auto-bridge mode for this project. Writes `.hyperflow/.bridge-mode`. The session-start hook reads this and decides what to do |

Default subcommand when none provided: `status`.

## Auto-bridge (default ON)

The CLI session-start hook (`hooks/session-start`) runs `scripts/auto-bridge.py` on every session start. Behavior depends on the mode stored in `.hyperflow/.bridge-mode`:

| Mode | Behavior |
|---|---|
| `auto` (**default** when `.bridge-mode` is absent) | If `./CLAUDE.md` is missing the doctrine block OR has an outdated version, **silently writes/refreshes** the block and prints a one-line notice in session-start output. Zero user friction. |
| `manual` | Never writes. Prints a one-line advisory when the block is missing or outdated: `./CLAUDE.md doctrine block would be refreshed (version 4.11.0) — run /hyperflow:bridge refresh to apply`. |
| `off` | Does nothing. No writes, no advisories. |

This means: open Claude Code CLI once in your project, and from then on every Desktop / web / IDE session in the same project automatically gets the up-to-date hyperflow doctrine via `CLAUDE.md`. Refresh on plugin update is automatic too.

To opt out: `/hyperflow:bridge mode off`. To require explicit refresh: `/hyperflow:bridge mode manual`.

## What gets written

A fenced block in the project's `./CLAUDE.md` (at the repo root, where Claude Code Desktop / web / CLI all look for it):

```markdown
<!-- hyperflow:doctrine:start version=<X.Y.Z> generated=<ISO-8601> source=https://github.com/Mohammed-Abdelhady/hyperflow -->

# Hyperflow Doctrine (Portable Subset)

<the full template body — autonomy, intent-routing, commit cadence,
 tier split, file-first artefacts, no AI attribution, security
 blocklists, what's missing vs CLI>

<!-- hyperflow:doctrine:end -->
```

The fenced markers (`hyperflow:doctrine:start` / `hyperflow:doctrine:end`) let `refresh` find and replace ONLY the doctrine block, leaving everything else in your `CLAUDE.md` untouched. Place the block anywhere in `CLAUDE.md`; the bridge respects its position.

## When to use

| Situation | Use bridge? |
|---|---|
| You work exclusively in Claude Code CLI (terminal) | No — the plugin loads doctrine directly; bridge would duplicate |
| You use Claude Code Desktop on Mac / Windows | **Yes** — bridge gives Desktop the autonomy + intent-routing + commit cadence rules |
| You use claude.ai web app for this project | **Yes** — same reason |
| You use VS Code / Cursor / JetBrains and the extension shells out to the `claude` CLI | No — the CLI plugin applies |
| You use VS Code / Cursor and the extension talks to the API directly | **Yes** — the API session loads `CLAUDE.md` |
| You collaborate with teammates who use mixed surfaces | **Yes** — commit the generated `CLAUDE.md` so everyone has the same rules regardless of their surface |

## What you keep / lose vs the full CLI plugin

| Capability | CLI plugin | CLAUDE.md bridge |
|---|---|---|
| Autonomy rules (no confirmations, minimal output, no hedging) | yes | **yes** |
| Intent-based routing (audit/debug/fix/brainstorm verbs) | yes | **yes (described in CLAUDE.md as rules for the orchestrator to follow)** |
| Per-task commit cadence | yes | **yes** |
| Tier split (per-batch Sonnet, final Opus) | yes | **yes** |
| File-first artefacts under `.hyperflow/` | yes | **yes** |
| Binary-gate rule (no recommendation on yes/no) | yes | **yes** |
| No-AI-attribution rule | yes | **yes** |
| Security blocklists | yes | **yes** |
| `/hyperflow:*` slash commands | yes | no — surfaces without the plugin can't dispatch named skills |
| Chain-mode Step-0 auto/manual question | yes | no — defaults to auto-style chain in CLAUDE.md mode |
| Operational pre-elections (commit/branch/push at scope Step 2.6) | yes | no — defaults applied per CLAUDE.md guidance |
| Per-step Worker → Reviewer dispatch templates from `worker-prompt.md` / `reviewer-prompt.md` | yes | partial — tier-split rule preserves the spirit; exact prompts not embedded (would bloat CLAUDE.md) |
| Background agents, sticky mode, status skill, cache skill | yes | no — these need their own slash command surfaces |
| Adaptive flow profiles (`fast` / `standard` / `deep`) | yes | no — orchestrator infers from message complexity |

Net coverage: ~70% of hyperflow's behavioral value. Slash commands and the infrastructure that wraps them are the missing 30%.

## Subcommand Details

### `generate` / `refresh`

1. Read the template at `~/.claude/plugins/cache/hyperflow-marketplace/hyperflow/<version>/templates/claude-md-doctrine.md` (resolve current version from the active plugin install).
2. Substitute placeholders: `__HYPERFLOW_VERSION__` → current plugin version, `__GENERATED_AT__` → current UTC timestamp (ISO-8601).
3. Read the project's `./CLAUDE.md`. Three cases:
   - **File absent** — create `./CLAUDE.md` with just the doctrine block.
   - **File exists, no existing doctrine block** — append the doctrine block at the end of the file (preceded by one blank line if the file doesn't already end with a blank line).
   - **File exists, doctrine block present** — find the `<!-- hyperflow:doctrine:start … -->` and `<!-- hyperflow:doctrine:end -->` markers, replace everything between them (inclusive of the markers) with the new block. All other content in `CLAUDE.md` is preserved exactly.
4. Write the updated `CLAUDE.md`.
5. Print:

```
Wrote hyperflow doctrine block to ./CLAUDE.md (version 4.10.1).
Surfaces that load CLAUDE.md (Desktop, claude.ai web, IDE extensions that talk to API) will now honor:
  · Autonomy rules
  · Intent-based routing (audit/debug/fix/brainstorm/scope/deploy verbs)
  · Per-task commit cadence
  · Tier split (per-batch Sonnet, final Opus)
  · File-first artefacts under .hyperflow/
  · No AI attribution
  · Security blocklists

Re-run `/hyperflow:bridge refresh` after updating the plugin to pick up doctrine changes.
What's NOT in the bridge: /hyperflow:* slash commands, plugin-loaded skill files, operational pre-elections. Those need the terminal CLI.
```

### `remove`

1. Read `./CLAUDE.md`. If absent or doctrine markers not present, print `Nothing to remove — no hyperflow doctrine block in ./CLAUDE.md.` and stop.
2. Find the `<!-- hyperflow:doctrine:start … -->` and `<!-- hyperflow:doctrine:end -->` markers; remove everything between them (inclusive of markers). Collapse adjacent blank lines so the file doesn't end up with a triple newline.
3. If `CLAUDE.md` is now empty (or only whitespace), leave it as an empty file rather than delete — the user may have other tooling that expects the file to exist.
4. Print `Removed hyperflow doctrine block from ./CLAUDE.md. Surfaces that loaded the doctrine block will revert to default behaviour.`

### `mode <auto|manual|off>`

Write the chosen mode to `.hyperflow/.bridge-mode`. The file holds one word: `auto`, `manual`, or `off`. The session-start hook reads it on every CLI session start. Print one of:

```
Auto-bridge: AUTO — ./CLAUDE.md doctrine block is silently maintained on every CLI session start.
Auto-bridge: MANUAL — session start prints an advisory when the block is stale; you run /hyperflow:bridge refresh.
Auto-bridge: OFF — no advisories, no writes. Use /hyperflow:bridge generate manually if you want the block.
```

Defaults to `auto` when `.bridge-mode` is absent (so first install of hyperflow auto-bridges with no user action). Setting `auto` explicitly is a no-op write that just records the intent.

### `status`

Read `./CLAUDE.md`. Find the doctrine markers. Print one of:

```
Hyperflow doctrine block: PRESENT in ./CLAUDE.md
  Version generated: 4.10.1
  Generated at:      2026-05-17T15:30:00Z
  Plugin current:    4.10.1
  Status:            up to date · or · update available (re-run /hyperflow:bridge refresh)
```

```
Hyperflow doctrine block: NOT PRESENT in ./CLAUDE.md
  Use /hyperflow:bridge generate to add it.
```

```
Hyperflow doctrine block: NOT PRESENT (no ./CLAUDE.md in project root)
  Use /hyperflow:bridge generate to create ./CLAUDE.md with the doctrine block.
```

## Flow

1. Parse subcommand (default `status`).
2. Locate the project's `./CLAUDE.md` (repo root).
3. Execute subcommand per the details above.
4. Print one-block confirmation.

## Overview

`/hyperflow:bridge` is the user-facing interface for the CLAUDE.md doctrine bridge. It does NOT itself enforce the doctrine — it writes the rules into a file that surfaces outside the terminal CLI will load. Enforcement happens in those surfaces when the host loads `CLAUDE.md` at session start.

## Prerequisites

- Project root contains a writable `./` directory (the bridge writes `./CLAUDE.md`).
- Hyperflow plugin installed (the bridge reads its template from the plugin cache). If running outside the plugin context, the bridge falls back to a vendored copy in the plugin source tree.

## Instructions

See [Subcommands](#subcommands) and [Subcommand Details](#subcommand-details). Summary:

1. Parse subcommand (default `status`).
2. Read/write `./CLAUDE.md` per the chosen subcommand.
3. Print one short confirmation block.

## Output

- `generate` / `refresh` — multi-line confirmation listing what surfaces now honor; what's NOT in the bridge.
- `remove` — one-line confirmation.
- `status` — three-field block (present / version / freshness).

## Error Handling

| Failure | Behavior |
|---|---|
| `./CLAUDE.md` not writable | Print explicit error; suggest `chmod +w ./CLAUDE.md` if permissions-related. Do NOT silently fall back to a hidden location. |
| Plugin template not found (running outside cached plugin) | Look up the template at `<plugin-root>/templates/claude-md-doctrine.md` relative to this SKILL.md's directory. If still not found, refuse with a clear error. |
| Existing doctrine block has malformed markers (one without the other) | Refuse to refresh; print the malformed file's line range and ask the user to fix the markers manually. Do NOT auto-repair — the user's content might be at risk. |
| Multiple doctrine blocks in one CLAUDE.md (duplicate) | Refuse and surface the line ranges of both. User decides which to keep. |
| User runs `generate` repeatedly | Idempotent — every run replaces the block with the latest template + timestamp. No duplication. |

## Examples

### First-time setup for a Desktop user

```
You: /hyperflow:bridge generate

Wrote hyperflow doctrine block to ./CLAUDE.md (version 4.10.1).
Surfaces that load CLAUDE.md (Desktop, claude.ai web, IDE extensions that talk to API) will now honor:
  · Autonomy rules
  · Intent-based routing (audit/debug/fix/brainstorm/scope/deploy verbs)
  · Per-task commit cadence
  · Tier split (per-batch Sonnet, final Opus)
  · File-first artefacts under .hyperflow/
  · No AI attribution
  · Security blocklists

Re-run `/hyperflow:bridge refresh` after updating the plugin to pick up doctrine changes.
What's NOT in the bridge: /hyperflow:* slash commands, plugin-loaded skill files, operational pre-elections. Those need the terminal CLI.
```

### Status check

```
You: /hyperflow:bridge status

Hyperflow doctrine block: PRESENT in ./CLAUDE.md
  Version generated: 4.10.0
  Generated at:      2026-05-15T09:12:00Z
  Plugin current:    4.10.1
  Status:            update available (re-run /hyperflow:bridge refresh)
```

### Refresh after plugin update

```
You: /hyperflow:bridge refresh

Wrote hyperflow doctrine block to ./CLAUDE.md (version 4.10.1).
...
```

### Remove

```
You: /hyperflow:bridge remove

Removed hyperflow doctrine block from ./CLAUDE.md. Surfaces that loaded the doctrine block will revert to default behaviour.
```

## Resources

- [`templates/claude-md-doctrine.md`](../../templates/claude-md-doctrine.md) — the portable doctrine template the bridge writes.
- [DOCTRINE.md](../hyperflow/DOCTRINE.md) — the full doctrine (CLI surface).
- [output-style.md](../hyperflow/output-style.md) — confirmation-block format.
