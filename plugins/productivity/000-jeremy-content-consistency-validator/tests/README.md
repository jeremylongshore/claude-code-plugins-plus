# Fixture gate — content-consistency validator

The red/green gate mandated by the #991 design council: **nothing else in
this plugin proceeds until this gate exists and passes.** Evals assert
findings, not procedure — the gate passes only when the deterministic
checker reports *exactly* the seeded drifts (zero invented, zero missed) on
the drifted fixture, and *zero* findings on the clean fixture.

## Run it

Local (from the repo root — no installs, no API keys, no network):

```bash
bash plugins/productivity/000-jeremy-content-consistency-validator/tests/run-fixture-check.sh
```

CI wiring (add as a discrete named step in
`.github/workflows/validate-plugins.yml`):

```yaml
- name: Consistency-validator fixture gate (red/green)
  run: bash plugins/productivity/000-jeremy-content-consistency-validator/tests/run-fixture-check.sh
```

Debugging a single tree (prints raw findings JSON):

```bash
python3 plugins/productivity/000-jeremy-content-consistency-validator/tests/fixture_checker.py \
  scan plugins/productivity/000-jeremy-content-consistency-validator/fixtures/drifted \
  --sot-map plugins/productivity/000-jeremy-content-consistency-validator/fixtures/sot-map.example.yaml
```

The plugin's `package.json` is generator-owned (sync-marketplace) and its
npm `files` set does not ship `tests/`, so no `npm test` entry is wired —
the `bash` line above is the canonical entry point.

## What is under test

`../fixtures/` holds a miniature fake project (**acme-widgets**) in two
copies:

- `clean/` — internally consistent on every surface.
- `drifted/` — the same project with **12 seeded drifts**, at least one per
  deterministic check in the skill's 9-check list, recorded in
  `../fixtures/expected-findings.json` (ids `DRIFT-01`…`DRIFT-12`).

| Id       | Check (skill §)              | Seeded drift                                          |
| -------- | ---------------------------- | ----------------------------------------------------- |
| DRIFT-01 | version-consistency (3.2)    | README badge 2.2.0 vs manifest 2.3.0                   |
| DRIFT-02 | staleness-bound (registry)   | docs date 241 days old vs 180-day bound                |
| DRIFT-03 | readme-vs-ci (3.3)           | README `npm test` vs CI `npm run test:unit`            |
| DRIFT-04 | broken-refs (3.8)            | README prose ref to deleted `docs/usage.md`            |
| DRIFT-05 | index-vs-filesystem (3.1)    | INDEX lists a file that is not on disk                 |
| DRIFT-06 | index-vs-filesystem (3.1)    | File on disk missing from the INDEX                    |
| DRIFT-07 | claude-md-paths (3.4)        | CLAUDE.md table refs deleted `docs/architecture.md`    |
| DRIFT-08 | stale-phase-language (3.5)   | "scaffold only — no application code" vs `src/cli.js`  |
| DRIFT-09 | cross-doc-facts (3.7)        | README Apache-2.0 vs manifest MIT                      |
| DRIFT-10 | command-claims-vs-code (3.6) | README claims `export` command code never registers    |
| DRIFT-11 | planning-vs-code (3.9)       | Roadmap marks shipped `list` command as Planned        |
| DRIFT-12 | unowned-fact-class           | Tagline conflict; `product.tagline` has no registry row |

Authority comes from `../fixtures/sot-map.example.yaml` — the per-fact-class
registry demonstrating the council schema (fact_class → owner → mirrors →
determinism-class → staleness bound). It deliberately does **not** register
`product.tagline`, so DRIFT-12 exercises the "unowned fact-class — human
adjudication needed" path: with no registry row the checker emits that
finding and never guesses a winner. The registry also carries one
`llm-judged` class (`brand.voice`) purely to demonstrate the determinism
axis — judged classes are advisory-only, never blocking, and this gate
skips them entirely.

The registry pins `as_of: 2026-07-01` so the date-staleness math is
deterministic forever; a real deployment omits `as_of` and uses today.

## Checker scope (Phase 1)

`fixture_checker.py` is bash/python3-stdlib only and implements the
**mechanical subset** of the skill's 9 drift checks: string, semver,
link/path-existence, and date compares. NO LLM. Extraction is
regex/convention-based (version badges, `## Commands` tables,
`registerCommand(...)` calls, `Last updated:` stamps, backtick prose paths
resolved root-relative, markdown links resolved file-relative).

Read-only contract: the checker never modifies the trees it scans — no
auto-fix, per council constraint.

## What Phase 2 replaces

The regex extractors above are the Phase 1 stopgap. Phase 2 introduces
**typed claim records**: each surface's facts get extracted into typed
records (fact_class, value, surface, span) once, and drift detection
becomes pure record comparison against the sot-map registry — the fixture
corpus and `expected-findings.json` stay as-is and become the regression
gate for that swap. The gate contract (exact-match findings, clean stays
zero) must not change.
