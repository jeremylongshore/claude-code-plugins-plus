<!-- doc-class: record -->

# Model-Agnostic Migration Surface — Committed Baseline

- **Date:** 2026-08-18
- **Authority:** Blueprint 727, Epic 3 bead 3.1
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-t9s9.1`
- **Generator:** `node scripts/measure-canonical-surface.mjs --write` (deterministic; commit
  recorded inside the JSON) — data file:
  [778-RA-DATA-model-agnostic-migration-surface.json](778-RA-DATA-model-agnostic-migration-surface.json)
- **Status:** Point-in-time baseline. Every later Epic 3 bead consumes THIS surface; the
  pre-regeneration numbers in blueprint § 3/§ 13 are superseded for planning purposes.

## Why this measurement exists

Epic 3's earlier surface estimates predated Epic 1's regeneration discipline: roughly half of
the `docs.anthropic.com` occurrences sat inside generated artifacts, and bead handles shaped
like `claude-4laa` could be mistaken for model identifiers by migration tooling. This baseline
measures the tracked tree at a recorded commit, classified twice:

- **Surface class** (by path): `first-party` (the actual migration surface) vs `mirror`
  (below a `.source.json` root — upstream-owned, PROHIBITED to Epic 3) vs `generated`
  (build projections — regenerated, never edited; they inherit whatever the canonical layer
  emits).
- **Model-identifier role** (per occurrence): `functional` (a `model:`/`"model"`/`--model`
  assignment that configures behavior — the thing E3.8 replaces with `model_class` tiers) vs
  `prose` (mentions in text — deliberately preserved) vs `bead-id` (beads issue handles —
  protected; the classifier keeps a digit-led handle like `claude-4laa` in this class even on a
  functional-looking line, with a regression test).

## The true surface (first-party, the only migratable class)

| Measure                                | Count | Files |
| -------------------------------------- | ----: | ----: |
| Functional model-id occurrences        |   398 |   184 |
| Prose model-id occurrences (preserved) |   485 |     — |
| Protected bead-id occurrences          | 7,656 |     — |
| `docs.anthropic.com` occurrences       |   257 |   115 |
| `CLAUDE_*` variable occurrences        | 1,627 |   381 |

Mirror-class counts (5 functional model ids, 4 doc links, 104 env vars) are recorded in the
JSON and are **out of scope by prohibition**, not by omission. Generated-class counts (531
functional model ids across 128 files, 179 doc links, 1,605 env vars) are projections of the
canonical layer: they converge to zero as the first-party surface migrates and regenerates, and
must never be edited directly.

The protected bead-id figure is dominated by the tracked beads export
(`.beads/issues.jsonl`) and the AAR corpus quoting bead handles — large by design, and every one
of them is a token migration tooling must refuse to touch (E3.7's exclusion contract).

## How later beads consume this

- **E3.2/E3.4** size the canonical contract against 184 functional files, not the stale ~131.
- **E3.7** ships the reusable classifier + exclusion list; this script's `classifyModelToken`
  (with its bead-id-on-functional-line regression test) is the draft semantics.
- **E3.8** replaces the 398 functional occurrences with `model_class` tiers, fail-closed.
- **E3.9** owns the 1,627 first-party `CLAUDE_*` occurrences (`${SKILL_DIR}` portability).
- **E3.10**'s vendor-literal gate takes the post-migration zero as its baseline; this document
  is the before.

## Reproduce

```bash
node scripts/measure-canonical-surface.mjs          # print JSON to stdout
node --test scripts/measure-canonical-surface.test.mjs
```

The JSON records the exact commit it measured; re-running at a later commit produces a NEW
measurement, never an edit to this one.

---

**E3.7 classifier-promotion correction (2026-08-18).** The classifier semantics were promoted to
the shared library (`scripts/lib/model-id-classifier.mjs`) with two refinements, and the JSON
baseline was regenerated through it: (1) a trailing-hyphen lookahead stops a hyphen-continued
model id (`claude-fable-5`) or product slug (`claude-code-plugins`) from leaking its prefix into
the protected scan as a phantom token — the protected count drops accordingly (7,656 → 2,923
first-party) with functional (398 → 404) and prose (485 → 493) essentially stable; (2) the
committed exclusion list (`schemas/canonical/v0/model-id-exclusions.json`, 393 live handles)
now pins every bead handle by exact string on top of the shape rule. The protected class
deliberately includes non-model `claude-*` tokens such as the bare harness name `claude-code`:
protection wins every tie, and model-id migration must not touch harness names either.
