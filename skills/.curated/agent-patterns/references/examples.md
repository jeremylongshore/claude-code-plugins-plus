# Examples

## Example 1: Spawning a Single Implementation Agent

The simplest pattern: one agent implementing one spec file with a shared contract.

**SPAWN REQUEST block:**

```
SPAWN REQUEST
Agent: python-dev
Specs: .claude/sprint/1/backend-specs.md
Contract: .claude/sprint/1/api-contract.md
Scope: All backend endpoints
```

**Agent reads these files, implements, then returns:**

```
AGENT REPORT
Agent: python-dev
Status: COMPLETE
Files Modified:
  - src/routes/users.py (created)
  - src/models/user.py (created)
  - src/middleware/auth.py (created)
  - tests/test_users.py (created)
Tests: 15 added, 15 passing
Conformity: All endpoints match api-contract.md schemas
Notes: Used bcrypt for password hashing per spec requirement
```

## Example 2: Parallel Agent Spawns with Domain Partitioning

Multiple agents running concurrently, each assigned to a non-overlapping domain
boundary to prevent file conflicts.

**Architect produces three SPAWN REQUEST blocks:**

```
SPAWN REQUEST
Agent: python-dev
Specs: .claude/sprint/2/backend-specs.md
Contract: .claude/sprint/2/api-contract.md
Scope: REST API endpoints and database models

SPAWN REQUEST
Agent: nextjs-dev
Specs: .claude/sprint/2/frontend-specs.md
Contract: .claude/sprint/2/api-contract.md
Scope: React components and page routes

SPAWN REQUEST
Agent: cicd-agent
Specs: .claude/sprint/2/infra-specs.md
Scope: Docker, GitHub Actions, and deployment configs
```

**Domain boundaries (no file overlap):**

```
python-dev  → src/api/*, src/models/*, tests/api/*
nextjs-dev  → app/*, components/*, tests/ui/*
cicd-agent  → .github/workflows/*, Dockerfile, docker-compose.yml
```

**All three agents run simultaneously. Reports collected:**

```
AGENT REPORT
Agent: python-dev
Status: COMPLETE
Files Modified: src/api/products.py, src/models/product.py, tests/api/test_products.py
Tests: 22 added, 22 passing
Conformity: All 6 backend endpoints match contract

AGENT REPORT
Agent: nextjs-dev
Status: COMPLETE
Files Modified: app/products/page.tsx, components/ProductCard.tsx, components/SearchBar.tsx
Tests: 8 component tests added
Conformity: All UI components consume contract-defined response types

AGENT REPORT
Agent: cicd-agent
Status: COMPLETE
Files Modified: .github/workflows/ci.yml, Dockerfile, docker-compose.yml
Tests: CI pipeline validated locally
Conformity: Deployment config targets correct service ports
```

## Example 3: Testing Agent Coordination (Sequential)

Testing agents must run after implementation agents complete. QA runs first,
then UI testing runs after QA passes.

**Sequential SPAWN REQUEST chain:**

```
SPAWN REQUEST
Agent: qa-test-agent
Specs: .claude/sprint/3/specs.md
Run After: python-dev, nextjs-dev
Contract: .claude/sprint/3/api-contract.md
Scope: API integration tests and unit test validation

SPAWN REQUEST
Agent: ui-test-agent
Specs: .claude/sprint/3/specs.md
Run After: qa-test-agent
Scope: Browser-based E2E tests for all user flows
```

**QA agent report:**

```
AGENT REPORT
Agent: qa-test-agent
Status: COMPLETE
Tests:
  - API tests: 34 passed, 2 failed
  - Unit tests: 67 passed, 0 failed
  - Coverage: 89%
Failures:
  1. POST /api/orders returns 500 when cart is empty (expected 400)
  2. GET /api/orders/:id returns stale cache after update

Conformity: 2 endpoints deviate from api-contract.md error codes
```

**UI test agent report (using structured format):**

```
AGENT REPORT
Agent: ui-test-agent
Status: COMPLETE
Tests:
  - E2E scenarios: 12 passed, 1 failed
  - Visual regression: 0 changes detected
Failures:
  1. Checkout flow: Submit button stays disabled after form validation passes
     Screenshot: .claude/sprint/3/screenshots/checkout-button-disabled.png

Console Errors:
  - TypeError: Cannot read property 'validate' of undefined (checkout.tsx:45)

Conformity: Checkout flow blocked by frontend validation bug
```

## Example 4: Architect Review and Iteration Decision

After collecting all agent reports, the architect decides whether to iterate
or finalize.

**Architect receives reports from Iteration 1:**

```
python-dev: COMPLETE (all endpoints working)
nextjs-dev: COMPLETE (all components rendered)
qa-test-agent: 2 failures (empty cart 500, stale cache)
ui-test-agent: 1 failure (checkout button disabled)
```

**Architect analysis:**

```
Conformity Review:
  ✓ 4/6 API endpoints fully conformant
  ✗ POST /api/orders: Missing empty-cart validation (backend fix)
  ✗ GET /api/orders/:id: Cache invalidation missing (backend fix)
  ✗ Checkout form: Validation state not propagating (frontend fix)

Decision: ITERATE
Reason: 3 targeted fixes needed, all within clear scope

Updated backend-specs.md:
  - REMOVED: All completed endpoint specs
  - ADDED: Fix empty cart → return 400 with ApiError
  - ADDED: Invalidate order cache on PATCH/DELETE

Updated frontend-specs.md:
  - REMOVED: All completed component specs
  - ADDED: Fix checkout form validation state propagation

Updated status.md:
  Iteration 1: 3/6 user stories complete. 3 fixes needed.
```

**Architect spawns narrowed Iteration 2:**

```
SPAWN REQUEST
Agent: python-dev
Specs: .claude/sprint/3/backend-specs.md
Contract: .claude/sprint/3/api-contract.md
Scope: Fix empty-cart validation and cache invalidation only

SPAWN REQUEST
Agent: nextjs-dev
Specs: .claude/sprint/3/frontend-specs.md
Scope: Fix checkout form validation state only
```

## Example 5: Framework-Specific Agent Selection

The orchestrator detects the project framework and selects appropriate
specialized agents.

**Project detection:**

```
Phase 0 scan:
  → Found: next.config.js → Framework: Next.js
  → Found: requirements.txt with fastapi → Backend: FastAPI
  → Found: docker-compose.yml → Infrastructure: Docker

Agent selection:
  → nextjs-dev (instead of generic frontend agent)
  → python-dev (instead of generic backend agent)
  → cicd-agent (for Docker + CI pipeline)
```

**For a different project stack:**

```
Phase 0 scan:
  → Found: nuxt.config.ts → Framework: Nuxt 3
  → Found: package.json with express → Backend: Express.js
  → Found: serverless.yml → Infrastructure: AWS Lambda

Agent selection:
  → allpurpose-agent with Nuxt context (no nuxt-specific agent exists)
  → allpurpose-agent with Express context
  → cicd-agent with serverless framework context
```

## Example 6: Handling Agent Failures

When an agent fails to produce a valid report or encounters unrecoverable errors.

**Failed agent report:**

```
AGENT REPORT
Agent: python-dev
Status: FAILED
Error: Cannot install dependency 'psycopg2-binary' — compilation fails on arm64
Files Modified: None
Tests: None
Conformity: Unable to assess — implementation did not start
```

**Architect response:**

```
Architect reviews failure:
  → Root cause: platform-specific dependency issue
  → Resolution: Switch to 'asyncpg' (pure Python, no compilation)
  → Updates backend-specs.md: Replace psycopg2-binary with asyncpg

SPAWN REQUEST
Agent: python-dev
Specs: .claude/sprint/1/backend-specs.md (updated)
Contract: .claude/sprint/1/api-contract.md
Scope: All backend endpoints (retry with asyncpg)
Notes: Use asyncpg instead of psycopg2-binary for PostgreSQL
```

## Example 7: Scoped Agent with File Path Constraints

When agents need strict boundaries to prevent overlapping modifications.

**Tightly scoped SPAWN REQUEST:**

```
SPAWN REQUEST
Agent: python-dev
Specs: .claude/sprint/5/backend-specs.md
Contract: .claude/sprint/5/api-contract.md
Scope: Payment processing endpoints only
Allowed Paths:
  - src/payments/**
  - tests/payments/**
  - src/models/payment.py
Forbidden Paths:
  - src/auth/**
  - src/users/**
  - src/orders/** (owned by another agent in this iteration)
```

**Agent respects boundaries in its report:**

```
AGENT REPORT
Agent: python-dev
Status: COMPLETE
Files Modified:
  - src/payments/routes.py (created)
  - src/payments/stripe_client.py (created)
  - src/models/payment.py (created)
  - tests/payments/test_payments.py (created)
Tests: 9 added, 9 passing
Conformity: All payment endpoints match contract
Notes: Did not modify src/orders/ — referenced via import only
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
