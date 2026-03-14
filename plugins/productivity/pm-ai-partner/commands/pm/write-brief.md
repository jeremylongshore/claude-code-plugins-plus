---
name: write-brief
description: Guide the user through creating a clear, actionable product brief
allowed-tools: Read, Write, Edit, Glob
---

Help me write a product brief for: $ARGUMENTS

## Instructions

Guide me through creating a clear, actionable product brief that engineering can use to scope and build. Follow this process:

1. **Gather context** — Ask me clarifying questions about the problem, users, constraints, and goals. Don't start writing until you understand the situation.
2. **Propose structure** — Show me an outline before drafting.
3. **Draft** — Write the full brief.
4. **Review** — Highlight gaps and suggest improvements.

## Brief Structure

```markdown
# [Feature Name]

## Problem Statement
What problem are we solving? Who has this problem? Why now?

## Proposed Solution
What are we building? (High-level — leave "how" to engineering)

## User Value
Why will users care? What's the measurable benefit?

## Success Metrics
| Metric | Current | Target |
|--------|---------|--------|

## Scope
### In Scope (v1)
### Out of Scope (and why)

## Open Questions
- Things to resolve before/during implementation

## Dependencies
- Other teams, systems, or work this depends on

## Timeline
- Target dates or "TBD pending scoping"
```

## Quality Checklist

Before finalizing, verify:
- [ ] Problem is specific (not "improve engagement")
- [ ] Solution describes "what" not "how"
- [ ] Metrics are measurable with current instrumentation
- [ ] Scope has explicit exclusions
- [ ] Open questions are honest about unknowns
- [ ] A senior engineer could read this and start scoping

Save the brief to `sandbox/planning/` as a draft. When ready to share, move to `product-catalog/planning/`.
