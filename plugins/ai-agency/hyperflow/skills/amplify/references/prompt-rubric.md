# Prompt-Quality Rubric

The scorecard the Reviewer applies in Step 2. Eight dimensions, each scored 1–5. The rubric gate passes only when **every dimension ≥ 4**. Any dimension below 4 returns targeted revisions; the Writer revises once, then the best version ships regardless (no infinite loop — see `failure-recovery.md` NEEDS_REVISION rule).

| # | Dimension | Scores 5 when… | Scores 1 when… |
|---|-----------|----------------|----------------|
| 1 | **Intent clarity** | The goal is unambiguous in one read; a stranger would know exactly what success is | The ask is vague ("make it better"), multiple readings possible |
| 2 | **Context sufficiency** | Enough background, inputs, and current-state given that the executor never has to guess | Key context missing; executor must invent assumptions |
| 3 | **Scope boundaries** | What's in and explicitly out of scope is stated | No boundaries — scope creep inevitable |
| 4 | **Structure** | Role · task · constraints · output spec · success criteria are all present and ordered | Wall of text, no structure |
| 5 | **Domain doctrine** | The matching domain's mandatory standards are injected as constraints (see below) | Generic; ignores the domain's quality bar |
| 6 | **Output specification** | The deliverable's format, shape, and acceptance criteria are defined | "Just do it" — no definition of done |
| 7 | **Guardrails** | Edge cases, anti-goals ("do NOT…"), and security/quality constraints are explicit | No guardrails; foot-guns wide open |
| 8 | **Economy** | Concise — every line earns its place; no filler, no hedging (intentional minimalism) | Padded, repetitive, hedged |

## Domain doctrine injection (dimension 5)

Step 1 detects the prompt's domain and selects the matching hyperflow persona(s) (`personas-A.md` / `personas-B.md`). The enhanced prompt must carry that persona's **mandatory** standards as explicit constraints. Representative standards per domain:

| Domain | Mandatory constraints to inject |
|--------|--------------------------------|
| `frontend` / `ui` / `creative` | Domain-folder architecture · zero static strings (i18n keys / named constants) · RTL + Intl localization · responsive breakpoints · `data-testid` on interactive elements · no generic AI aesthetics · use existing component library, never rebuild primitives |
| `api` / `db` (backend) | Layered architecture (thin routes → services → repositories) · Zod validation as single source of truth · typed domain errors, never leak internals · structured logging with request IDs · transaction + connection-pool correctness · integration tests against a real DB |
| `mobile` (react-native) | Domain folders · zero static strings · RTL via I18nManager · responsive via useWindowDimensions · `testID` on interactive elements · 60fps UI-thread animation · strict TS, no `any` |
| `security` | Threat model first · input validation · least privilege · no secrets in code · injection/XSS/CSRF guards |
| `performance` | Measure before optimize · name the metric + budget · avoid premature abstraction |
| `refactor` / `bugfix` / `test` | Root cause not symptom · characterization tests before change · no behavior change unless asked |
| Any | No `any` (use `unknown` / `z.infer` / typed) · conventional-commit-ready · early returns over deep nesting · single responsibility · reuse before rebuild |

## Project-rule overlay

After the persona standards, Step 1 reads — when present — `CLAUDE.md`, `AGENTS.md`, and `.hyperflow/memory/*` (especially `conventions.md`, `project-decisions.md`, `anti-patterns.md`). Any project-specific rule found there is layered on top of the persona standards and injected into the enhanced prompt as a constraint. Project rules win on conflict — they are the user's explicit instructions.

## What the enhanced prompt looks like

The single best output follows this skeleton (adapt section presence to the task — economy still applies):

```
<role / expertise framing — one line>

<task — the precise goal, unambiguous>

Context:
- <relevant background, current state, inputs>

Constraints:
- <domain doctrine standards as bullet constraints>
- <project rules from CLAUDE.md / memory>

Output:
- <deliverable format + acceptance criteria>

Out of scope:
- <explicit anti-goals>
```

Not every prompt needs every section — a one-line lookup shouldn't be inflated into a spec. Dimension 8 (economy) is the counterweight to dimensions 1–7: enhance to the level the task warrants, never more.
