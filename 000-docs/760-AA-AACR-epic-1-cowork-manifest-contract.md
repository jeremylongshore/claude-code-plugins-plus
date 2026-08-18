<!-- doc-class: record -->

# Cowork Manifest Contract — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727 §13, Epic 1 bead 1.6
- **Bead:** `claude-hz8f.13`
- **Status:** implementation slice; final merge fields are recorded in Beads/Dolt after review

## Outcome

The Cowork page now fails closed when its generated manifest is absent or incomplete. It no longer
invents `300`/`1300`/`18` totals, guessed download URLs, or `Loading...` values. The grid consumes
the producer's `skills` and `commands` fields. The validator now uses the producer's canonical
`checksum` field, verifies a deterministic ten-plugin sample plus every bundle and the mega-zip,
and refuses missing, aliased, malformed, or mismatched checksums.

The clean-checkout measured Cowork population is 451 non-MCP catalog plugins, 2,998 packaged skills,
302 commands, 269 agents, 18 categories, and 28 pack rows. Generated archives and manifests remain
ignored build projections. No plugin, skill, `SKILL.md`, `.source.json`, mirrored content,
registry, credential, contributor, Plane, branch-rule, release, or production state changed.

## Evidence

| Gate                   | Result                                                                            |
| ---------------------- | --------------------------------------------------------------------------------- |
| Fixture contract tests | PASS — 7/7, including missing/alias/mismatch checksum red proofs                  |
| Cowork producer        | PASS — 451 plugin zips, 18 bundles, 27.4 MB mega-zip, 2,998 clean-checkout skills |
| Astro build            | PASS — 3,870 pages                                                                |
| Download validator     | PASS — 18 checks, 480 links, deterministic checksums                              |
| Manifest drift gate    | PASS — 451/451 plugins and 18/18 bundles aligned                                  |
| Count cohort gate      | PASS — `ALLOW cohorts=5 enforced=5 deferred=50 discovered=51`                     |
| Epic 1 measurement     | PASS — 37/37                                                                      |
| Generated-content gate | PASS — 8/8 plus 3,068/3,068 projections                                           |
| Changelog coverage     | PASS — 20/20 released tags                                                        |

## Failure and rollback

The old consumer/validator failure is reproduced by the tests: missing manifests and checksum
aliases are refused rather than silently accepted. Rollback is the focused revert of the consumer,
validator, contract-test, registry-reason, changelog, and this AAR changes, followed by the same
Cowork, cohort, generated-content, and measurement commands.

The producer's independent soft-failure and partial-manifest behavior remains a separately bounded
follow-up; it is not silently expanded into this slice.
