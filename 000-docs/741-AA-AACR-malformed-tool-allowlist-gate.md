# Malformed Tool-Allowlist Gate — After-Action Review

- **Date:** 2026-08-16
- **Authority:** Blueprint 727, Epic 1 bead 1.11; schema changelog non-negotiable 7
- **Bead:** `claude-hz8f.3`
- **Implementation PR:** [#1206](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1206)
- **Reviewed head:** `79e0424a4cd04f311406c9afbf73d536222ddf19`
- **Merge commit:** `57800272b20e4321ff5286b9a7f9f48fcd2c913d`
- **Status:** Implementation merged and verified; Bead closure follows this filing transaction

## Outcome

The canonical skill-schema validator now rejects structurally malformed `allowed-tools` values at
every validation tier. Well-formed but vocabulary-unknown tool names remain advisory, preserving
their separate E3.3/E4.2 disposition. Valid CSV, space-separated, YAML-list, and folded-scalar forms
remain accepted. The observable fail-closed change advances the schema from 3.16.1 to 4.0.0 in the
validator and every live schema authority marker.

## Before and after

| Measure                                          |    Before |      After |
| ------------------------------------------------ | --------: | ---------: |
| Malformed synthetic value classified as an error |         0 | 1 per tier |
| Focused regression cases                         |        49 |         54 |
| First-party `SKILL.md` malformed declarations    | 0 / 2,802 |  0 / 2,802 |
| Provenance-marked mirror malformed declarations  |   0 / 377 |    0 / 377 |
| Mirror-owned folded scalar files preserved       |        10 |         10 |
| Schema version                                   |    3.16.1 |      4.0.0 |
| Required GitHub status contexts                  |         3 |          3 |

The census used tracked `SKILL.md` paths and classified mirrors only through applicable
`.source.json` ancestry. Of 3,179 tracked skills, 2,801 first-party and 337 mirror-owned files
declare `allowed-tools`. Both cohorts contain zero structurally malformed declarations. The ten
folded scalars resolve dynamically to one provenance root and five canonical/`.codex`
byte-identical pairs.

## Run evidence

- Red proof before the production edit:
  `python3 -m pytest tests/test_validate_skills_schema_frontmatter.py::test_malformed_allowed_tool_surfaces_error_at_every_tier -q`
  failed because `Bash(git add *` produced no error in standard mode.
- At the reviewed head and after merge,
  `python3 -m pytest tests/test_validate_skills_schema_frontmatter.py -q` passed 54/54.
- `python3 -m py_compile scripts/validate-skills-schema.py`, Ruff 0.15.22 lint and formatting,
  Prettier, `pnpm typecheck`, `pnpm lint`, and `pnpm run verify` passed.
- Documentation governance passed: generated index check (180 documents before this filing),
  authority gate (two effective claimants and ten canonical links), and five prose-anchor tests.
- `audit-harness conform --strict` reported 2,452 PASS, one existing marketplace advisory, and zero
  failures. The advisory is the harness's lack of a bundled marketplace schema, not an E1.11 gate.
- Exact-head GitHub checks passed: `ci-required`, `gitleaks`, `skill-conform`, the complete Validate
  Plugins fanout, PR Pre-screen, link check, both MiniMax reviews, and A-grade coach.

Broad local `pnpm test` encountered an untouched CLI dependency-loader defect: Vitest 2.1.9
resolved Vite 7.3.3 and failed before collection under Node 20 and 22. This PR changed no CLI,
package, or lock file; the authoritative GitHub CLI smoke and repository test matrices passed. The
dependency issue remains separate work and was not hidden or repaired inside this bead.

## Failure paths and independent review

Fixture tests refuse unbalanced tokens, empty scopes, illegal identifiers, non-string and blank
YAML-list members, and leading, middle, or trailing empty CSV fields. They also prove valid forms
still pass and unknown names remain warnings. Corpus tests fail if either provenance cohort becomes
empty, a malformed declaration enters either cohort, a folded scalar stops parsing, or a canonical
and `.codex` mirror pair diverges.

A non-implementing reviewer checked out the exact PR head in a fresh detached worktree, inspected
the complete seven-file diff, independently reproduced the census and folded-scalar inventory,
reran all 54 focused tests plus formatting and governance checks, and returned PASS. MiniMax's
earlier concerns about vacuous corpus discovery, a hard-coded mirror path, and the canonical
standard's self-changelog were corrected before that review. Greptile was checked, but its only
response was a trial-ended notice; it provided no findings and is not counted as review evidence.

## Merge topology, scope, and rollback

GitHub still required one human approval after all exact-head checks and independent review passed.
The platform owner authorized an administrator bypass for that topology gap. The bypass was
disclosed on PR #1206 and changed no branch rule, required context, workflow gate, or review policy.

The implementation changed the validator, focused tests, schema authorities, RTM marker, and
`CHANGELOG.md`. It changed no plugin or mirrored skill content, provenance record, workflow,
generated catalog, package, lockfile, credential, registry, contributor record, Plane projection,
branch protection, or production state. `VALID_TOOLS`, the eight-field required set, and the
deprecated `compatible-with` behavior remain unchanged.

Rollback must reverse this filing transaction first so the generated index and public ledger remain
consistent, then run `git revert 57800272b20e4321ff5286b9a7f9f48fcd2c913d`. Rerun the focused
suite and corpus census; the expected reverted behavior is that malformed permission syntax returns
to advisory handling and every schema authority marker returns to 3.16.1.

## Lessons and next gate

Tool vocabulary and permission-string structure are different fact classes: structure can fail
closed without prematurely deciding the vocabulary migration. Executable, non-vacuous corpus tests
are stronger than a one-time zero-defect count. Epic 1 remains open; E1.11 closure does not activate
E3.3, E4.2, or any other bead.
