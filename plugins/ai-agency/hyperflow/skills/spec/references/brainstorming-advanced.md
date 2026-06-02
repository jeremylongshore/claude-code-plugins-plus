# Advanced Brainstorming Framework

Extends Layer 4 with structured question clarification, multi-dimensional analysis, and AskUserQuestion UI integration. Use this as the reference for how Opus runs the brainstorming flow.

---

## Phase 1: Multi-Dimensional Analysis (silent)

Before asking the user anything, score these 6 dimensions internally. Do not show this to the user.

| Dimension | What to evaluate | Example unknown |
|-----------|-----------------|-----------------|
| Technical | Stack fit, API design, data model | "Does this need a new DB table or extend existing?" |
| UX | User flow, interaction patterns, accessibility | "Is this a modal or a full page?" |
| Performance | Load impact, caching needs, bundle size | "Will this load data eagerly or lazily?" |
| Security | Auth boundaries, data exposure, input validation | "Should this be behind auth?" |
| Scalability | Growth patterns, multi-tenant, data volume | "Will this handle 10 or 10K items?" |
| Maintainability | Testing strategy, code ownership, extensibility | "Who maintains this long-term?" |

**Score each:** `clear` (no unknowns) / `uncertain` (some unknowns) / `blind` (critical unknowns)

Only ask questions for `uncertain` and `blind` dimensions. `blind` gets priority.

**Dimension → technique mapping:**

| Score + Dimension | Technique to apply |
|-------------------|--------------------|
| blind Technical | Constraint Discovery |
| blind UX | Intent Clarification |
| uncertain Security | Assumption Challenging |
| Multiple blind | Scope Boundaries first to narrow |

---

## Phase 2: Smart Question Sequence

Four techniques, applied based on blind spot analysis. Max 4–5 questions total — not 4 per technique.

**1. Intent Clarification** — What problem does this actually solve?

Goes beyond the literal request to surface the underlying goal. User says "add a sidebar" → real intent might be "improve navigation for power users."

Use `AskUserQuestion` with 2–3 options showing different interpretations of the real goal.

**2. Constraint Discovery** — What limits exist that weren't mentioned?

Surfaces technical, timeline, and compatibility constraints. Check: existing tech stack, backward compatibility, performance budgets, target platforms. Skip constraints discoverable from the codebase — find those through context exploration.

**3. Assumption Challenging** — What are we both assuming that might be wrong?

After gathering initial requirements, identify 2–3 implicit assumptions and validate them explicitly. Example: "I'm assuming this needs to work offline — is that correct?" Use confirm/deny options with a preview of what changes per assumption.

**4. Scope Boundaries** — What is explicitly NOT part of this?

Prevents scope creep. Present likely adjacent features and confirm they're out of scope. Example: "Should this include [feature A] or [feature B], or just the core [X]?"

**Rules:**
- Skip any technique where the answer is already obvious from context
- Each question MUST use `AskUserQuestion` — never plain text questions
- Skip questions with a single obvious answer

---

## Phase 3: Requirement Synthesis

After the question sequence, present this summary and get confirmation before proposing approaches:

```
## Discovered Requirements
- **Goal:** [one sentence]
- **Constraints:** [list]
- **Confirmed assumptions:** [list]
- **Out of scope:** [list]
- **Key unknowns resolved:** [list]
```

User confirms → move to approach proposals.

---

## AskUserQuestion Patterns

All brainstorming questions MUST use the `AskUserQuestion` tool. Never ask in plain text.

**Standard clarification** — multiple choice with descriptions:

```
AskUserQuestion({
  questions: [{
    question: "What's the primary goal of this feature?",
    header: "Intent",
    options: [
      { label: "Option A", description: "..." },
      { label: "Option B", description: "..." }
    ],
    multiSelect: false
  }]
})
```

**Architecture/layout comparisons** — use `preview` for side-by-side ASCII mockups:

```
AskUserQuestion({
  questions: [{
    question: "Which layout approach?",
    header: "Layout",
    options: [
      {
        label: "Sidebar",
        description: "Persistent nav panel on the left",
        preview: "┌──────┬────────┐\n│ Nav  │Content │\n│      │        │\n└──────┴────────┘"
      },
      {
        label: "Top nav",
        description: "Horizontal bar above content",
        preview: "┌────────────────┐\n│   Navigation   │\n├────────────────┤\n│    Content     │\n└────────────────┘"
      }
    ]
  }]
})
```

**Scope boundaries** — use `multiSelect: true` when excluding features:

```
AskUserQuestion({
  questions: [{
    question: "Which of these are OUT of scope for now?",
    header: "Scope",
    options: [...],
    multiSelect: true
  }]
})
```

**Rules:**
- Never ask more than 2 questions per `AskUserQuestion` call
- Use `preview` only for visual/structural comparisons — not text-only choices
- Always include `description` on every option
- `header` should be 1–2 words matching the technique: Intent / Constraint / Assumption / Scope

---

## Full Flow

```
User shares idea
    |
[Opus] Explore context — check files, docs, recent commits
    |
[Opus] Multi-Dimensional Analysis (silent)
    |   Score 6 dimensions: clear / uncertain / blind
    |   Map blind spots to question techniques
    |
[Opus] Smart Question Sequence (via AskUserQuestion)
    |   1. Intent Clarification    (if UX/goal is blind)
    |   2. Constraint Discovery    (if Technical is blind)
    |   3. Assumption Challenging  (if uncertain dimensions exist)
    |   4. Scope Boundaries        (if multiple blind dimensions)
    |   Max 4-5 questions total. Skip obvious ones.
    |
[Opus] Requirement Synthesis
    |   Present structured summary — user confirms before proceeding
    |
[Opus] Propose 2-3 approaches with trade-offs + recommendation
    |
[User] Picks approach
    |
[Opus] Present design in sections, get approval per section
    |
[User] Approves full design
    |
[Opus] Transition to Layer 3 (orchestrator) for implementation
```
