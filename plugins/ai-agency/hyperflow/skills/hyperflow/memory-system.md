# Project Memory System

Advanced project-scoped memory replacing the global `~/.claude/hyperflow-memory.md` approach. All data lives inside the project root under `.hyperflow/memory/`.

## Storage Layout

```
.hyperflow/memory/
├── index.md              # Quick-scan index: all entry titles, tags, dates, tier
├── learnings.md          # Discovered patterns and gotchas
├── decisions.md          # Architectural decisions + reasoning
├── pitfalls.md           # Failed approaches + why they failed
├── patterns.md           # Reusable code and architecture patterns
├── conventions.md        # Project-specific conventions learned mid-session
├── anti-patterns.md      # Recurring problem patterns curated from audit findings (hot-tier)
├── project-decisions.md  # Structural project-level answers memoized across spec runs (spec-tier)
└── archive/
    └── YYYY-MM.md        # Compressed cold entries, one file per month
```

`.hyperflow/` is gitignored. Memory is local to each developer's machine.

## Registered Memory Files

Files in `.hyperflow/memory/` that have a defined producer, consumer, and injection tier. All others follow the standard hot/warm/cold tiering based on entry age.

| File | Tier | Producer | Consumer | Notes |
|------|------|----------|----------|-------|
| `learnings.md` | hot/warm/cold (age-based) | orchestrator (after each batch) | all workers (tag-matched) | General patterns and gotchas |
| `decisions.md` | hot/warm/cold (age-based) | orchestrator (after each batch) | all workers (tag-matched) | Architectural decisions |
| `pitfalls.md` | hot/warm/cold (age-based) | orchestrator (after each batch) | all workers (tag-matched) | Failed approaches |
| `patterns.md` | hot/warm/cold (age-based) | orchestrator (after each batch) | all workers (tag-matched) | Reusable code patterns |
| `conventions.md` | hot/warm/cold (age-based) | orchestrator (after each batch) | all workers (tag-matched) | Project-specific conventions |
| `anti-patterns.md` | **hot — always injected** | audit Step 4d (anti-pattern curation Writer) | all workers, all sessions | See below |
| `project-decisions.md` | **spec-tier — spec pre-flight only** | spec Step 4 (post-collection append) | spec Step 4 (pre-flight read) | See below |

### anti-patterns.md (hot-tier)

Always loaded at session start alongside other hot-tier entries. Every worker prompt receives it regardless of task tags.

- **Producer:** audit Step 4d dispatches a Writer that reads the existing file, extracts up to 3 new entries from `[Critical]` and `[Important]` findings, and appends or increments frequency counters. The Step 4d Sonnet Reviewer validates dedup and frequency accuracy before the write lands.
- **Consumer:** injected into every worker prompt under `## Known anti-patterns` at session start. Workers use it to avoid repeating mistakes that prior audits flagged.
- **Format:**
  ```markdown
  ## <Pattern category> (e.g. Error handling, Naming, Dead code)
  - <description> — first observed in audit <YYYY-MM-DD>, frequency: <count>, last seen: <YYYY-MM-DD>
    Recommendation: <what workers should do to avoid this>
  ```
- **Compaction:** subject to the standard compaction protocol (default 300-line threshold, configurable via `memory.compactionThreshold`). Run `/hyperflow:cache compact` when the session-start advisory fires. See the Compaction Protocol section below.
- **Dedup rule:** before appending, the Writer checks for a semantic match in the existing file. On match: increment `frequency` and update `last seen`. Never create a duplicate entry.
- **New-entry cap:** max 3 new entries per audit run. When more than 3 eligible findings exist, prioritize multi-file findings over single-file findings.

### project-decisions.md (spec-tier)

Not hot-tier. Only spec Step 4 reads and writes it. Injecting it into every worker prompt would be waste — workers don't make structural project decisions; they implement them.

- **Producer:** spec Step 4 post-collection append — after the user answers the Smart Questions, the orchestrator scans answers for structural decisions (database choice, auth strategy, test framework, framework patterns, project-level defaults) and appends each one inline (no Agent dispatch; trivial per DOCTRINE §12.1).
- **Consumer:** spec Step 4 pre-flight memoization check — before generating the question list, spec reads this file and skips any question whose answer is already recorded. If a cached answer conflicts with the current task's requirements, the question fires anyway, framed as "project-decisions.md says X — does this task change that?"
- **Format:**
  ```markdown
  ## <Category>
  - <decision> (recorded <YYYY-MM-DD>, source chain: <task-slug>)
  ```
- **Compaction:** same threshold policy as other memory files. Entries are structural and rarely go stale, so compaction is infrequent in practice.
- **Scope:** only structural, project-wide decisions belong here. Task-specific answers (e.g., "use a modal for this feature") are excluded.

## Tag Taxonomy

Every entry carries tags drawn from this controlled vocabulary. Pick the minimum set that accurately describes the entry.

**Domain tags** (what area of the codebase):
`auth` `db` `api` `ui` `state` `testing` `build` `ci` `deploy` `perf` `security` `i18n` `rtl` `a11y`

**Type tags** (what kind of learning):
`pattern` `gotcha` `decision` `pitfall` `convention` `dependency-quirk`

Rules:
- Every entry must have exactly one type tag
- Every entry must have at least one domain tag
- Maximum four tags total per entry

## Entry Format

```markdown
### [YYYY-MM-DD] Short title  `[domain, type]`
**What:** One-line statement of the learning.
**Why it matters:** Context explaining when this applies.
**Evidence:** file:line reference or commit SHA where this was discovered.
```

### Examples

```markdown
### [2026-05-15] Zod schemas are the single source of truth for request validation  `[api, convention]`
**What:** All request validation goes through `src/shared/validation/` — never inline Zod in route handlers.
**Why it matters:** Duplicating schemas causes silent drift between validation and types.
**Evidence:** src/shared/validation/user.ts:1, confirmed by searching 23 route files.

### [2026-05-10] Prisma `findUnique` throws on missing relation if `select` omits it  `[db, gotcha]`
**What:** Selecting a relation field that's not in the include block silently returns null instead of throwing.
**Why it matters:** Leads to runtime null-dereference errors that only appear in production data paths.
**Evidence:** src/services/order.ts:88, commit a3f92c1.

### [2026-05-02] Tailwind v4 uses CSS variable tokens, not tailwind.config  `[ui, dependency-quirk]`
**What:** Color and spacing customizations live in CSS custom properties (`--color-*`), not `tailwind.config.js`.
**Why it matters:** Any attempt to extend via config is silently ignored in v4.
**Evidence:** tailwind.css:3-40.
```

## Hot / Warm / Cold Tiering

| Tier | Age | Load behavior |
|------|-----|---------------|
| Hot | ≤ 7 days | Always loaded at session start |
| Warm | 8–30 days | Loaded only when task tags match entry tags |
| Cold | > 30 days | Compressed to one-line summary; original archived to `archive/YYYY-MM.md` |

`index.md` always records tier alongside each entry so the orchestrator can decide without reading individual files.

### index.md Format

```markdown
| Date       | Tier | File          | Title                                          | Tags                      |
|------------|------|---------------|------------------------------------------------|---------------------------|
| 2026-05-15 | hot  | learnings.md  | Zod schemas are the single source of truth     | api, convention           |
| 2026-05-10 | warm | learnings.md  | Prisma findUnique throws on missing relation    | db, gotcha                |
| 2026-04-02 | cold | archive/2026-04.md | Tailwind v4 uses CSS variable tokens      | ui, dependency-quirk      |
```

## Read Protocol (Session Start)

1. Read `index.md` — always. It is small by design.
2. Load all **hot** entries in full (≤ 7 days).
3. Load `anti-patterns.md` in full — always, regardless of age or tags. It is permanently hot-tier (see Registered Memory Files above).
4. Infer tags from the current task description. Load **warm** entries whose tags overlap.
5. Skip **cold** entries unless user explicitly requests them (`hyperflow: memory show <tag>`).
6. Inject loaded entries into the first worker prompt under `## Learnings from prior sessions`. Inject `anti-patterns.md` under a separate `## Known anti-patterns` header.

Workers receive only the subset matching their task's inferred tags — never the full dump.

## Write Protocol (After Each Batch)

1. Orchestrator reviews worker outputs for candidate learnings.
2. Apply the test: "Would a worker on this project benefit from knowing this in 2 weeks?"
3. Discard ephemeral learnings (task-specific facts that won't recur).
4. Deduplicate against existing entries: if the same fact already exists (semantic match, not exact string), skip or update rather than append.
5. Append to the appropriate file using the entry format above.
6. Update `index.md` with the new row (tier = `hot`).

Write only from the orchestrator — never delegate memory writes to workers.

## Compression Protocol

Triggered at session start for any entry whose date crossed the 30-day threshold since last session.

1. Replace the full entry in its source file with a one-line summary:
   ```markdown
   ### [YYYY-MM-DD] Short title  `[tags]`  *(archived)*
   > Tailwind v4 uses CSS variable tokens, not tailwind.config. See archive/2026-04.md.
   ```
2. Append the original full entry to `archive/YYYY-MM.md` (month of the original entry date).
3. Update `index.md` tier to `cold` and point file column to `archive/YYYY-MM.md`.

## Pruning Protocol

Run at session start, after tiering is computed.

| Condition | Action |
|-----------|--------|
| Entry contradicted by a newer entry | Mark `[SUPERSEDED by YYYY-MM-DD entry]`; delete after 7 days |
| Entry references a file that no longer exists | Delete immediately; remove from index |
| Entry not referenced in any session after 90 days | Move to archive without summary |
| Cold entry in archive older than 180 days | Delete permanently |

"Referenced" means the entry was loaded (hot auto-load counts; warm tag-match counts).

## Lazy Injection

Workers receive only the memory subset relevant to their task:

1. Orchestrator infers tags from the worker's task description (e.g., "implement login flow" → `auth`, `api`, `state`).
2. Filter loaded entries to those sharing at least one tag.
3. Inject filtered entries under `## Learnings from prior sessions` in the worker prompt.
4. Never inject the full memory dump into any worker prompt.

## Migration from Legacy

On first session start in a project that has no `.hyperflow/memory/` but has `~/.claude/hyperflow-memory.md`:

1. Parse the legacy file for entries belonging to the current project path.
2. Map each bullet point to a `learnings.md` entry, tagging as `pattern` + best-guess domain.
3. Write migrated entries to `learnings.md` and update `index.md`.
4. Print: `Hyperflow — migrated N entries from ~/.claude/hyperflow-memory.md`
5. Do not delete the legacy file — the user may have other projects in it.

## User Controls

| Command | Effect |
|---------|--------|
| `hyperflow: memory off` | Disable memory reads and writes for the current session |
| `hyperflow: memory clear` | Wipe `.hyperflow/memory/` — prompts for confirmation first |
| `hyperflow: memory show <tag>` | List all entries (including cold) matching the tag |
| `hyperflow: memory show all` | Dump full index |

## Constraints

- `index.md` must stay under 200 lines. If it grows beyond that, prune cold entries aggressively.
- No code snippets in memory entries — patterns and facts only.
- Memory writes never block task execution. If a write fails, log and continue.
- Users may edit any memory file directly — it is plain markdown.

## Compaction Protocol

Memory files crossing a line-count threshold (default 300, configurable via `memory.compactionThreshold` in `~/.hyperflow/config.json`) can be compacted via the user-invoked `/hyperflow:cache compact` subcommand. Compaction summarises entries older than 7 days into stub lines and preserves the full text in monthly archive sidecars at `<memory-dir>/archive/YYYY-MM.md`.

A non-blocking session-start advisory is emitted by the Session-start lineCount checker when any tracked memory file's cached `lineCount` (stored in `.hyperflow/memory/.checksums`, scoped to memory files only — not to be confused with `.hyperflow/.checksums` which the scaffold staleness check owns) meets or exceeds the threshold.

The stub format is:

```
### [YYYY-MM-DD] Short title  [domain, type] — summarized, see archive/YYYY-MM.md
```

The Date/tag parser accepts BOTH `[domain, type]` (new) and `` `[domain, type]` `` (legacy backticked) so existing entries remain eligible after the feature lands.

Idempotency is guaranteed by source-side stub-line match and archive-side header match (both check date + title + tags). Re-running `/hyperflow:cache compact` on a fully compacted file produces no new writes.

See `skills/cache/references/compaction.md` for the full protocol (Compaction Writer dispatch, Dedup Reviewer reuse, Archive-sidecar writer details).
