# Session Memory (Legacy Reference)

This file is retained for backwards compatibility. The active memory system is documented in [memory-system.md](memory-system.md).

## What Changed (v1.9+)

Memory moved from a single global file (`~/.claude/hyperflow-memory.md`) to a project-scoped directory (`.hyperflow/memory/`) with:

- Multiple files by category (learnings, decisions, pitfalls, patterns, conventions)
- Tag taxonomy for fast lookup
- Hot/warm/cold tiering with automatic compression
- Lazy injection into worker prompts (only tag-matched entries, not full dump)
- Project-scoped by design — no cross-project leakage

## Migration

On first run with the new system, hyperflow scans the legacy `~/.claude/hyperflow-memory.md` for entries matching the current project path. Matched entries are migrated into `.hyperflow/memory/`. The legacy file is left untouched (other projects may still use it).

To migrate manually: copy relevant sections from `~/.claude/hyperflow-memory.md` into `.hyperflow/memory/learnings.md` using the format documented in [memory-system.md](memory-system.md).

## Disabling

Say `hyperflow: memory off` to disable for the current session.

To clear all memories for the current project: `hyperflow: memory clear` or delete `.hyperflow/memory/`.
