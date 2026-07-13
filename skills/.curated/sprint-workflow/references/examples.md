# Examples

## Example 1: Full Sprint Lifecycle for a CRUD API

A complete sprint building a user management API with CRUD endpoints, database
integration, and automated testing.

**Step 1 — Create the sprint and write specs:**

```bash
/sprint:new
# Creates .claude/sprint/1/specs.md
```

**Step 2 — Edit specs.md:**

```markdown
# Sprint 1: User Management API

## Goal
Build a REST API for user management with CRUD operations and role-based access.

## Scope
### In Scope
- POST /api/users (create user with email validation)
- GET /api/users/:id (retrieve user profile)
- PATCH /api/users/:id (update user fields)
- DELETE /api/users/:id (soft delete with archived flag)
- GET /api/users (list users with pagination and role filter)
- PostgreSQL schema with users table
- JWT authentication middleware

### Out of Scope
- Password reset flow
- OAuth providers
- Email notifications
- Admin dashboard UI

## Testing
- QA: required
- UI Testing: skip
- UI Testing Mode: automated
```

**Step 3 — Execute the sprint:**

```bash
/sprint
```

**Phase 0 — Load Specifications:**

```
Orchestrator reads .claude/sprint/1/specs.md
  → Goal: User Management API (5 endpoints)
  → Testing: QA required, UI testing skipped
  → No status.md found (fresh sprint)
  → Project type detected: Python + FastAPI
```

**Phase 1 — Architectural Planning:**

```
project-architect reads:
  → .claude/project-map.md (existing codebase structure)
  → .claude/project-goals.md (business objectives)

Architect produces:
  → .claude/sprint/1/api-contract.md (endpoint schemas, TypeScript interfaces)
  → .claude/sprint/1/backend-specs.md (implementation tasks per endpoint)

Architect returns SPAWN REQUEST blocks:
  SPAWN REQUEST
  Agent: python-dev
  Specs: .claude/sprint/1/backend-specs.md
  Contract: .claude/sprint/1/api-contract.md
  Scope: All user management endpoints
```

**Phase 2 — Implementation (Iteration 1):**

```
python-dev agent:
  → Reads backend-specs.md and api-contract.md
  → Creates src/models/user.py (SQLAlchemy model)
  → Creates src/routes/users.py (5 endpoints)
  → Creates src/middleware/auth.py (JWT validation)
  → Creates tests/test_users.py (15 test cases)

AGENT REPORT
Agent: python-dev
Status: COMPLETE
Files Modified: src/models/user.py, src/routes/users.py, src/middleware/auth.py, tests/test_users.py
Tests: 15 added
Conformity: All 5 endpoints implemented per contract
```

**Phase 3 — Testing (Iteration 1):**

```
qa-test-agent runs:
  → pytest tests/test_users.py
  → 13 passed, 2 failed
  → Failures:
    1. PATCH /api/users/:id returns 500 when email already exists (expected 409)
    2. GET /api/users pagination returns wrong total count with filters

QA REPORT
Tests: 13 passed, 2 failed
Coverage: 87%
Failures:
  - test_update_duplicate_email: Expected 409, got 500
  - test_list_users_filtered_pagination: total=50, expected=12
```

**Phase 4 — Review (Iteration 1):**

```
Architect reviews QA report:
  → 2 failures identified
  → Updates backend-specs.md:
    - Remove completed endpoints (POST, GET/:id, DELETE)
    - Add fix: PATCH must return 409 on duplicate email
    - Add fix: GET list pagination must count after filter
  → Updates status.md: "Iteration 1: 3/5 endpoints passing. 2 fixes needed."
  → Decision: ITERATE (spawn python-dev with narrowed specs)
```

**Iteration 2 — Fix and Re-test:**

```
python-dev agent:
  → Reads narrowed backend-specs.md (only 2 fixes)
  → Fixes duplicate email check in PATCH handler
  → Fixes filtered count query in list endpoint
  → Updates tests

qa-test-agent runs:
  → 15 passed, 0 failed
  → Coverage: 91%

Architect reviews:
  → All specs satisfied
  → Decision: FINALIZE
```

**Phase 5 — Finalization:**

```
Orchestrator writes final status.md:
  Sprint 1: COMPLETE
  Iterations: 2
  Endpoints: 5/5 passing
  Tests: 15 passing, 91% coverage
  Files: 4 created, 0 removed

FINALIZE
```

## Example 2: Resuming a Paused Sprint

A sprint that hit the 5-iteration limit and requires manual intervention.

**status.md after 5 iterations:**

```markdown
# Sprint 2 Status

## Iteration 5 (PAUSED — max iterations reached)

### Completed
- WebSocket connection handler
- Message broadcasting to channels
- User presence tracking

### Blocking Issues
- Race condition in channel join/leave when multiple users join simultaneously
- Message ordering inconsistent under high concurrency (>100 msgs/sec)

### Recommendation
The concurrent access patterns require a Redis-backed message queue instead
of in-memory state. This is an architectural change beyond the current specs.
```

**Manual intervention:**

```bash
# Review the status
cat .claude/sprint/2/status.md

# Update specs to narrow scope and address the architecture gap
# Edit .claude/sprint/2/specs.md:
#   - Add: "Use Redis pub/sub for message distribution"
#   - Add: "Use Redis sorted sets for message ordering"
#   - Remove: Completed items (WebSocket handler, broadcasting, presence)
#   - Focus: Only the two blocking issues

# Resume the sprint
/sprint
# → Phase 0 reads updated specs + status.md
# → Phase 1 architect plans Redis integration
# → Iteration 6 targets only the 2 blocking fixes
```

## Example 3: Frontend-Only Sprint with Manual UI Testing

A sprint focused on UI changes where automated E2E tests are impractical
and manual visual verification is needed.

**specs.md:**

```markdown
# Sprint 3: Dashboard Redesign

## Goal
Redesign the admin dashboard with responsive layout and dark mode support.

## Scope
### In Scope
- Responsive grid layout (mobile, tablet, desktop breakpoints)
- Dark mode toggle with system preference detection
- Dashboard widget reordering via drag-and-drop
- Loading skeleton states for all widgets

### Out of Scope
- New API endpoints or data changes
- Authentication changes
- New dashboard widgets (only restyling existing ones)

## Testing
- QA: skip
- UI Testing: required
- UI Testing Mode: manual
```

**Sprint execution:**

```
Phase 1: Architect produces frontend-specs.md only (no backend)
Phase 2: nextjs-dev agent implements layout, dark mode, drag-and-drop
Phase 3: ui-test-agent generates manual-test-report.md:

  MANUAL TEST CHECKLIST
  ─────────────────────
  [ ] Desktop (1920x1080): Grid shows 3 columns, all widgets visible
  [ ] Tablet (768x1024): Grid collapses to 2 columns
  [ ] Mobile (375x812): Single column, hamburger menu visible
  [ ] Dark mode: Toggle switch in header, all text readable
  [ ] System preference: Respects prefers-color-scheme on first load
  [ ] Drag-and-drop: Reorder widgets, order persists on refresh
  [ ] Skeleton states: Visible during data loading (throttle network to see)

  Instructions: Open the app in a browser and verify each item above.
  Report results by editing this file with [x] for pass or notes for failures.

Phase 4: Sprint pauses for user to complete manual testing
```

## Example 4: Multi-Agent Parallel Implementation

A sprint where backend and frontend agents work simultaneously on the same feature,
coordinated through a shared API contract.

**specs.md:**

```markdown
# Sprint 4: Product Search

## Goal
Full-text search for products with type-ahead suggestions and faceted filtering.

## Scope
### In Scope
- Backend: Search API with Elasticsearch integration (POST /api/search)
- Backend: Facet aggregation endpoint (GET /api/search/facets)
- Frontend: Search bar with debounced type-ahead (300ms delay)
- Frontend: Facet sidebar with checkboxes (category, price range, rating)
- Frontend: Search results grid with pagination

### Out of Scope
- Search analytics or tracking
- Saved searches
- Search result caching

## Testing
- QA: required
- UI Testing: required
- UI Testing Mode: automated
```

**Phase 2 — Parallel agent spawns:**

```
SPAWN REQUEST
Agent: python-dev
Specs: .claude/sprint/4/backend-specs.md
Contract: .claude/sprint/4/api-contract.md
Scope: Search API + facet aggregation

SPAWN REQUEST
Agent: nextjs-dev
Specs: .claude/sprint/4/frontend-specs.md
Contract: .claude/sprint/4/api-contract.md
Scope: Search UI components + facet sidebar

Both agents share api-contract.md which defines:
  POST /api/search
    Request: { query: string, filters: FilterSet, page: number, limit: number }
    Response: { results: Product[], total: number, facets: FacetGroup[] }

  GET /api/search/facets
    Response: { facets: FacetGroup[] }

python-dev works on: src/search/routes.py, src/search/elasticsearch.py
nextjs-dev works on: components/SearchBar.tsx, components/FacetSidebar.tsx
No file path overlap → safe for parallel execution
```

**Phase 3 — Sequential testing:**

```
1. qa-test-agent runs first:
   → Tests search API returns correct results
   → Tests facet aggregation counts
   → Tests pagination boundaries

2. ui-test-agent runs after QA passes:
   → Tests type-ahead renders suggestions after 300ms
   → Tests facet checkbox filtering updates results
   → Tests pagination navigates correctly
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
