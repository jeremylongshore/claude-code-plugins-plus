# Batched Reviewer Prompt Template

Use this template when dispatching a single Opus reviewer to evaluate N sibling worker outputs in one call (Pattern P2 — batched single-pass review). Collapses N sequential reviewer round-trips into one without changing the tier mix or the review floor.

## When to Use vs. When to Fall Back

| Use batched review | Fall back to per-sub-task reviewers |
|---|---|
| All siblings share the same review-level cap (e.g., all L1–L3) | Sub-tasks carry different level caps (mixed flow profile) |
| Siblings were drafted from the same shared input (e.g., one chosen approach) | Sub-tasks depend on each other's outputs |
| Siblings are section-level or batch-level peers (spec §7, scope batch decomposition, dispatch batch) | One sibling has a security-sensitive surface the others don't — review it alone at L4 |
| Parallel Writers completed in the same wave | A prior batch's learnings must be incorporated before reviewing the next |

## Complexity Classification

Same scale as per-sub-task review — but applied to the batch as a whole. The review-level cap for the batch is the highest cap among all siblings. If any sibling is Complex, run L1–L5 for all.

- **Simple** (levels 1-2): All siblings are single-file or config changes
- **Medium** (levels 1-3): Any sibling modifies existing shared functionality
- **Complex** (levels 1-5): Any sibling introduces a new feature, touches UI, or changes DB/API contracts

## Honor the Level Cap

Apply ONLY the levels specified in the dispatch's review-level cap (e.g., `L1-L2` means run L1 and L2; do NOT silently escalate to L3 unless the cap says so). The cap is set by upstream triage via the dispatch flow profile and the triage `security`/`integration_risk` flags. Workers cannot request escalation; only triage classification can elevate the cap.

If you encounter something that would warrant escalation beyond the cap — for example, spotting a security concern during an L1-L2 review — surface it as an `[Important]` note in the relevant sibling's finding block for the orchestrator to consider, but do not fail the verdict on it. The orchestrator decides whether to re-dispatch at a higher cap or surface the concern to the user.

## Template

```
## Batched review scope
Siblings: [N sections or sub-tasks being reviewed]
Shared input: [the common spec, chosen approach, or task file they all derive from]
Review-level cap: L[n] — [classification rationale]

## Sibling outputs
### §1 <name>
[Paste §1 worker's summary and changed files]

### §2 <name>
[Paste §2 worker's summary and changed files]

... (repeat for each sibling)

## Level 1: Requirements (all siblings)
For each sibling:
- Does the output match its assigned spec exactly?
- All sub-tasks completed? Nothing missing or extra?

## Level 2: Code Quality (all siblings)
For each sibling:
- Follows project naming conventions?
- No TypeScript `any`, no dead code?
- Uses existing utils/hooks (not reinventing)?
- Proper error handling, SRP, early returns?

## Level 3: Integration — cross-section + per-sibling (medium + complex only)
Per-sibling:
- Imports resolve? No circular dependencies?
- API contracts preserved? Existing tests would still pass?

Cross-section (only possible in batched review):
- Do sibling outputs contradict each other? (e.g., §1 proposes interface A, §3 consumes interface B)
- Shared state or context types consistent across all siblings?
- No duplicated logic introduced independently by two siblings?
- If a sibling depends on another's output landing first, flag the ordering constraint.

## Level 4: Performance & Security (complex only)
For each sibling:
- No N+1 queries? Expensive ops memoized?
- No unnecessary re-renders?
- No hardcoded secrets (sk-*, AKIA*, ghp_*, private keys)?
- Input validation at boundaries? No injection vectors?

## Level 5: UX & Accessibility (complex UI tasks only)
For each sibling:
- Aria labels on interactive elements?
- Keyboard navigation works?
- Loading/error/empty states handled?
- Responsive + RTL considered?

## Security Review (always — per sibling)
- Were any blocked files accessed? (.env, *.pem, *.key, ~/.ssh/*)
- Any dangerous commands? (rm -rf, force push, sudo)
- Any data exfiltration? (contents piped to external URLs)

## Token economy (DOCTRINE rule 16)
Return ONLY the Output format block below — no preamble, no restating of sibling outputs or shared input, no narration of the review process, no postamble summary. One verdict per sibling; one short feedback line per NEEDS_FIX. Cross-section notes stay to one line each. Stop after the global verdict.

## Output format
── Batched Review ──────────────────────
§1 <name>:  PASS
§2 <name>:  NEEDS_FIX — [specific feedback for §2]
§3 <name>:  PASS
§4 <name>:  PASS  (cross-section: depends on §2 fix landing first)
§5 <name>:  SECURITY_VIOLATION — [finding]
────────────────────────────────────────
GLOBAL VERDICT: NEEDS_FIX
[Consolidated re-dispatch instructions: list only the siblings that need a Worker re-run]
[Cross-section notes that survive into the next review pass]
[Notes for future tasks]
```

## Verdict Rules

| Condition | Global verdict |
|---|---|
| All siblings PASS | APPROVED |
| Any sibling NEEDS_FIX | NEEDS_FIX |
| Any sibling SECURITY_VIOLATION | SECURITY_VIOLATION — chain halts immediately |

A single `SECURITY_VIOLATION` in any sibling stops the entire batch. The orchestrator does not re-dispatch failed siblings — it escalates to the user.

On `NEEDS_FIX`: the orchestrator re-dispatches only the failed siblings (not all N). The passing siblings' outputs are accepted as-is. A single Opus re-review of just the fixed siblings follows (not another full batched pass unless the fix affects shared interfaces).

## Dispatch Example

Five design sections (Architecture, Data flow, Key decisions, Edge cases, File structure) reviewed at L1–L3 in one call after parallel Writers complete:

```
Agent({
  description: "Batched review — 5 spec design sections (medium, L1–L3)",
  model: "opus",
  prompt: `## Batched review scope
Siblings: §1 Architecture, §2 Data flow, §3 Key decisions, §4 Edge cases, §5 File structure
Shared input: Chosen approach — "Event-sourced task store with Redis fan-out"
Review-level cap: L3 (Medium — modifies shared task state model)

## Sibling outputs
### §1 Architecture
Files reviewed: docs/spec/architecture.md
Summary: Proposed layered architecture — API gateway → task engine → event store.
Introduces TaskEngine interface; Redis adapter is pluggable.

### §2 Data flow
Files reviewed: docs/spec/data-flow.md
Summary: Documented the write path (create → event → fan-out) and read path (subscribe → materialize).
Uses TaskEngineEvent type from §1.

### §3 Key decisions
Files reviewed: docs/spec/decisions.md
Summary: Captured 4 ADRs: Redis over Kafka (latency), event sourcing over CRUD (auditability),
TypeScript over Python (existing stack), polling fallback for SSE-unsupported clients.

### §4 Edge cases
Files reviewed: docs/spec/edge-cases.md
Summary: Covers fan-out lag under load, event replay on reconnect, partial write failures,
and consumer back-pressure. References Redis adapter from §1.

### §5 File structure
Files reviewed: docs/spec/file-structure.md
Summary: Proposed src/task-engine/, src/adapters/redis/, src/types/task-event.ts.
Matches the TaskEngine interface name from §1.

## Level 1: Requirements
- Each section covers its assigned design dimension?
- No section drifts into another's scope?

## Level 2: Code Quality
- Naming consistent across sections? Types referenced by the correct names?
- No dead concepts introduced then never used?

## Level 3: Integration (cross-section focus)
- §2 data flow references types defined in §1 — are they consistent?
- §4 edge cases reference the Redis adapter from §1 — does the adapter contract hold?
- §5 file structure — does the proposed layout accommodate every component named in §1–§4?
- Any contradictions between ADRs in §3 and the design in §1 or §2?

## Security Review
- Blocked files accessed? Dangerous commands? Data exfiltration?

## Output format
── Batched Review ──
§1–§5 per-section verdict + GLOBAL VERDICT`
})
```

See [reviewer-prompt.md](reviewer-prompt.md) for the per-sub-task variant and [review-levels.md](review-levels.md) for full checklist details.
