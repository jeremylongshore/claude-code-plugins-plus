# Task Tracking

Persist active task state across sessions as individual files in `.hyperflow/tasks/`. One file per task. Created AFTER research, BEFORE implementation. Dynamic — updated throughout execution. Deleted on completion.

## Task File Format

```markdown
---
id: implement-user-auth
status: in-progress | blocked | in-review | completed
complexity: simple | medium | complex
created: 2026-05-15T14:30:00Z
updated: 2026-05-15T15:00:00Z
---

## Objective
[Clear statement of what this task achieves and why]

## Research Findings
[What was discovered during the research phase that informs this task]
- Existing auth context at `src/context/AuthContext.tsx` — extend, don't replace
- Project uses httpOnly cookies, not localStorage for tokens
- JWT library already installed: `jose` v5.2
- Related tests in `src/__tests__/auth/` use MSW for mocking

## Files in Scope
- `src/middleware/auth.ts` — creating (new middleware)
- `src/hooks/useAuth.ts` — modifying (add refresh logic)
- `src/types/auth.ts` — creating (JWT payload types)
- `src/context/AuthContext.tsx` — modifying (extend with new methods)

## Dependencies
- Depends on: [other task IDs if any]
- Blocks: [tasks waiting on this one]
- External: [APIs, services, or packages needed]

## Sub-tasks
- [x] Define JWT payload types in auth.ts
- [x] Create auth middleware with RS256 verification
- [ ] Add token refresh rotation logic
- [ ] Extend AuthContext with logout + refresh methods
- [ ] Wire middleware into route handlers
- [ ] Add integration tests

## Acceptance Criteria
- [ ] Middleware validates JWT with RS256
- [ ] Expired tokens trigger silent refresh
- [ ] Invalid tokens return 401 with proper error shape
- [ ] Tests cover valid/expired/malformed token scenarios

## Progress
- [2026-05-15 14:35] Created JWT types — used `jose` JWTPayload as base
- [2026-05-15 14:42] Auth middleware done — handles verify + decode + error mapping
- [2026-05-15 14:50] DISCOVERY: route handlers expect `req.user` not `req.auth` — updating

## Learnings
- Route handlers use `req.user` pattern (not `req.auth`) — checked 12 handlers
- Error responses must follow `{ code, message, details }` shape from shared ErrorResponse type
- Existing refresh endpoint at `/api/auth/refresh` — reuse, don't create new

## Blocked (only if status=blocked)
[What's blocking, why, and what needs to happen to unblock]
```

## Naming Convention

Pattern: `<verb>-<short-description>.md` in kebab-case.

- `implement-user-auth.md`
- `fix-login-redirect-loop.md`
- `refactor-extract-validation.md`
- `add-search-to-dashboard.md`
- `build-reuse-audit-tool.md`

## Lifecycle

```
User request
    |
[Opus] RESEARCH — dispatch searchers to explore code
    |
[Opus] PLAN — decompose based on research findings
    |
[Opus] CREATE task files (comprehensive, with research findings)
    |
[Opus] Dispatch workers
    |
[Opus] UPDATE task files dynamically:
    |   - Check off completed sub-tasks
    |   - Add new sub-tasks discovered during work
    |   - Remove sub-tasks that are unnecessary
    |   - Reorder based on new dependencies found
    |   - Append to Progress with timestamps
    |   - Add Learnings as discoveries happen
    |
[Opus] Review → APPROVED → DELETE task file
    |         → NEEDS_FIX → update task file, re-dispatch
```

## Dynamic Updates

Task files are living documents. Update them after EVERY batch:

**Add sub-tasks** when implementation reveals new work:
```diff
+ - [ ] Handle edge case: expired refresh token during concurrent requests
+ - [ ] Add rate limiting to refresh endpoint
```

**Remove sub-tasks** when research proves them unnecessary:
```diff
- - [ ] Create new refresh endpoint (existing one works)
```

**Change status** based on discoveries:
- `in-progress` → `blocked` if waiting on another task or external dependency
- `blocked` ��� `in-progress` when blocker resolves
- `in-progress` → `in-review` when all sub-tasks complete

**Add to Progress** with timestamps so context is preserved across sessions:
```
- [2026-05-15 15:10] PIVOT: switched from custom middleware to Next.js middleware pattern
```

## Session Resume

On session start, check `.hyperflow/tasks/` for existing files:

- If active tasks exist:
  - Read all task files
  - Present summary: "Found N incomplete tasks from previous session"
  - Show each task's objective + progress percentage (checked/total sub-tasks)
  - Ask: "Continue these tasks or start fresh?"
  - **Continue** → read Progress + Sub-tasks to determine exact next step
  - **Start fresh** → delete all task files

## Integration with Orchestrator (Layer 3)

1. **Research first** — always explore code before creating task files
2. **Comprehensive creation** — task files include research findings, file paths, dependencies, acceptance criteria
3. **One file per logical unit** — not per worker dispatch. A feature with 3 sub-components = 1 task file with 3 sub-task groups
4. **Feed into workers** — include task file's Research Findings and Learnings in worker prompts
5. **Dynamic maintenance** — update after every batch, not just at completion
6. **Delete only when done** — reviewer approves AND acceptance criteria met → delete

## Directory Structure

```
.hyperflow/
├── tasks/            # Active task tracking (auto-cleaned)
│   ├── implement-auth.md
│   ├── build-reuse-audit.md
│   └── fix-redirect.md
├── profile.md
├── architecture.md
├── conventions.md
├── dependencies.md
├── testing.md
├── git-workflow.md
└── .checksums
```

## Constraints

- Maximum 10 active task files — if more, decompose differently
- Task files are gitignored (`.hyperflow/` is already gitignored)
- Don't track trivial tasks (single-file renames, one-line fixes) — only tasks with 2+ sub-steps
- Reusable learnings feed into session-memory when they apply beyond this task
- Always include timestamps in Progress entries for cross-session clarity
