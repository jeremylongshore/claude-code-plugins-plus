# Flow profiles

## Purpose

Flow profiles are complete execution templates the orchestrator selects after triage. Each profile is a self-contained recipe — specifying worker count, reviewer count, brainstorm depth, context budget, parallelization rules, and exit criteria — so the orchestrator never has to invent a pipeline on the fly. Profiles solve the rigidity problem of the old fixed pipeline: instead of every task going through the same heavyweight sequence, the orchestrator picks the lightest profile that safely handles the task, then escalates mid-flight only when unexpected complexity emerges.

## Profile selection (input → profile)

The orchestrator reads the triage output and maps it to exactly one profile. When multiple types are present, the strictest profile wins (see composition rules).

| Complexity   | Scope          | Risk          | Ambiguity | Types include       | Profile    |
|--------------|----------------|---------------|-----------|---------------------|------------|
| trivial      | single-file    | reversible    | < 0.3     | any                 | fast       |
| simple       | ≤ 5 files      | reversible    | any       | no scientific       | standard   |
| moderate     | ≤ 5 files      | reversible    | any       | no scientific       | standard   |
| complex      | any            | any           | any       | no scientific       | deep       |
| any          | cross-cutting  | any           | any       | no scientific       | deep       |
| system-wide  | any            | any           | any       | no scientific       | deep       |
| research     | any            | any           | any       | any                 | research   |
| moderate+    | any            | any           | any       | ui, creative        | creative   |
| any          | any            | any           | any       | scientific          | scientific |
| any          | any            | irreversible  | any       | correctness-domain  | scientific |

---

## The 6 profiles

### Profile: fast

**Use when:** The task is trivial, touches a single file, is fully reversible, and has no ambiguity.

**Triage signature:**
- complexity: trivial
- scope: single-file
- risk: reversible
- ambiguity: < 0.3
- types: any (except scientific)

**Pipeline:**
1. Brainstorm: silent recap only — orchestrator silently confirms intent, no questions asked
2. Research: none — 0 searchers
3. Task file: no
4. Workers: 1 worker, sequential, implementer persona
5. Review: inline self-review by orchestrator after worker returns; no separate reviewer agent dispatched
6. Quality gates: changed-file only (lint + type-check on affected file)
7. Commit: yes, single atomic commit

**Token budget:** ≤ 30 000 tokens (soft target)

**Agent counts:**
- Thinking: 1 (orchestrator only; inline review = no separate dispatch)
- Worker: 1

**Skip conditions:** Never — fast is already the minimal profile; it cannot be downgraded further.

**Upgrade conditions:** Worker returns `ESCALATE` flag (unexpected complexity, cross-file side effects discovered) → bump to standard. See [escalation.md](escalation.md) for full escalation rules.

**Example invocations:**

```text
"Rename the `getUserById` function to `fetchUserById` throughout the auth module"
"Fix the typo in the error message on line 42 of api/errors.ts"
"Bump the version string in package.json to 2.1.4"
```

**Anti-patterns:** fast is NOT for tasks that touch more than one file, require research, have design decisions, or carry any irreversibility risk.

---

### Profile: standard

**Use when:** The task is simple or moderate complexity, touches ≤ 5 files, has no cross-cutting concerns, and is fully reversible.

**Triage signature:**
- complexity: simple or moderate
- scope: ≤ 5 files, no cross-cutting
- risk: reversible
- ambiguity: any
- types: any (except scientific)

**Pipeline:**
1. Brainstorm: light — 1 clarifying question max, skip if intent is unambiguous
2. Research: conditional — 1 searcher dispatched only if an external API, library behavior, or unknown pattern is involved
3. Task file: yes — created before dispatching workers
4. Workers: 1–2 parallel workers, implementer persona; split by file boundary when 2 are used
5. Review: 1 batch reviewer (thinking model) after all workers complete
6. Quality gates: full suite on changed files (lint, type-check, unit tests for touched modules)
7. Commit: yes, single commit per logical task

**Token budget:** ≤ 100 000 tokens (soft target)

**Agent counts:**
- Thinking: 1–2 (orchestrator + optional reviewer)
- Worker: 1–2 implementers + 0–1 searcher

**Skip conditions:** Discovered mid-flight to be single-file and trivial → downgrade to fast (save the task file overhead, skip batch reviewer).

**Upgrade conditions:** Worker discovers cross-cutting impact or scope expands beyond 5 files → escalate to deep. See [escalation.md](escalation.md).

**Example invocations:**

```text
"Add a newsletter signup form to the marketing page with client-side validation"
"Wire up the /settings route to the existing SettingsPage component"
"Add a `role` column to the users table and write the migration"
```

**Anti-patterns:** standard is NOT for cross-cutting refactors, system-wide changes, anything requiring TDD as a correctness guarantee, or tasks with design-first requirements.

---

### Profile: deep

**Use when:** The task is complex, cross-cutting, or system-wide; multiple subsystems are affected; or the implementation requires coordination across many files and modules.

**Triage signature:**
- complexity: complex, OR
- scope: cross-cutting or system-wide
- risk: any
- ambiguity: any
- types: any (except scientific, which overrides to scientific regardless)

**Pipeline:**
1. Brainstorm: standard depth — 2–3 targeted questions covering approach, constraints, and integration points
2. Research: parallel — 2–3 searchers dispatched simultaneously to cover affected subsystems
3. Task file: yes — mandatory before any worker dispatch; includes sub-task breakdown
4. Workers: 3–5+ parallel workers across multiple batches; each batch covers one logical slice; personas: implementer, test-writer, migration-writer as needed
5. Review: per-batch reviewer after each batch, plus a final integration reviewer (thinking model) after all batches complete
6. Quality gates: full suite — lint, type-check, unit tests, integration tests, no regressions
7. Commit: yes, one commit per completed sub-task (not per batch)

**Token budget:** 200 000–500 000 tokens (soft target; varies by subsystem count)

**Agent counts:**
- Thinking: batches + 1 minimum (integration reviewer always present per Layer 3 rule)
- Worker: 3–5+ implementers across batches

**Skip conditions:** Mid-flight discovery that scope is smaller than triage suggested (e.g., only 2 files, no cross-cutting) → downgrade to standard; reuse already-created task file.

**Upgrade conditions:** Not applicable — deep is the highest general-purpose profile. Tasks requiring correctness guarantees escalate to scientific instead. See [escalation.md](escalation.md).

**Example invocations:**

```text
"Implement JWT-based authentication with refresh tokens across the API and frontend"
"Refactor the data access layer to use the repository pattern throughout"
"Add multi-tenant support with row-level security to the existing schema"
```

**Anti-patterns:** deep is NOT for tasks that can be expressed as a single logical unit within 5 files, and NOT for tasks where numerical correctness or proof-level validation is required.

---

### Profile: research

**Use when:** Triage classifies the task type as research — the goal is evaluation, exploration, or understanding rather than implementation.

**Triage signature:**
- complexity: research (unknown territory, evaluation, or audit)
- types: includes research or analysis
- risk: any (output is usually read-only)
- ambiguity: any

**Pipeline:**
1. Brainstorm: light — 1 question to sharpen the research question; skip if question is already precise
2. Research: heavy — 3+ parallel searchers dispatched simultaneously; this is the core of the flow
3. Task file: optional — only if the research output must be persisted (e.g., an ADR or comparison doc)
4. Workers: 0–1 implementer (only for a proof-of-concept prototype, only if explicitly requested)
5. Review: 1 reviewer if any code was changed; skip entirely for read-only research runs
6. Quality gates: none if read-only; changed-file gates only if prototype was written
7. Commit: no if read-only; yes if prototype or docs were created

**Token budget:** ≤ 80 000 tokens (searchers are cheap; output is mostly synthesis text)

**Agent counts:**
- Thinking: 1–2 (orchestrator performs heavy synthesis after searchers return)
- Worker: 3+ searchers, 0–1 implementer

**Skip conditions:** Not applicable — research cannot be downgraded; if less research is needed the triage should have returned a different type.

**Upgrade conditions:** Prototype reveals hidden complexity → escalate implementer work to standard or deep. See [escalation.md](escalation.md).

**Example invocations:**

```text
"Should we use Postgres or DynamoDB for the events table given our query patterns?"
"What's the right state management approach for the new cart feature?"
"What does the auth module currently do? I need to understand it before touching it."
```

**Anti-patterns:** research is NOT for tasks where code must land; do not use research when the user expects a committed implementation.

---

### Profile: creative

**Use when:** Task types include ui or creative AND complexity is moderate or higher, OR design-dominant ambiguity is present (the "right" answer is aesthetic or experiential, not technical).

**Triage signature:**
- types: includes ui or creative
- complexity: moderate, complex, or research
- ambiguity: design-dominant (what it should look like/feel like is unclear)
- risk: any

**Pipeline:**
1. Brainstorm: full 6-dimension brainstorm (section-by-section approval per [brainstorming-advanced.md](brainstorming-advanced.md)); no code is written until brainstorm is approved
2. Research: optional — 1–2 design-exploration agents to gather visual references or component patterns if needed
3. Task file: yes — created after brainstorm approval, captures approved design direction
4. Workers: 1 implementer dispatched only after design approval; 1 additional implementer for complex multi-component UIs
5. Review: 1 reviewer covering visual fidelity + accessibility (WCAG AA minimum, AAA target)
6. Quality gates: lint, type-check, accessibility audit on changed components
7. Commit: yes, after quality gates pass

**Token budget:** ≤ 150 000 tokens (brainstorming is thinking-heavy)

**Agent counts:**
- Thinking: 2–3 (brainstorming is the expensive phase)
- Worker: 1–2 implementers + 1 reviewer

**Skip conditions:** If brainstorm reveals the task is actually trivial (e.g., change a color variable) → downgrade to fast after brainstorm; skip task file.

**Upgrade conditions:** Implementation reveals accessibility or interaction complexity beyond initial scope → escalate to deep. See [escalation.md](escalation.md).

**Hard rule:** No code is dispatched until the brainstorm is explicitly approved. This is non-negotiable per the Layer 4 rule in SKILL.md.

**Example invocations:**

```text
"Design and build a hero section for the marketing landing page"
"Create an animated onboarding flow with step-by-step progress"
"Build a data visualization dashboard with interactive charts"
```

**Anti-patterns:** creative is NOT for purely structural changes with no visual design component, and NOT for tasks where the "right" implementation is objectively deterministic.

---

### Profile: scientific

**Use when:** Task types include scientific, OR risk is irreversible-with-correctness, OR the task involves numerical computation, statistical logic, cryptography, financial calculation, or proof-level validation where an incorrect result causes real-world harm.

**Triage signature:**
- types: includes scientific, OR
- risk: irreversible-with-correctness, OR
- domain: numerical, cryptographic, financial, ML/statistical

**Pipeline:**
1. Brainstorm: standard — 2–3 questions covering spec clarity, expected outputs, edge cases, and numerical precision requirements
2. Research: yes — 1–2 searchers to verify mathematical correctness of the approach, check for known edge cases, review existing implementations
3. Task file: yes — includes spec section with expected inputs/outputs and edge case table
4. Workers: tests FIRST (TDD mandatory) — 1 test-writer dispatched before any implementer; then 1–2 implementers; test count must increase
5. Review: multi-level L1–L5 — spec review, code quality, edge case coverage, performance correctness, security implications (see [review-levels.md](review-levels.md))
6. Quality gates: full test suite must pass; no new code lands if any test introduced in this task is failing
7. Commit: yes, only after every quality gate passes; no partial commits

**Token budget:** 200 000–400 000 tokens (TDD multiplies tokens; correctness takes priority over speed)

**Agent counts:**
- Thinking: 3–5 (multi-level review is thinking-heavy)
- Worker: 2–3 (test-writer + 1–2 implementers)

**Skip conditions:** Not applicable — scientific cannot be downgraded. If triage classified a task as scientific, that classification must be respected regardless of apparent simplicity.

**Upgrade conditions:** Not applicable — scientific is the strictest profile. There is no higher profile to escalate to; additional complexity is absorbed within the scientific pipeline by adding review passes.

**Hard rule:** No implementation code is dispatched until the test-writer agent has completed. No commit is made until all tests — including newly written ones — pass. These rules are non-negotiable.

**Example invocations:**

```text
"Implement the subscription proration calculation for mid-cycle plan changes"
"Write the gradient descent training loop for the recommendation model"
"Optimize the fast Fourier transform used in the audio processing pipeline"
```

**Anti-patterns:** scientific is NOT for general CRUD operations, UI work, or anything where an off-by-one is a cosmetic inconvenience rather than a correctness failure.

---

## Composition rules (multi-type tasks)

When triage returns multiple types, exactly one profile is selected. The strictest profile always wins. Priority order (most strict first):

| Priority | Profile / Constraint | Notes |
|----------|----------------------|-------|
| 1        | scientific           | Correctness trumps speed; any scientific signal forces this profile |
| 2        | security type        | Not a profile itself, but forces minimum standard; blocks fast entirely — `types` includes `security` → never `fast` (minimum `standard`) |
| 2        | architect type       | Not a profile itself, but forces minimum standard; blocks fast entirely — `types` includes `architect` → never `fast` (minimum `standard`) |
| 2        | scientific type      | `types` includes `scientific` → never `fast`, minimum `standard`; if numerical-correctness or proof code → `scientific` profile |
| 2        | risk = irreversible  | `risk` = `irreversible` → never `fast` (minimum `standard`) |
| 3        | deep                 | Cross-cutting or complex scope |
| 4        | creative             | Design-dominant; code blocked until brainstorm approved — `types` includes `creative` AND complexity ≥ moderate → `creative` profile; `types` includes `creative` AND complexity < moderate → minimum `standard` (brainstorm depth still forced to `deep` per adaptive-brainstorming.md, but profile may downgrade for trivial creative tweaks like "change the hover color") |
| 5        | research             | Evaluation/exploration dominant |
| 6        | standard             | Default multi-file path |
| 7        | fast                 | Only reachable when no other signal exists |

**Example:** `types: [frontend, security]` → can never be fast; minimum profile is standard (security constraint forces it upward).

**Example:** `types: [frontend, architect]` → can never be fast; minimum profile is standard (architect constraint forces it upward).

**Example:** `types: [frontend, scientific]` → never fast; minimum standard; escalates to scientific if numerical-correctness or proof code is involved.

**Example:** `risk: irreversible, complexity: trivial` → can never be fast; minimum profile is standard (irreversibility constraint forces it upward).

**Example:** `types: [ui, creative], complexity: simple` → complexity < moderate so profile downgrades to standard, but brainstorm depth remains forced to `deep` per adaptive-brainstorming.md.

**Example:** `types: [ui, creative, scientific]` → scientific wins; full TDD pipeline applies even though the task has a visual component. Design brainstorm is folded into the scientific pipeline's brainstorm phase.

**Example:** `types: [research, frontend]` → research wins over standard; output is a recommendation, not committed code.

---

## Mid-flight escalation

When a worker hits unexpected complexity during execution — scope larger than triage estimated, side effects discovered, new cross-cutting concerns found — it returns an `ESCALATE` flag with a reason string. The orchestrator:

1. Pauses the current batch
2. Re-evaluates scope using the worker's discovery report
3. Selects the appropriate higher profile
4. Rewrites the task file to reflect the expanded scope
5. Continues from the escalation point (work already completed is not re-done)

See [escalation.md](escalation.md) for the full escalation protocol, flag format, and downgrade rules.

---

## Token accounting

Each profile has a soft budget. The orchestrator tracks cumulative token usage per agent role and prints a usage summary at the end of every task.

```text
── Hyperflow Usage ──────────────────────
Profile: deep (budget: 300k)
Thinking (Opus 4.8)   4 agents   80k
Worker   (Sonnet 4.6) 9 agents  220k
Total                13 agents  300k  · within budget
─────────────────────────────────────────
```

Budget thresholds by profile:

| Profile    | Soft budget     |
|------------|-----------------|
| fast       | ≤ 30 000        |
| standard   | ≤ 100 000       |
| deep       | 200 000–500 000 |
| research   | ≤ 80 000        |
| creative   | ≤ 150 000       |
| scientific | 200 000–400 000 |

If `Total > budget × 1.5` the orchestrator flags the overrun: `⚠ OVER BUDGET`. The flag is informational — it does not abort the task, but it is included in the usage summary so patterns of over-budget runs can be caught and the profile selection or task decomposition can be adjusted.

---

## Quick-reference summary

| Profile    | Brainstorm depth | Searchers | Workers    | Reviewers            | Budget          | Task file | TDD  |
|------------|------------------|-----------|------------|----------------------|-----------------|-----------|------|
| fast       | silent recap     | 0         | 1          | none (inline)        | ≤ 30k           | no        | no   |
| standard   | 1 question max   | 0–1       | 1–2        | 1 batch              | ≤ 100k          | yes       | no   |
| deep       | 2–3 questions    | 2–3       | 3–5+       | per-batch + final    | 200k–500k       | yes       | no   |
| research   | 1 question max   | 3+        | 0–1        | 0–1                  | ≤ 80k           | optional  | no   |
| creative   | full 6-dim       | 0–2       | 1–2        | 1 (visual + a11y)    | ≤ 150k          | yes       | no   |
| scientific | 2–3 questions    | 1–2       | 2–3        | L1–L5 multi-level    | 200k–400k       | yes       | yes  |

Key constraints at a glance:
- **fast:** inline review only; no task file; upgrade on any ESCALATE signal
- **standard:** task file mandatory; 1 batch review; upgrade when scope expands past 5 files
- **deep:** per-batch + integration review; sub-task commits; minimum 1 thinking agent always present
- **research:** no code committed unless prototype explicitly requested; synthesis by orchestrator
- **creative:** code gate — zero implementation until brainstorm approved
- **scientific:** test gate — zero implementation until test-writer completes; all tests must pass before commit

---

## Profile decision flowchart

Use this as a mental shortcut when triage output is ambiguous:

```text
Is the task type "scientific" or domain correctness-critical?
  YES → scientific

Does the task touch numerical, cryptographic, or financial logic?
  YES → scientific

Is the primary goal evaluation / exploration / audit (no code expected)?
  YES → research

Do the types include "ui" or "creative" AND is the design direction unclear?
  YES → creative

Is the scope cross-cutting, system-wide, or complexity=complex?
  YES → deep

Are types [security] present (even with simple scope)?
  YES → minimum standard (never fast)

Is complexity trivial AND scope single-file AND ambiguity < 0.3?
  YES → fast

Default → standard
```

The flowchart applies before composition rules. If multiple branches match, the strictest wins (scientific > deep > creative > research > standard > fast).
