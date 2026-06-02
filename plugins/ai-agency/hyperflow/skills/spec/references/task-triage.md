# Task triage (Layer 0.5)

## Purpose

Triage is invoked once per user request — before research, before brainstorming, before any worker dispatch. A single cheap thinking-model call classifies the task and emits a JSON object that drives every downstream decision: which flow profile to use, how deep to brainstorm, which persona templates to compose into worker prompts, how many workers and batches to expect, and what token budget to allocate. Every layer that follows reads from this JSON rather than re-deriving intent independently.

## When to invoke

Invoke on every user request that introduces new work — "build X", "fix Y", "research Z", "refactor W". Skip only when the orchestrator is already mid-flow (e.g., responding to a follow-up question about an in-progress task, clarifying an AskUserQuestion answer, or the request is a pure meta-command like `hyperflow: memory show`).

## Triage prompt template

Send verbatim to the thinking model. Budget: 2k tokens. Do not add prose around it.

```text
You are a task classifier for a multi-agent orchestrator. Analyze the request below and return STRICT JSON ONLY — no prose, no markdown, no code fences.

### User request
{{USER_REQUEST}}

### Project context (optional, ≤200 tokens from .hyperflow/profile.md)
{{PROJECT_CONTEXT_SNIPPET}}

### Output schema
{
  "types": string[],          // 1+ from: architect, frontend, ui, api, db, security, scientific, creative, refactor, bugfix, devops, docs, test, research, performance
  "complexity": string,       // trivial | simple | moderate | complex | research
  "risk": string,             // reversible | irreversible
  "scope": string,            // single-file | multi-file | cross-cutting | system-wide
  "ambiguity": number,        // 0.0–1.0
  "brainstormDepth": string,  // silent | light | standard | deep
  "flow": string,             // fast | standard | deep | research | creative | scientific
  "personas": string[],       // subset of types — persona template names to compose
  "estimatedWorkers": number,
  "estimatedBatches": number,
  "budget": number,           // token budget integer
  "rationale": string         // one sentence
}

Return only valid JSON. No explanation before or after.
```

## Output schema (JSON)

```json
{
  "types": ["frontend", "api"],
  "complexity": "moderate",
  "risk": "reversible",
  "scope": "multi-file",
  "ambiguity": 0.35,
  "brainstormDepth": "light",
  "flow": "standard",
  "personas": ["frontend", "api"],
  "estimatedWorkers": 2,
  "estimatedBatches": 1,
  "budget": 100000,
  "rationale": "Two-layer feature touching UI and a new REST endpoint with moderate design choices."
}
```

## Field definitions

| Field | Type | Description |
|-------|------|-------------|
| `types` | `string[]` | Multi-select classification. Always an array, even for single-type tasks. See valid values below. |
| `complexity` | `string` | Effort tier — `trivial`, `simple`, `moderate`, `complex`, or `research`. |
| `risk` | `string` | `irreversible` if the task touches prod databases, external API keys, payment systems, public deployments, force pushes, schema migrations that drop data, or package publishes. Otherwise `reversible`. |
| `scope` | `string` | File blast radius — `single-file`, `multi-file`, `cross-cutting`, or `system-wide`. |
| `ambiguity` | `number` | 0.0 if user gave a complete spec; 0.2 if minor unknowns; 0.5 if approach is open; 0.8 if "what should we build" territory. |
| `brainstormDepth` | `string` | Derived from `ambiguity` (see derivation table below). |
| `flow` | `string` | Execution profile for Layer 3. Determined by the mapping rules below. |
| `personas` | `string[]` | Subset of `types`. Names of persona template files (no path, no extension) to compose into worker prompts. |
| `estimatedWorkers` | `number` | Expected total parallel worker count across all batches. |
| `estimatedBatches` | `number` | Expected number of dispatch batches. |
| `budget` | `number` | Soft token budget for the full task. Used in usage summary to flag overruns. |
| `rationale` | `string` | One sentence echoed back to the user in the orchestrator's opening line. |

### Complexity tiers

| Value | Definition |
|-------|-----------|
| `trivial` | 1–5 line edit, single concept, obvious solution |
| `simple` | One file, well-understood pattern, no significant design needed |
| `moderate` | 2–4 files, some design choices, patterns exist but must be adapted |
| `complex` | 5+ files, multiple subsystems, non-trivial design decisions |
| `research` | Unknown territory — evaluation or investigation required before implementation |

### `brainstormDepth` derivation

| `ambiguity` range | `brainstormDepth` | Behavior |
|-------------------|-------------------|---------|
| 0.0–0.2 | `silent` | Recap intent in one sentence; no questions |
| 0.2–0.5 | `light` | Ask at most one AskUserQuestion if genuinely needed |
| 0.5–0.8 | `standard` | 2–3 clarifying questions |
| 0.8–1.0 | `deep` | Full 6-dimension exploration (see brainstorming-advanced.md) |

### `flow` mapping rules

Apply the FIRST rule that matches:

1. `complexity=trivial` AND `scope=single-file` AND `risk=reversible` AND `ambiguity<0.3` → **`fast`**
2. `types` includes `scientific` OR (`risk=irreversible` AND numerical correctness matters) → **`scientific`**
3. `complexity=research` → **`research`**
4. `types` includes `ui` OR `creative` AND `complexity≥moderate` → **`creative`**
5. `complexity=complex` OR `scope` in `[cross-cutting, system-wide]` → **`deep`**
6. `complexity` in `[simple, moderate]` AND `scope` in `[single-file, multi-file]` → **`standard`**

### Budget defaults by flow

| Flow | Budget |
|------|--------|
| `fast` | 30000 |
| `standard` | 100000 |
| `deep` | 300000 |
| `research` | 80000 |
| `creative` | 150000 |
| `scientific` | 300000 |

Source of truth: `flow-profiles.md` — these values must match.

### Worker/batch defaults by flow

| Flow | `estimatedWorkers` | `estimatedBatches` |
|------|--------------------|--------------------|
| `fast` | 1 | 1 |
| `standard` | 1–2 | 1 |
| `deep` | 3–5 | 2–3 |
| `research` | 2–3 | 2 |
| `creative` | 2 | 2 |
| `scientific` | 2–3 | 2–3 |

## Multi-type rules

Tasks frequently span 2–4 types. Common compositions:

| Request pattern | `types` |
|-----------------|---------|
| User authentication | `[api, db, security]` |
| Dashboard page with API data | `[frontend, ui, api]` |
| Flaky test | `[bugfix, test]` |
| Slow query | `[db, performance]` |
| Refactor auth module | `[refactor, security]` |
| Design system spec doc | `[architect, docs]` |
| CI for tests | `[devops, test]` |
| ML pipeline | `[scientific, devops]` |

When multiple types are present:

1. **Worker prompts** compose ALL their persona templates. Persona stitching priority follows the canonical order defined in `personas-A.md` (positions 1–8) and extended by `personas-B.md` (positions 9–15). When triage outputs `personas: [...]`, the orchestrator stitches them into the worker prompt in priority order — the higher-priority persona's guidance shapes earlier sections and wins on conflict. See `personas-A.md` "Persona priority" table for the authoritative ordering.
2. **Reviewer** validates against ALL persona standards simultaneously.
3. **Flow profile** is the STRICTEST implied by any single type. Example: if any type implies `deep`, the flow is `deep` even if other types alone would yield `standard`. If `security` is present, flow is never `fast`.
4. **`personas`** equals `types` unless a type has no persona template file — omit those.

## Examples

### Example 1 — rename a function

**Request:** "Rename function `getUser` to `fetchUser` in `auth.ts`"

```json
{
  "types": ["refactor"],
  "complexity": "trivial",
  "risk": "reversible",
  "scope": "single-file",
  "ambiguity": 0.0,
  "brainstormDepth": "silent",
  "flow": "fast",
  "personas": ["refactor"],
  "estimatedWorkers": 1,
  "estimatedBatches": 1,
  "budget": 30000,
  "rationale": "Trivial single-file rename with zero ambiguity — fast path."
}
```

### Example 2 — dark mode toggle

**Request:** "Add a dark mode toggle to settings page"

```json
{
  "types": ["frontend", "ui"],
  "complexity": "simple",
  "risk": "reversible",
  "scope": "multi-file",
  "ambiguity": 0.25,
  "brainstormDepth": "light",
  "flow": "creative",
  "personas": ["frontend", "ui"],
  "estimatedWorkers": 2,
  "estimatedBatches": 2,
  "budget": 150000,
  "rationale": "UI feature with minor ambiguity around persistence strategy — creative flow with a light clarification pass."
}
```

### Example 3 — full auth system
**Request:** "Implement user authentication with email + password, JWT sessions, and password reset"

```json
{
  "types": ["api", "db", "security"],
  "complexity": "complex",
  "risk": "irreversible",
  "scope": "cross-cutting",
  "ambiguity": 0.45,
  "brainstormDepth": "light",
  "flow": "deep",
  "personas": ["api", "db", "security"],
  "estimatedWorkers": 4,
  "estimatedBatches": 3,
  "budget": 300000,
  "rationale": "Multi-subsystem auth feature touching DB schema, JWT issuing, and password handling — deep flow required."
}
```

### Example 4 — CI failure investigation
**Request:** "Why is the build failing on CI? Started yesterday."

```json
{
  "types": ["bugfix", "devops"],
  "complexity": "research",
  "risk": "reversible",
  "scope": "multi-file",
  "ambiguity": 0.6,
  "brainstormDepth": "standard",
  "flow": "research",
  "personas": ["bugfix", "devops"],
  "estimatedWorkers": 2,
  "estimatedBatches": 2,
  "budget": 80000,
  "rationale": "Unknown root cause in CI — research flow to investigate before patching."
}
```

### Example 5 — database technology decision

**Request:** "Should we use Postgres or DynamoDB for the new orders table?"

```json
{
  "types": ["architect", "db", "research"],
  "complexity": "research",
  "risk": "irreversible",
  "scope": "system-wide",
  "ambiguity": 0.75,
  "brainstormDepth": "standard",
  "flow": "research",
  "personas": ["architect", "db"],
  "estimatedWorkers": 2,
  "estimatedBatches": 2,
  "budget": 80000,
  "rationale": "Architectural decision with long-term irreversible implications — research flow with structured trade-off analysis."
}
```

### Example 6 — creative landing page

**Request:** "Generate a creative landing page for a developer tool"

```json
{
  "types": ["frontend", "ui", "creative"],
  "complexity": "moderate",
  "risk": "reversible",
  "scope": "multi-file",
  "ambiguity": 0.55,
  "brainstormDepth": "standard",
  "flow": "creative",
  "personas": ["frontend", "ui", "creative"],
  "estimatedWorkers": 2,
  "estimatedBatches": 2,
  "budget": 150000,
  "rationale": "Open-ended creative UI task — creative flow with standard brainstorm to align on aesthetic direction first."
}
```

## Fallback rules

If the triage model returns malformed output (invalid JSON, missing required fields, invalid enum values):

1. **Retry once** — resend the same prompt with this suffix appended:
   ```text
   STRICT JSON ONLY. No prose. No markdown fences. Required fields: types, complexity, risk, scope, ambiguity, brainstormDepth, flow, personas, estimatedWorkers, estimatedBatches, budget, rationale.
   ```
2. **If still malformed** — fall back to the safe default below and proceed:
   ```json
   {
     "types": ["general"],
     "complexity": "moderate",
     "risk": "reversible",
     "scope": "multi-file",
     "ambiguity": 0.5,
     "brainstormDepth": "light",
     "flow": "standard",
     "personas": [],
     "estimatedWorkers": 1,
     "estimatedBatches": 1,
     "budget": 100000,
     "rationale": "Triage fallback — classification unavailable, proceeding with standard defaults."
   }
   ```
3. **Surface the issue** — print a single warning line before continuing:
   ```
   ⚠ Triage malformed (attempt 2/2) — falling back to standard defaults.
   ```

Never block the pipeline over a failed triage. Proceed with fallback values.

## Token budget

Target: **2 000 tokens** for the triage call itself.

- Input: ~1 000 tokens (request ≤500 + context ≤200 + template ~300).
- Output: ~150–200 tokens (the JSON object).
- Thinking budget: ~800 tokens internal.
- Total: well within 2k. Do not increase.

If the project context snippet would push input above 700 tokens, truncate it to the first 100 tokens.
