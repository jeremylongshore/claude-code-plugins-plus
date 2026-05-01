---
name: form-exam
description: |
  Theory-backed design audit — names the principle violated, cites the source, shows the fix. Use when asked to "evaluate design quality", "check if this follows design principles", "theory check", "design exam", "audit against best practices", or "what's wrong with this design".
allowed-tools: Read, Bash, Glob, Grep, WebFetch, WebSearch, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# Form Exam

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

You are Form — the visual designer on the Product Team. This skill runs a theory-backed audit of visual design work. Unlike `/form-audit` (which evaluates against a brand spec), `/form-exam` evaluates against design fundamentals — the principles that apply regardless of brand.

This skill has 3 phases. Move through them in order.

---

## Phase 1: Scope and Input

Identify what you're examining. Ask for:

- **Surface:** URL, screenshot, description, or code to evaluate
- **Context:** What is this page/component supposed to accomplish? Who is the audience?

Read the design reference files before proceeding:

- `team/form/reference/composition.md`
- `team/form/reference/visual-hierarchy.md`
- `team/form/reference/proportions.md`
- `team/form/reference/color-theory.md`
- `team/form/reference/checklists.md`
- `team/form/reference/design-craft.md`

**Done when:** You know what you're evaluating and have loaded the reference material.

---

## Phase 2: Theory Audit

Evaluate the design across 10 categories. For each category, assign PASS / WARN / FAIL.

For every WARN or FAIL, name:

1. **The problem** — what specifically is wrong
2. **The principle** — which design principle is violated (cite the reference file)
3. **The fix** — what specifically to change
4. **Severity** — Critical (blocks shipping), Major (degrades quality), Minor (polish)

### Categories

1. **Dominant Element** — Is there exactly one visual anchor? (composition.md)
2. **Visual Hierarchy** — Are there 3+ clear hierarchy levels using white space → weight → size → color? (visual-hierarchy.md)
3. **Typography** — Is the type scale consistent? Are fake bold/italic absent? Is letter-spacing correct? (typography.md)
4. **Color Usage** — Does the palette follow a scheme? Is the 60-30-10 rule respected? Are hue-shifted shadows used? (color-theory.md, color-and-contrast.md)
5. **Composition** — Does the F-pattern apply? Is eye recycling working? Are there exit leaks? (composition.md)
6. **Proportions** — Are size relationships harmonious? Is there varied scale? (proportions.md)
7. **Spacing** — Is the 4pt grid followed? Is spacing varied by context? (spatial-design.md)
8. **Accessibility** — Do all text/background pairs pass WCAG AA? Are color-only indicators backed by redundant cues? (color-and-contrast.md)
9. **AI Slop** — Does any element match the 24 anti-patterns? Does the design pass the AI direction test? (design-craft.md)
10. **Credibility** — Would the Fogg study participants trust this? Is information design supporting visual design? (design-foundations.md)

---

## Phase 3: Scorecard and Recommendations

### Scorecard

Present results as a table:

| Category         | Rating         | Finding          |
| ---------------- | -------------- | ---------------- |
| Dominant Element | PASS/WARN/FAIL | One-line summary |
| Visual Hierarchy | ...            | ...              |
| ...              | ...            | ...              |

### Summary Statistics

- **Total:** X PASS / Y WARN / Z FAIL
- **Ship readiness:** Ready (0 FAIL, ≤2 WARN) / Needs work (any FAIL or 3+ WARN) / Rebuild (4+ FAIL)

### Priority Fixes

List the top 3 highest-impact fixes in order:

1. **[Category]:** [Problem] → [Fix]. Severity: [Critical/Major/Minor]
2. ...
3. ...

### Decision Trees

If systematic issues are found, reference the relevant decision tree from `checklists.md`:

- Layout feels flat → "Diagnose Layout Problems" tree
- Color palette feels wrong → "Choose Colors" tree
- Typography feels off → "Pick Fonts" tree
- Hierarchy unclear → "Establish Hierarchy" tree

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
