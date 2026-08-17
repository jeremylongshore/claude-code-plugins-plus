# 722-RA-AUDT — Duplicate & Orphan Report (Mission 01)

**Captured:** 2026-08-11 @ `4358a65a3`. Dispositions live in the register (doc 719); this
report is evidence only.

## Byte-identical duplicates (`cmp`-proven)

Exactly **2** files have `marketplace/src/data` ↔ `marketplace/public/data` twins:

| File                        | Bytes          |
| --------------------------- | -------------- |
| `skills-catalog.json`       | 25,600,536     |
| `unified-search-index.json` | 2,860,309      |
| **Total duplicated**        | **28,460,845** |

No other data file has a twin — the dedup candidate (register row 4) is precisely scoped.

## Triplicated binary

`kobiton` — Mach-O 64-bit x86_64 executable, 11,790,440 B, committed **3×**:
plugin `skills/`, plugin `.codex/` shadow, and the generated `skills/.curated/` mirror
(35.4 M total). The curated copy regenerates — a source-level fix removes 2 of 3
automatically (register row 3).

## Manifest excess

621 `plugin.json` manifests vs 474 plugin dirs — the excess is `.codex/` shadow copies of
plugin manifests, a structural duplication pattern worth a policy decision (keep vs generate).

## Catalog ↔ directory reconciliation

- Catalog sources: 465 paths · plugin dirs on disk: 475.
- **0 catalog entries point at missing dirs.**
- 10 dirs are uncatalogued: 6 infrastructure (`saas-packs/{000-docs,_templates,scripts,skill-databases,vendors}`, `mcp/.greptile`) — expected, KEEP; **4 orphan candidates**:
  `business-tools/general-legal-assistant`, `mcp/a2a-client`, `productivity/claude-memory-kit`,
  `saas-packs/claude-pack` (register row 5 — investigate WIP-vs-orphan before any action).

## Loose / misplaced files

- `plugins/JEREMY_PLUGINS_SUMMARY.md`, `plugins/README_JEREMY_PLUGINS.md`,
  `plugins/install-jeremy-plugins.sh` — non-conforming location (register row 6).
- `plugins/ai-agency/tonone/.claude-plugin/CLAUDE.md` (319 B) — session-tool auto-generated
  noise inside a `curated: true` **frozen** mirror; removal requires the curated-exception
  process (register row 7).

## Documentation number collisions

Numbers 256, 264, 265 each have a tracked holder and a local-only claimant (doc 720 §8).
