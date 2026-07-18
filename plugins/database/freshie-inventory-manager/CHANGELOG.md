# Changelog — freshie-inventory-manager

## 1.5.0 — 2026-07-18

DoltHub VCS-plugin patterns applied to the sync pipeline (additive; the
SQLite runtime, parity gates, pump, and push are untouched).

- **Run-delta report** — new `freshie/scripts/run-delta.py`: after each
  sync commits run N, a structured `freshie/reports/run-delta-<N>.json` is
  emitted comparing `run-(N-1)` → `run-N` via `DOLT_DIFF_SUMMARY` /
  `DOLT_DIFF_STAT` (per-table schema-vs-data change classification + row
  counts) plus a **grade-regression list** (skills whose grade dropped
  tag-over-tag — adjacent run tags, so intra-run repopulations like
  run-9 → run-9.1 are compared too — computed from a temporal
  `AS OF '<tag>'` compare of `skill_compliance`).
- **Commit-hash stamping** — `grade-histogram.json` and every run-delta
  report now carry `dolt_commit`, the immutable Dolt revision the artifact
  was cut from (traceability beyond the `run-N` tag / git SHA).
- **Commit-triggered structured output** — `dolt-sync.py` runs the delta
  emission as a NON-FATAL post-commit step (loud-skip like gc) and prints a
  one-line GH-Actions-consumable summary. Default inert; new
  `--alert-on-regression` flag (on both scripts) exits 4 when grades
  regressed — the sync itself still succeeds.
- Tests: `tests/test_run_delta.py` (29 pure-function tests) + 2 new
  stamp tests in `tests/test_dolt_sync.py` (71 total across both).

## 1.0.0 — initial release

Unified command center for the freshie ecosystem inventory database —
discovery scans, compliance grading, batch remediation, querying, and
reporting across the 51-table plugin/skill/pack metadata model.
