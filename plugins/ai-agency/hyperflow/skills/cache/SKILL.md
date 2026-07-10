---
name: cache
description: |
  Use when the user wants to view, search, add, edit, prune, archive, or clear hyperflow memory entries. CRUD interface for `.hyperflow/memory/` — never modifies source code, only memory files.
  Trigger with /hyperflow:cache, "show memory", "search memory for X", "clear memory", "what does hyperflow remember about Y".
allowed-tools: Read, Write, Edit, Bash(ls:*), Bash(mv:*), Bash(rm:*), Glob, Grep, Agent, AskUserQuestion
argument-hint: "<show|search|add|edit|prune|archive|clear|stats|migrate|off|compact> [args]"
version: 3.1.3
license: MIT
compatibility: Designed for Claude Code
tags: [memory, persistence, project-state]
---

# Cache

CRUD interface for `.hyperflow/memory/`. Full protocol: [memory-system.md](references/memory-system.md).

## Storage

All operations target `.hyperflow/memory/` at the project root. Never modify source code files — if asked to "remember X about file Y", add a memory entry only, never edit Y.

## Subcommands

| Subcommand | Description |
|---|---|
| `show [tag]` | Print index or filter entries by tag |
| `search <query>` | Full-text search across all memory files |
| `add <category> <title>` | Append a new entry (prompts for details) |
| `edit <entry-id>` | Find entry by date+title slug and update in place |
| `prune` | Remove stale, superseded, and orphaned entries |
| `archive` | Move entries older than 30 days to cold storage |
| `clear` | Wipe all memory (with confirmation, recoverable) |
| `stats` | Counts, tier breakdown, tag frequency, oldest/newest |
| `migrate` | Import entries from legacy `~/.claude/hyperflow-memory.md` |
| `off` | Disable memory writes for this session |
| `compact` | Summarise aged memory entries into stubs + monthly archive sidecars |

## Subcommand Details

### `show [tag]`
No arg → print `index.md`. With tag → filter all files for matching entries.
Output table: `Date | Title | Tags | File | Tier`

### `search <query>`
grep/ripgrep across `learnings.md`, `decisions.md`, `pitfalls.md`, `patterns.md`, `conventions.md`.
Return `file:line` + snippet, ranked by relevance.

### `add <category> <title>`
Categories: `learning` `decision` `pitfall` `pattern` `convention`
Prompt via AskUserQuestion for: `what`, `why it matters`, `tags` (controlled vocab).
Append to the matching file using:
```
### [YYYY-MM-DD] <title>  `[tag1, tag2]`
**What:** ...
**Why it matters:** ...
**Evidence:** ...
```
Update `index.md` with the new row.

### `edit <entry-id>`
Locate by date+title slug. Show current value, prompt for new value, update in place.

### `prune`
Per [memory-system.md](references/memory-system.md) pruning protocol:
- Remove `[SUPERSEDED]` entries older than 7 days
- Remove entries whose referenced files no longer exist (`test -f`)
- Archive entries unreferenced 90+ days to `.hyperflow/memory/archive/YYYY-MM.md`
Print summary of removed/archived counts.

### `archive`
Compress hot entries older than 30 days → `.hyperflow/memory/archive/YYYY-MM.md`.
Leave one-line summary in original file. Update `index.md` tier column.

### `clear`
Confirm via AskUserQuestion: "This wipes all memory for this project. Are you sure?"
If yes → move all content to `.hyperflow/memory/archive/cleared-<timestamp>.md`, then reset files to empty stubs.

### `stats`
Print: total entries, hot/warm/cold counts, tag frequency table, oldest and newest entry dates.

### `migrate`
Read `~/.claude/hyperflow-memory.md`, filter entries matching current project path.
Append matching entries to `learnings.md`. Leave legacy file untouched.
Print count of migrated entries.

### `off`
Print: "Memory writes disabled for this session." No files modified.

### `compact`
User-invoked memory compaction. Summarises entries older than 7 days into stub lines and preserves the full text in monthly archive sidecars at `.hyperflow/memory/archive/YYYY-MM.md`.

Flow:
1. The compact subcommand handler reads the target memory file (default: `learnings.md`; pass a path to target another).
2. The Date/tag parser splits entries into hot (≤7 days, preserved) and eligible (>7 days). Both `[domain, type]` and legacy backticked `` `[domain, type]` `` tag forms are accepted.
3. The Compaction Writer is dispatched in a single batch with all eligible entries.
4. The Stub formatter renders each replacement line as `### [YYYY-MM-DD] Short title  [domain, type] — summarized, see archive/YYYY-MM.md`.
5. The Dedup Reviewer performs source-side stub-line match and archive-side header match (date + title + tags on both sides) to prevent duplicates.
6. The Archive-sidecar writer appends accepted entries to `archive/YYYY-MM.md`, grouped by each entry's calendar month.
7. The source file is rewritten with stubs replacing the original entries.
8. The compact subcommand handler refreshes `.hyperflow/memory/.checksums` (a memory-scoped sidecar — distinct from `.hyperflow/.checksums` which the scaffold staleness check owns) and exits with a summary.

Output: `N entries compacted into archive/YYYY-MM.md · M stubs rejected as duplicates · source N→M lines`. Full protocol in [compaction.md](references/compaction.md).

## Flow

1. Parse invocation to determine subcommand
2. If subcommand missing → list subcommands table above with one-line descriptions
3. Execute subcommand
4. Print structured result with counts/changes summary

## Overview

`/hyperflow:cache` is the operator interface to project-scoped memory under `.hyperflow/memory/`. It's the only skill that mutates memory files directly (other skills append via the memory-system protocol). Subcommands cover the full lifecycle: show, search, add, edit, prune, archive, clear, stats, migrate. All operations are project-local — entries never leak across projects.

## Prerequisites

- `.hyperflow/` initialized (run `/hyperflow:scaffold` if missing — cache creates `.hyperflow/memory/` on first write but expects the parent dir).
- Write access to `.hyperflow/memory/` and `.hyperflow/memory/archive/`.
- For `migrate` only: read access to `~/.claude/hyperflow-memory.md` (legacy global memory).

## Instructions

See [Subcommands](#subcommands) and [Subcommand Details](#subcommand-details) above for the full operational spec. Summary:

1. Parse the subcommand from the user's invocation (or list subcommands if none given).
2. Validate prerequisites for the chosen subcommand (e.g. `clear` requires `AskUserQuestion` confirmation; `migrate` requires legacy file presence).
3. Execute the subcommand against `.hyperflow/memory/`.
4. Print structured result with counts and any file-level changes.

## Output

Each subcommand prints a compact summary:

- `show` — table of matching entries (Date | Title | Tags | File | Tier).
- `search` — `file:line` matches with snippets, ranked by relevance.
- `add` / `edit` — confirmation line with new entry id and target file.
- `prune` / `archive` / `clear` — counts of removed/archived/cleared entries plus destination paths.
- `stats` — totals + hot/warm/cold breakdown + top-N tags.
- `migrate` — count of migrated entries + source legacy file path.
- `off` — single-line `Memory writes disabled for this session.`

## Error Handling

| Failure | Behavior |
|---|---|
| `.hyperflow/memory/` missing | Auto-create skeleton (index.md + 5 category files + archive/.gitkeep) on first write; for read-only subcommands, print `(no memory yet — invoke /hyperflow:scaffold first)`. |
| Subcommand unknown | Print subcommands table; suggest closest match via Levenshtein distance. |
| `add` with invalid category | Reject and list valid categories: learning, decision, pitfall, pattern, convention. |
| `edit` entry id not found | List 3 closest matches by title slug + date. |
| `clear` without confirmation (headless) | Refuse and print `clear requires interactive confirmation`. Do not wipe. |
| `migrate` source file missing | Print `(nothing to migrate — ~/.claude/hyperflow-memory.md not found)` and stop. |

## Examples

### Show all entries

```
/hyperflow:cache show

Date         Title                              Tags                  File              Tier
2026-05-16   Bash scoping required by validator [validator, marketplace] learnings.md   hot
2026-05-15   No AI attribution in commits       [convention, git]     conventions.md    hot
2026-05-14   Per-task commits in plugin dev     [convention, git]     conventions.md    hot
3 entries (3 hot, 0 warm, 0 cold)
```

### Search

```
/hyperflow:cache search "validator"

.hyperflow/memory/learnings.md:42 — "Jeremy's validator requires scoped Bash..."
.hyperflow/memory/decisions.md:8 — "...validator score of 73 → 94 after fix"
2 matches
```

### Add a learning

```
/hyperflow:cache add learning "Markdown frontmatter needs block scalar for colons"

? What: Block scalar (|) preserves : and backticks in YAML values
? Why it matters: prevents fatal YAML parse failures in marketplace validators
? Tags: yaml, validator, frontmatter
Added — .hyperflow/memory/learnings.md (entry 2026-05-16-block-scalar-frontmatter)
```

### Stats

```
/hyperflow:cache stats

Memory entries: 47
  Hot   (≤7d)   12
  Warm  (8-30d) 23
  Cold  (30d+)  12
Top tags: validator (8), convention (7), git (6), yaml (4)
Oldest: 2026-02-14   Newest: 2026-05-16
```

## Resources

- [memory-system.md](references/memory-system.md) — full protocol: files, tiers, tagging, pruning rules.
- [compaction.md](references/compaction.md) — `/hyperflow:cache compact` protocol: stub format, archive sidecar, idempotency.
- [output-style.md](references/output-style.md) — label and table conventions.
- [DOCTRINE.md](../hyperflow/DOCTRINE.md) — orchestration rules.
