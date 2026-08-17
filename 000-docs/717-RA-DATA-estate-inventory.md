# 717-RA-DATA — Estate Inventory (Mission 01)

**Captured:** 2026-08-11 @ `4358a65a3` · **Machine-readable:** `717-RA-DATA-estate-inventory.json`

Per-area counts with the authority that governs each area. "Authority" = where the rules live;
"unresolved" areas carry a register row (doc 719) instead of an authority.

| Area                                         | Count           | Authority                                                            |
| -------------------------------------------- | --------------- | -------------------------------------------------------------------- |
| Plugin dirs (`plugins/*/*/`)                 | 474             | `marketplace.extended.json` + CLAUDE.md § Plugin Structure           |
| Plugin manifests (`plugin.json`)             | 621             | excess over dirs = `.codex/` shadow copies (doc 722)                 |
| SKILL.md in plugins                          | 3,179           | `validate-skills-schema.py` (prose-spec, authoritative)              |
| SKILL.md curated mirror (`skills/.curated/`) | 1,921           | GENERATED — `promote-to-curated.py`, gate `promote-curated-check`    |
| SKILL.md root `skills/` (non-curated)        | 500             | unresolved → register row                                            |
| Command files                                | 379             | plugin structure spec                                                |
| Agent files                                  | 347             | kernel-strict agent gate (advisory lane; baseline in doc 721)        |
| MCP plugin dirs                              | 15              | CLAUDE.md § Plugin Structure                                         |
| Hook-bearing files                           | 306             | per-plugin                                                           |
| npm workspace packages                       | 4               | `analytics-daemon`, `analytics-dashboard`, `cli`, `plugin-validator` |
| Catalog entries (extended = derived)         | 471 = 471       | extended is SoT; `marketplace.json` GENERATED                        |
| External mirrors (`.source.json`)            | 63              | `sources.yaml` + sync-external (curated:true = frozen)               |
| Workflows                                    | 31              | CLAUDE.md § CI gate architecture                                     |
| Root `*.test.mjs`                            | 9               | `pnpm test`                                                          |
| `tests/` files                               | 408             | mixed; Python subset has no runner (doc 721 gap)                     |
| Python test files                            | 39              | no runner config — recorded gap                                      |
| freshie tracked files                        | 66              | `freshie/README.md`; Dolt = versioned SoR                            |
| `scripts/`                                   | 86              | validator/CI tooling                                                 |
| Tracked docs (`000-docs/`)                   | 143 at baseline | doc-filing v4.4; crosswalk doc 720                                   |

Notes: `analytics-daemon` test script stubs exit 0; `analytics-dashboard` has no test script —
both recorded as test-on-nothing gaps (doc 721), not fixed here.
