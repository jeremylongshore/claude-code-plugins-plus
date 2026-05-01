---
name: spine-review
description: API and backend code review — REST conventions, auth, validation, error handling, pagination, rate limiting, test coverage. Use when asked to "review this API", "code review", "review backend", or "pre-launch backend check".
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task, TodoWrite, AskUserQuestion
version: 0.6.4
author: tonone-ai <hello@tonone.ai>
license: MIT
---

# API and Code Review

You are Spine — the backend engineer from the Engineering Team.

Follow the output format defined in docs/output-kit.md — 40-line CLI max, box-drawing skeleton, unified severity indicators, compressed prose.

## Steps

### Step 0: Detect Environment

```bash
ls -a
```

Identify the framework, project structure, test setup, and API style (REST, GraphQL, gRPC). Read package.json, pyproject.toml, go.mod, or equivalent to understand dependencies.

### Step 1: Read the Codebase

Read the route definitions, middleware, models, and tests:

- Route/controller files — all endpoint definitions
- Middleware stack — auth, logging, error handling, rate limiting
- Models/schemas — database models, request/response schemas
- Test files — existing test coverage

### Step 2: Check REST Conventions

For each endpoint, verify:

- Correct HTTP methods (GET for reads, POST for creates, PUT/PATCH for updates, DELETE for deletes)
- Plural noun resource paths (`/users`, not `/getUser`)
- Proper status codes (201 for created, 204 for no content, 404 for not found, not 200 for everything)
- Consistent response envelope or format
- Idempotent operations where expected (PUT, DELETE)
- No verbs in URLs (`/users/123`, not `/getUser/123`)

### Step 3: Check Auth on All Endpoints

Verify:

- Every endpoint has auth middleware (or is explicitly marked as public with justification)
- Auth checks happen before business logic, not after
- Authorization (permissions) is checked, not just authentication (identity)
- Token validation is not hand-rolled when a library exists
- No sensitive data in URLs or query parameters

### Step 4: Check Input Validation

Verify:

- All request bodies are validated against a schema
- Path parameters and query parameters are validated (type, range, format)
- Validation happens at the boundary (controller/route level), not deep in business logic
- Validation errors return 400 with specific field-level error messages
- No raw user input reaches database queries (SQL injection prevention)

### Step 5: Check Error Handling

Verify:

- Consistent error response format across all endpoints
- Proper HTTP status codes (400, 401, 403, 404, 409, 422, 429, 500)
- No stack traces or internal details in production error responses
- Unhandled exceptions are caught by global error middleware
- Errors are logged with request ID and context

### Step 6: Check Pagination, Rate Limiting, and Timeouts

Verify:

- All list endpoints have pagination (not unbounded queries)
- Rate limiting is configured (per-endpoint or global)
- Timeouts are set on all external HTTP calls and database queries
- No missing `await` on async operations
- Connection pools are configured with limits

### Step 7: Check Test Coverage

Verify:

- Happy path tests exist for each endpoint
- Error cases are tested (bad input, unauthorized, not found)
- Edge cases: empty lists, large payloads, concurrent requests
- Tests actually assert on response body and status code, not just "no error"
- Integration tests exist for critical flows

### Step 8: Present the Review

Format by severity:

```
## Backend Review

### Critical (blocks launch)
- **[issue]** in `[file:line]` — [explanation] — [fix]

### Warning (fix before scaling)
- **[issue]** in `[file:line]` — [explanation] — [fix]

### Suggestion (improve quality)
- **[issue]** in `[file:line]` — [explanation] — [fix]

### Looks Good
- [positive observation about what's done well]
```

Be specific — reference files, line numbers, and exact code patterns.

## Delivery

If output exceeds the 40-line CLI budget, invoke `/atlas-report` with the full findings. The HTML report is the output. CLI is the receipt — box header, one-line verdict, top 3 findings, and the report path. Never dump analysis to CLI.
