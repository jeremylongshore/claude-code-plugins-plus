# Compound Commands — Plane Behavior Observatory

Each command answers a question that **cannot** be answered from any single Plane API endpoint. Each is derived from the NOI (`references/noi.md`) and the Project / Workflow archetype's default `velocity / stale / bottleneck` triplet, adapted to Plane's behavioral observatory framing.

## Command 1 — `/plane-cycle-velocity`

**Question**: Does this team's cycle velocity match its planning?

**Synthesizes**:
- `list_cycles` → enumerate completed cycles
- `get_cycle` (per cycle) → planned start/end + actual completion counts
- `list_cycle_issues` (per cycle) → estimate_point sum vs. completed_issues sum
- `get_issue_worklogs` (sample) → actual time spent per issue (if estimate_point unset)

**Output**:

```
PROJECT: braves-booth
Cycles analyzed: 8 most recent

Cycle              Planned   Completed  Overrun   Estimate   Actual    Variance
─────────────────  ────────  ─────────  ────────  ─────────  ────────  ────────
Sprint 14          14d        18d        +4d       42 pts     58 pts    +38%
Sprint 13          14d        14d         0d       38 pts     34 pts    -10%
Sprint 12          14d        21d        +7d       45 pts     61 pts    +36%
Sprint 11          14d        14d         0d       40 pts     42 pts     +5%
...

Pattern: 4/8 cycles overrun by ≥ 4 days. Mean variance: +21%.
Behavioral signal: cycle planning is ~20% optimistic — either reduce
scope per cycle or extend cycle length.
```

**Caching**: cycle data is immutable once a cycle closes; cache by cycle ID in `~/.cache/plane-skill/cycles.sqlite`.

## Command 2 — `/plane-stale-tickets`

**Question**: Which tickets are quietly failing under shared ownership?

**Synthesizes**:
- `list_project_issues` → open issues
- `list_states` → identify "In Progress" state UUIDs
- `get_issue_comments` (per stale candidate) → assignee changes during the open window

**Output**:

```
PROJECT: braves-booth
Threshold: In Progress > 14 days

Issue            Days In   Assignee Churn   Last Comment   Score
───────────────  ────────  ───────────────  ─────────────  ─────
BRAVES-78        29d       3 assignees      11d ago        9.2 ⚠
BRAVES-91        21d       2 assignees      4d ago         5.1
BRAVES-85        18d       1 assignee       2d ago         2.8

Score = days_in × (1 + assignee_churn) × (days_since_last_comment / 7)

Behavioral signal: BRAVES-78 has 3 assignees and hasn't moved in 11 days
— classic shared-ownership orphan. Assign one owner or close as won't-do.
```

**Caching**: open-issue list is mutable; refresh on each invocation.

## Command 3 — `/plane-reviewer-gate-strength`

**Question**: Which reviewers gate-keep harder than the spec demands?

**Synthesizes**:
- `list_project_issues` filtered to recently-closed
- `get_issue_comments` (per closed issue) → look for "blocked by reviewer" pattern + reviewer assignment timing

Heuristic for blocker detection: a comment containing a state-change to "blocked" or text matching `/blocked|review|approval/i`, followed by a comment lifting the block.

**Output**:

```
PROJECT: braves-booth
Period: last 30 days

Reviewer    Issues Gated   Mean Time Blocked   Verdict
──────────  ─────────────  ──────────────────  ──────────────────────
Alice         12             1.2 days           Engineer-fast clearance
Bob            8             6.8 days           Bottleneck — not a senior
Carol         15             2.1 days           Healthy review cadence

Behavioral signal: Bob's 6.8-day mean indicates a process bottleneck.
Either re-route reviews, define explicit review SLAs, or split Bob's
queue.
```

**Note**: this command doesn't define "good" or "bad" reviewer behavior — the score surfaces friction, the human decides whether the friction is intentional (security review) or unintentional (overload).

## Command 4 — `/plane-priority-drift`

**Question**: Does the team plan high-priority work but ship low-priority work?

**Synthesizes**:
- `list_cycles` → recent closed cycles
- `list_cycle_issues` (per cycle) → priority distribution at planning time
- Cross-reference with `get_issue_using_readable_identifier` for issues marked `completed` in the cycle

**Output**:

```
PROJECT: braves-booth
Cycles analyzed: 8 most recent

Priority   Planned    Shipped    Drift
─────────  ─────────  ─────────  ─────────
urgent          12         4      -67%
high            38        18      -53%
medium          24        31      +29%
low              8        29     +263%

Pattern: 67% of planned urgents and 53% of planned highs do not ship
in the cycle they're planned in. Meanwhile low-priority work ships
+263% above plan.

Behavioral signal: the planning conversation does not reflect what
actually gets done. Either the team plans theatrically and ships
opportunistically, or planning is happening at the wrong time/place.
```

**This is the NOI-specific compound command** — not in the default Project/Workflow archetype set; added because the NOI's "stated-vs-actual priority drift" framing demands it.

## Command 5 — `/plane-cross-project-load`

**Question**: Which engineers are spread across too many active projects?

**Synthesizes**:
- `get_workspace_members` → engineer roster
- `list_project_issues` (across all active projects, filtered to assignee × open state)
- `list_modules` (used as a project-internal grouping signal)

**Output**:

```
WORKSPACE: internal
Active projects: 14

Engineer        Projects   Active Cycles   Open Issues   Verdict
──────────────  ─────────  ──────────────  ────────────  ─────────────
Alice               7            6              42        Stretched
Bob                 4            4              23        Healthy
Carol              11            9              68        Crisis ⚠
David               2            2               9        Focused

Behavioral signal: Carol is on 11 active projects and 9 active cycles
— that's not focus, that's project-management debt. Either consolidate
projects or rotate Carol off most.
```

**Caching**: assignment data is mutable; refresh on each invocation.

## How agents consume this

`plane-expert` agent reads from `api-surface.md` and answers "how do I query X" questions about the Plane API.

`plane-analyst` agent reads from `noi.md` + this file and orchestrates the compound commands above. The orchestrator skill (`SKILL.md`) routes to one or the other based on user intent: "tell me about Plane endpoint X" → expert; "how is my team behaving in cycle Y" → analyst.

## When new compound commands are added

Constraint: any new command must answer a behavioral question that the NOI implies. If a command can be answered by a single endpoint call (e.g., "list issues assigned to me"), it does not belong here. Add it to a separate utility skill or call `mcp__plane` directly.
