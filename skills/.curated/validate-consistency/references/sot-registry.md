# Source-of-Truth Registry (sot-map.yaml)

## Purpose

Defines the per-fact-class authority registry that replaces the retired global source-of-truth hierarchy. Authority is **declared as data, per fact class, by a human** — never a global ranking, never auto-detected at runtime. When two artifacts disagree about a fact, the registry row for that fact's class names the artifact class that owns the fact; the finding is filed against the other artifact. A fact class with no row is **unowned**: the conflict is reported for human adjudication and no winner is ever named.

## Location

Default: `~/000-projects/intent-os/sot-map.yaml`. The path is configurable per invocation (argument or explicit instruction to the skill). Missing or unparseable registry → bootstrap mode (all fact classes unowned).

## File Format

```yaml
version: 1
fact_classes:
  version:                              # key = fact_class (snake_case / dotted)
    owner: package-manifest             # required — the ONE producing surface
    mirrors:                            # surfaces expected to restate the fact;
      - readme                          #   each diffed against the owner only
      - changelog                       #   (star topology — never pairwise N×N)
    determinism: deterministic          # deterministic | llm-judged
    depth_tier: T1                      # T1 value-equality | T2 judged/semantic
    staleness_bound: 0                  # days a mirror may lag before lag = drift
    criticality: high                   # critical | high | medium (severity ceiling)
    volatile: false                     # true = mirrors expected to trail (Info-level
                                        #   replication lag inside the bound)
    adjudicated_by: jeremy              # optional provenance — who made the call
    adjudicated_on: YYYY-MM-DD          # optional provenance — when
  license:
    owner: license-file
    mirrors: [readme]
    determinism: deterministic
    depth_tier: T1
    staleness_bound: 0
    criticality: high
    volatile: false
```

Rows are added, edited, and committed by a human. The validator only reads this file — it never writes it. Bootstrap drafts (below) are emitted in the report for a human to review and paste.

## Fact-Class Vocabulary

| Fact class | Produced by check | Notes |
|------------|-------------------|-------|
| `version-string` | 3.2 | Version numbers across VERSION, manifests, CHANGELOG, README, CLAUDE.md |
| `ci-commands` | 3.3 | Test/build/lint commands: README claims vs workflow `run:` steps |
| `license` | 3.7 | License identifier: README vs LICENSE file vs manifest field |
| `runtime-version` | 3.7 | Language/runtime version: README vs manifest vs CI matrix |
| `repository-url` | 3.7 | Repo URL: README vs manifest vs git remote |
| `project-description` | 3.7 (advisory) | Semantic comparison — findings are advisory-only |
| `phase-status` | 3.5 (advisory) | Stale phase/status language — findings are advisory-only |
| `capability-claims` | 3.6 (advisory) | Feature claims vs implementation — findings are advisory-only |
| `planning-status` | 3.9 (advisory) | Planning-vs-implementation state — findings are advisory-only |

Referential-integrity checks (3.1 index-vs-filesystem, 3.4 CLAUDE.md path references, 3.8 broken cross-references) need no registry row: the filesystem is the definitional referent, not a competing authority.

## Artifact-Class Vocabulary

Values accepted in a row's `owner` field:

| Artifact class | Meaning |
|----------------|---------|
| `code` | Implemented behavior in source files |
| `tests` | Verified behavior asserted by the test suite |
| `workflow-yaml` | CI workflow definitions (`.github/workflows/`) |
| `package-manifest` | `package.json`, `pyproject.toml`, `Cargo.toml`, gemspec, `go.mod`, VERSION |
| `license-file` | The LICENSE file itself |
| `canonical-docs` | `000-docs/`, `docs/` |
| `readme` | README.md |
| `claude-md` | CLAUDE.md |
| `planning-docs` | `planning/`, roadmaps |
| `task-tracker` | Beads/issue trackers |
| `published-website` | The live published site |
| `cms-source` | CMS/content source files |

## Resolution Rule

When two artifacts disagree on a fact of class F:

1. Registry has a row for F → the artifact belonging to the row's `owner` class is correct; the finding is filed against the other artifact and cites the row.
2. Registry has no row for F → emit `unowned fact-class — human adjudication needed`. List every value with its location, symmetrically. Name no winner. Never guess, never fall back to a ranking.

## Appendix — Legacy Hierarchy (bootstrap heuristic ONLY)

The tables below are the retired v1 global hierarchies. They are **not runtime authority** and are never used to resolve a conflict. They exist solely as the drafting heuristic for proposing registry rows during bootstrap: detect the project type (marker scan — see SKILL.md § Bootstrap), pick the matching table, and draft one row per unowned fact class mapping it to the artifact class that table would have favored. Every drafted row is emitted as `bootstrap draft — requires human adjudication`; the old resolution rule ("Rank N beats Rank M") is retired.

### Engineering-repo drafting table

| Rank | Artifact | Rationale |
|------|----------|-----------|
| 1 | Code (implemented behavior) | What actually runs is what actually matters |
| 2 | Tests (verified behavior) | Tests assert what code should do — if they pass, the behavior is verified |
| 3 | CI/Workflows (automation reality) | What CI actually runs is the real validation pipeline |
| 4 | Canonical docs (`000-docs/`, `docs/`) | Current system documentation — should track code closely |
| 5 | README | Public front door — must not overclaim or underclaim |
| 6 | CLAUDE.md | Repo-operational guidance — should reflect actual project state |
| 7 | Planning docs (`planning/`, roadmaps) | Future-state unless explicitly marked as implemented |
| 8 | Beads/task trackers | Execution state — tracks intent, not reality |

### Marketing/content-site drafting table

| Rank | Artifact |
|------|----------|
| 1 | Published website |
| 2 | CMS/content source |
| 3 | GitHub README |
| 4 | Local docs |

### Hybrid

Draft code-related fact classes from the engineering table and content-related fact classes from the marketing table.

### Key principles (drafting rationale)

1. **Code never lies** — it may be buggy, but it's the actual behavior
2. **Tests are assertions** — passing tests confirm behavior; failing tests indicate known gaps
3. **Docs are claims** — they describe intended or believed behavior, which may have drifted
4. **Planning is aspirational** — roadmap items are NOT features until code implements them
5. **Trackers are process** — task status reflects workflow state, not code state
