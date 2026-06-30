# Feature / Phase task structure

For work large enough to split into **sequential phases**, Hyperflow organizes artefacts as a self-contained
**feature folder** whose **phases are sub-folders**, each encapsulating *everything* for that phase — its own
`tasks/` folder plus the phase's design, research, and decisions. This replaces the single flat task file **only
for multi-phase features**; small / single-phase work keeps the flat
[`.hyperflow/tasks/<slug>.md`](task-tracking.md) model unchanged.

## When to use a feature (vs. a flat task file)

The **Planner** (scope Step 3) decides during decomposition. Use the **feature/phase structure** when **≥ 2
phases** are warranted — i.e. the work has natural sequential stages with dependencies or milestones between them:

| Use a flat task file | Use a feature with phases |
|---|---|
| One coherent unit of work, even if many sub-tasks | Distinct sequential stages (e.g. data layer → API → UI) |
| All batches can complete in one pass | A later stage depends on an earlier stage shipping first |
| Single design, single review surface | Each stage has its own design + review surface |
| `triage.complexity ≤ moderate`, single milestone | `complexity = complex` / `scope ∈ {cross-cutting, system-wide}` with ≥ 2 milestones |

A phase is **not** the same as a batch. Batches are the parallel-dispatch unit *inside* a phase; phases are
sequential milestones with their own encapsulated artefacts. One phase contains one or more batches.

## Directory layout

```
.hyperflow/
├── features/
│   └── <feature-slug>/            # e.g. checkout-redesign/
│       ├── feature.md             # feature overview: status, phase roster, dependency graph
│       ├── phase-1-<name>/        # e.g. phase-1-data-layer/
│       │   ├── phase.md           # phase status, goal, exit criteria, task roster
│       │   ├── tasks/             # one file per task (replaces the single combined file)
│       │   │   ├── T1-<slug>.md
│       │   │   └── T2-<slug>.md
│       │   ├── spec.md            # this phase's design — architecture, data flow, key decisions ("the blends")
│       │   ├── research.md        # findings, links, scratch work for the phase
│       │   └── decisions.md       # ADR-style decisions + phase-scoped learnings (roll up to memory on completion)
│       ├── phase-2-<name>/
│       │   └── … (same shape)
│       └── phase-3-<name>/
│           └── …
└── tasks/                         # small / single-phase work stays here (unchanged)
    └── fix-redirect.md
```

Phase folders are named `phase-<n>-<kebab-name>`; the numeric prefix fixes execution order. The optional files
(`spec.md`, `research.md`, `decisions.md`) are created only when the phase has content for them — an empty phase
folder carries just `phase.md` + `tasks/`.

## File templates

### `feature.md`

```markdown
# Feature: <Name>

## Status

| Field       | Value                                              |
|-------------|----------------------------------------------------|
| Status      | planning \| in_progress \| completed               |
| Phases      | `██████░░░` 2 / 3 complete                          |
| Branch      | `feat/<slug>`                                       |
| Specialists | <Brain-decided roster across the whole feature>    |

## Goal

<one-line plain-English statement of what shipping this feature changes>

## Phases

1. **phase-1-<name>** — <goal> — `completed`
2. **phase-2-<name>** — <goal> — `in_progress` (depends on phase-1)
3. **phase-3-<name>** — <goal> — `pending` (depends on phase-2)

## Phase dependency graph

```
phase-1-data-layer → phase-2-api → phase-3-ui
```
```

### `phase.md`

```markdown
# Phase <n> — <Name>

## Status

| Field       | Value                                          |
|-------------|------------------------------------------------|
| Status      | pending \| in_progress \| in_review \| completed |
| Progress    | `██████░░░░` 3 / 5 tasks (60%)                  |
| Depends on  | phase-<n-1> (or — for the first phase)          |
| Specialists | <responsible specialists for this phase>        |

## Goal

<what this phase delivers on its own>

## Exit criteria

- [ ] <concrete, verifiable condition that ends this phase>

## Tasks

- [x] T1 — <Role> · <one-line task> · Specialist: <reviewer>   → `tasks/T1-<slug>.md`
- [ ] T2 — <Role> · <one-line task> · Specialist: <reviewer>   → `tasks/T2-<slug>.md`

## Artefacts

- `spec.md` — design for this phase
- `research.md` — findings
- `decisions.md` — decisions + learnings
```

### `tasks/T<n>-<slug>.md`

One file per task — the same content the flat model puts in a combined file, scoped to a single task. Follows the
per-task line shape in [`artefact-format.md`](artefact-format.md) (Role, Read/Modify/Create, Complexity,
Specialist) plus a small status block. Checked off in the parent `phase.md` task roster on PASS.

## Lifecycle

```
Planner decides ≥2 phases
    │
Create features/<slug>/ + feature.md + phase-N folders (phase.md + tasks/ each)
    │
For each phase in order:
    ├─ (optional) write phase spec.md / research.md from the design
    ├─ dispatch the phase's tasks/ in batches (parallel inside the phase)
    ├─ per-task PASS → check off in phase.md → commit
    ├─ phase exit criteria met → phase.md status = completed → roll decisions.md learnings to memory
    └─ advance to the next phase (gated on its `Depends on`)
    │
All phases completed → feature.md status = completed → archive the feature folder
```

Phases run **sequentially** by dependency; tasks **inside** a phase run in parallel batches exactly as today.
A phase does not start until its `Depends on` phase is `completed` (the dispatch phase-scope gate decides whether phases run all-at-once or phase-by-phase).

## Status rollup

- A **task** completes → checked off in its `phase.md` roster + the phase Progress bar advances.
- A **phase** completes (all tasks PASS + exit criteria met) → `phase.md` status `completed` + `feature.md` Phases
  bar advances + `decisions.md` learnings append to `.hyperflow/memory/`.
- All phases complete → `feature.md` status `completed`; the feature folder is eligible for archival
  (`.hyperflow/archive/features/YYYY-MM/<slug>/`).

`/hyperflow:status` reads `feature.md` for the phase roster and each active `phase.md` for live task progress.

## Constraints

- Use phases only for genuine sequential stages — never split a single coherent unit into ceremonial phases.
- Max phases per feature: keep it readable (typically 2–6). More than that usually means two features.
- A phase's `tasks/` follows the flat-task constraints (≤ 10 tasks per phase; decompose further if more).
- `.hyperflow/features/` is gitignored like the rest of `.hyperflow/`.
- Backward compatible: existing flat `.hyperflow/tasks/<slug>.md` files and single-phase work are untouched.
