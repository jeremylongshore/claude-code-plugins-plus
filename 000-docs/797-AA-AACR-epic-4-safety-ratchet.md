<!-- doc-class: record -->

# Epic 4 Triple-Keyed Safety Ratchet — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 4 beads 4.3 + 4.4 + 4.11 (disclosed coupling — one machine, three debt classes)
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Beads:** `claude-or1m.9` (4.3), `claude-or1m.10` (4.4), `claude-or1m.11` (4.11)
- **Implementation PR:** [#1285](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1285)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** controls implemented; merge fields are recorded in Beads/Dolt after review

## Dependency resolution (recorded per the epic's entry criteria)

The blueprint gated 4.3/4.11 on "Epic 6's ratchet machinery." Epic 6 is unactivated; blocking
Epic 4's completion on it would invert the program order. Resolution, under the owner's
"finish epic 4" authorization: the machinery is built NOW on the E3.11 ratchet pattern —
`scripts/check-safety-ratchet.mjs` + `scripts/safety-ratchet-baseline.json`. If Epic 6 later
ships a generalized ratchet substrate, this gate is its first migration customer, not a
blocker.

## What shipped

Four frozen debt classes, each pinned by **three keys** (count · sorted-set SHA-256 ·
validator schema version), blocking in the `validate` job:

| Class                                                                                                  | Baseline (measured)                                                                                                    | Bead |
| ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- | ---- |
| `bare_bash` — first-party SKILL.md declaring unscoped `Bash`                                           | 1                                                                                                                      | 4.3  |
| `tier2_tool_safety` — bare Bash + Write/WebFetch, no Safety Justification                              | 1                                                                                                                      | 4.3  |
| `shell_substitution` — `[security] YAML field contains shell substitution` occurrences (`file::field`) | **7 first-party** (the blueprint's 10 counted mirror copies; mirrors are upstream-owned and excluded)                  | 4.4  |
| `agents_only_errors` — the `--agents-only` corpus error lines                                          | 252 lines / 253 terminal count (the blueprint's figure, confirmed; includes the schema 3.11.0 body-vs-allowlist check) | 4.11 |

Rules: totals monotone non-increasing; a **swap fails at equal count** (any member not in the
baseline is new debt); `shell_substitution` has **no waiver path in the gate source** — a test
pins that absence; a shrink passes and re-pins via `--write` in the shrinking PR
(script-generated, human-reviewed — the "bot-written" baseline).

## One owner for the classification logic

The metrics are computed by the canonical validator, not the gate: new `--safety-metrics`
mode (schema **4.1.0**, five-surface lockstep updated: validator literal, SCHEMA_CHANGELOG
head, 6767-b banner, CLAUDE.md, version-pin test) reuses `parse_allowed_tools` /
`tier2_check_tool_safety` / `check_yaml_shell_substitution` verbatim; the agents lane runs
`--agents-only` and captures its error lines.

## Verification

Gate unit tests 6/6 (growth, swap-at-equal-count, shrink, three-key shape, no-waiver-source
pin); python suite 55/55 after the version re-pin; live run: `safety-ratchet: OK (bare_bash=1
tier2_tool_safety=1 shell_substitution=7 agents_only_errors=252; schema 4.1.0)`. Register 790
rows for E4.3/E4.4/E4.11 flipped in this PR. Hosted CI final.
