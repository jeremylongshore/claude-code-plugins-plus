# Compaction Protocol

> Canonical reference. Linked from `skills/cache/SKILL.md` (`### compact` subcommand) and the `## Compaction Protocol` section of every `memory-system.md` mirror.

## Purpose

Compaction reduces memory files that have grown beyond a useful line count by replacing old entries with one-line stubs and archiving their full content to monthly sidecars. It keeps hot (recent) entries intact while making older context retrievable without inflating context windows.

## Two flows

### Session-start advisory (non-LLM)

At session start, the Session-start lineCount checker reads `.hyperflow/memory/.checksums` and compares the stored `lineCount` for each memory file against `memory.compactionThreshold` from `~/.hyperflow/config.json` (default 300). Uses `python3` — not `jq`. No LLM call is made. If any file exceeds the threshold, the Warning printer emits a single advisory line naming the file and its current count. Non-blocking — the session continues regardless.

### User-invoked compact

Triggered by `/hyperflow:cache compact`. Eight-step flow:

1. Compact subcommand handler reads the target memory file.
2. Date/tag parser splits entries into hot (≤ 7 days) and eligible (> 7 days).
3. Compaction Writer is dispatched in a single batch with all eligible entries.
4. Stub formatter renders the replacement line for each entry.
5. Dedup Reviewer runs source-side stub-line match and archive-side header match.
6. Archive-sidecar writer appends accepted entries to `archive/YYYY-MM.md`.
7. Source file is rewritten with stubs replacing eligible entries.
8. Compact subcommand handler updates `.hyperflow/memory/.checksums` and exits with a summary.

## Stub format

The replacement line for a compacted entry:

```
### [YYYY-MM-DD] Short title  [domain, type] — summarized, see archive/YYYY-MM.md
```

**Dual-acceptance rule:** the Date/tag parser MUST accept BOTH tag forms:
- New (unbackticked): `[domain, type]`
- Legacy (backticked): `` `[domain, type]` ``

Legacy backticked tags exist in pre-compaction entries written before this feature. Stubs emitted by the Stub formatter use the unbackticked form; the parser must still recognise the backticked form on subsequent reads so that legacy entries remain eligible and stubs round-trip cleanly.

## Archive sidecar layout

`<memory-dir>/archive/YYYY-MM.md` — one file per calendar month, append-only. Grouped by each compacted entry's own date. The `archive/` directory is created by `/hyperflow:scaffold` (`archive/.gitkeep`) and re-created lazily by the Archive-sidecar writer if absent.

Header inside the archive matches the source entry header exactly: `### [YYYY-MM-DD] Short title  [domain, type]` followed by the original body.

## `.hyperflow/memory/.checksums` JSON shape

This is a **separate sidecar** from `.hyperflow/.checksums` (which `/hyperflow:scaffold` uses to track tracked-config staleness). The memory-checksums sidecar is scoped exclusively to memory files. Shape:

```json
{
  ".hyperflow/memory/learnings.md": { "sha256": "<hex>", "lineCount": 247 },
  ".hyperflow/memory/decisions.md": { "sha256": "<hex>", "lineCount": 89 }
}
```

Per-file object keyed by path. Fields:
- `sha256` — hex digest of the file, refreshed after every compact run
- `lineCount` — integer line count, read by the Session-start lineCount checker and updated by the compact subcommand handler as the final step of a successful run

The Session-start lineCount checker compares `lineCount` to `memory.compactionThreshold` from `~/.hyperflow/config.json` (default 300). The `/hyperflow:scaffold` staleness check does NOT touch this file; it owns `.hyperflow/.checksums` (different path).

## Date/tag parser contract

Input: a markdown memory file (`learnings.md`, `decisions.md`, etc).

For each H3 entry header line, the parser must:

1. Extract the date from `### [YYYY-MM-DD]` — reject entries whose date does not parse as ISO 8601.
2. Extract the tags from either `[domain, type]` (new) or `` `[domain, type]` `` (legacy). Both forms produce the same parsed `[domain, type]` pair.
3. Classify by age:
   - `≤ 7 days` (hot tier — never eligible for compaction)
   - `> 7 days` (eligible)
4. Detect a back-pointer suffix `— summarized, see archive/YYYY-MM.md` to recognise an already-compacted stub line and skip re-compaction.

Future-dated entries (date > today) fall into the `≤ 7 days` bucket by definition and are silently skipped — see edge case 22 in the spec.

## Dedup Reviewer reuse pattern

The Dedup Reviewer is not a function — it is a prompt-level pattern reused from the existing memory-write pipeline (compare with `skills/audit/SKILL.md`, where the same agent pattern appears for memory dedup checks).

The compact subcommand handler dispatches a thinking-tier Reviewer with instructions to perform two header-based checks:

1. **Source-side stub-line match** — for each candidate stub the Stub formatter produced, search the source file for an existing stub whose date + title + tags already match. Reject duplicates.
2. **Archive-side header match** — for each candidate archive block, search `archive/YYYY-MM.md` (for that block's calendar month) for an existing header with the same date + title + tags. Reject duplicates.

Matching is header-only — entry body is not inspected. Manually pasted entries without a conforming header will not be detected; this is a documented limitation (spec edge case 10).

## Idempotency contract

Re-running `/hyperflow:cache compact` on a file that has already been fully compacted produces no new writes. The Dedup Reviewer rejects every candidate stub on the source side and every candidate block on the archive side; the compact subcommand handler refreshes `.hyperflow/memory/.checksums` and exits with a one-line "N stubs rejected — file already compacted" summary.

## Behaviour summary table

| Trigger | Component(s) involved | LLM | Blocking | Outputs |
|---|---|---|---|---|
| Session start | Session-start lineCount checker, Warning printer | no | no | one-line advisory or silence |
| `/hyperflow:cache compact` | compact subcommand handler, Date/tag parser, Compaction Writer, Stub formatter, Dedup Reviewer, Archive-sidecar writer | yes (Compaction Writer only) | yes | rewritten source file, appended archive sidecar, refreshed checksums |

## See also

- `.hyperflow/specs/memory-compaction.md` — full design spec including all 13 key decisions and 22 edge cases
- `memory-system.md` (mirrored across cache, hyperflow, trace, dispatch, spec, audit skills) — the `## Compaction Protocol` section in each links back here
- `skills/cache/SKILL.md` — `### compact` subcommand block
- `hooks/session-start` — Session-start lineCount checker implementation
- `config/schema.json` — `memory.compactionThreshold` property
