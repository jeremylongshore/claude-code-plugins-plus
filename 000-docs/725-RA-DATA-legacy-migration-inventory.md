<!-- doc-class: record -->

# 725-RA-DATA — Legacy Model-Agnostic Migration Inventory (Mission 01)

**Captured:** 2026-08-11 @ `4358a65a3` · **Machine-readable:** `725-RA-DATA-legacy-migration-inventory.json`
Relates GH **#1146** (which under-scopes the surface at "~486"). Inventory only — migration is a
future, approval-gated epic. Model-id changes are **functional** (they break at runtime), never
mechanical find-replace.

## Reproduced metrics (tracked tree)

| Surface | Metric | Command basis |
| --- | --- | --- |
| `docs.anthropic.com` | **169 files** | `git grep -l 'docs\.anthropic\.com' \| wc -l` |
| | **412 lines** | `git grep -c` summed |
| | **500 occurrences** | `git grep -o \| wc -l` |
| | 150 of 500 inside the two `skills-catalog.json` byte-dupes | scoped `git grep -o` |
| `claude-3` | **248 files** — functional model ids | `git grep -lE 'claude-3' \| wc -l` |
| `claude-2` | **19 files** (no word-boundary) / **11 files** (`claude-2\b`) | both regexes recorded — earlier reports citing 19 used the unbounded form |

## Migration-shaping observations

1. **30 % of `docs.anthropic.com` occurrences are inside generated artifacts** (the
   `skills-catalog.json` twins). Migrating generator *sources* and rebuilding eliminates those
   150 for free — the true hand-migration surface is meaningfully smaller than raw counts.
2. `claude-3`/`claude-2` references include live model ids in plugin bodies — each needs a
   per-plugin decision (current-model upgrade vs doc-only mention), not a sweep.
3. Counting method matters: this doc pins exact commands so future runs diff cleanly; the
   "~486" figure in #1146 reproduces under none of the recorded commands.
