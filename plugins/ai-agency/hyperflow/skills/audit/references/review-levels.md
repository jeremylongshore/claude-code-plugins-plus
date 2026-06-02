# Multi-Level Review System

## Overview

After every worker completes, Opus runs a multi-level review. The number of levels scales with task complexity — Opus classifies complexity first, then dispatches a single reviewer covering all applicable levels in one pass.

---

## The 5 Levels

| Level | Name | What to check |
|-------|------|---------------|
| 1 | Requirements | Built what was asked? All sub-tasks done? Nothing missing or extra? Matches original spec? |
| 2 | Code Quality | Follows project conventions? Clean patterns? No duplication? Proper naming? Types correct? No `any`? Early returns? SRP? |
| 3 | Integration | Works with existing code? No broken imports? Existing tests still pass? Shared state intact? API contracts preserved? |
| 4 | Performance & Security | No N+1 queries? No unnecessary re-renders? Memoization where needed? No exposed secrets? Input validation at boundaries? No unsafe operations? |
| 5 | UX & Accessibility | Keyboard navigation works? Aria labels present? Responsive layout? Loading/error/empty states handled? RTL support? |

---

## Complexity Classification

**Simple** → levels 1–2 only
- Single file change, rename/move, config change, one-line fix, docs update

**Medium** → levels 1–3
- 2–3 files modified, modifies existing functionality, touches shared code (utils, hooks, services), extends existing components

**Complex** → levels 1–5
- 4+ files created/modified, new feature from scratch, multi-component work, UI with user interactions, database schema changes, API endpoint changes

Opus classifies before dispatching. Classification criteria:
- Number of files in scope
- New functionality vs modifying existing
- UI/UX involved → triggers Level 5
- Data persistence or external APIs involved → triggers Level 4

---

## Review Output Format

```
── Review ──────────────────────────────
L1 Requirements    pass     — [one-line summary]
L2 Code Quality    pass     — [one-line summary]
L3 Integration     pass     — [one-line summary]
L4 Performance     fail     — [specific issue found]
L5 UX/A11y         skipped  — not applicable
────────────────────────────────────────
VERDICT: APPROVED | NEEDS_FIX | SECURITY_VIOLATION
[If NEEDS_FIX: specific issues per level, each on its own line]
[Notes for future tasks if any]
```

Status words: `pass` (level passed) · `fail` (blocks approval) · `skipped` (not applicable). Plain words only — no `✓` / `✗` / `⊘`.

---

## Failure Handling

- Any level fails → `NEEDS_FIX` with specific issues listed per level
- Level 4 security sub-check fails → `SECURITY_VIOLATION` (halts pipeline, surfaces to user immediately)
- Worker receives fix instructions referencing the specific level that failed
- After fix, re-review only the failed levels — not all 5 again
- Max 3 fix attempts per level before escalating to user

---

## Level-Specific Checklists

**L1 — Requirements**
- [ ] All items from the task spec are implemented
- [ ] Nothing extra added beyond the spec
- [ ] Edge cases mentioned in the spec are handled
- [ ] Output makes sense for the original user request

**L2 — Code Quality**
- [ ] Follows naming conventions from project analysis
- [ ] No TypeScript `any` types
- [ ] No unnecessary comments or dead code
- [ ] Functions are focused (SRP)
- [ ] Uses existing utils/hooks instead of reinventing
- [ ] Proper error handling patterns

**L3 — Integration**
- [ ] Imports resolve correctly
- [ ] No circular dependencies introduced
- [ ] Shared state/context not broken
- [ ] API contracts match (types align between caller and callee)
- [ ] Existing tests would still pass

**L4 — Performance & Security**
- [ ] No N+1 database queries
- [ ] Expensive computations memoized
- [ ] No unnecessary re-renders (React.memo, useMemo, useCallback where needed)
- [ ] No hardcoded secrets or API keys
- [ ] Input validation at system boundaries
- [ ] No unsafe innerHTML or SQL injection vectors

**L5 — UX & Accessibility**
- [ ] Interactive elements have aria-labels
- [ ] Keyboard navigation works (tab order, enter/escape handlers)
- [ ] Loading states shown during async operations
- [ ] Error states handled gracefully
- [ ] Empty states have useful messaging
- [ ] Responsive — works on mobile viewport
- [ ] RTL layout considered (logical properties)
