# Task Templates

Pre-built decomposition patterns Opus selects automatically based on the request type. Templates are starting points — Opus adapts them to the specific task and project.

## Templates

### CRUD Feature

**Trigger:** "add X management", "build X CRUD", "create X with list and form"

```
Task 1: [Sonnet] Create data model / schema (if needed)
Task 2: [Sonnet] Create API routes / server actions (depends on 1)
Task 3: [Sonnet] Build list/table UI (parallel with 2 if model exists)
Task 4: [Sonnet] Build create/edit form UI (parallel with 3)
Task 5: [Sonnet] Add tests for API + UI (depends on 2, 3, 4)
```

### API Endpoint

**Trigger:** "add endpoint for X", "create API for X", "add server action for X"

```
Task 1: [Sonnet] Define schema (zod / types)
Task 2: [Sonnet] Implement handler / server action (depends on 1)
Task 3: [Sonnet] Add tests (depends on 2)
```

### UI Component

**Trigger:** "build X component", "add X to the page", "create X widget"

```
Task 1: [Sonnet] Create component + styles
Task 2: [Sonnet] Add tests / stories (parallel with wiring)
Task 3: [Sonnet] Wire into parent page / layout (depends on 1)
```

### Database Migration

**Trigger:** "add X column", "new X table", "rename X field", "change X schema"

```
Task 1: [Sonnet] Update Prisma schema / migration file
Task 2: [Sonnet] Run prisma generate + validate
Task 3: [Sonnet] Update affected queries / server actions (depends on 1)
Task 4: [Sonnet] Update seed data if applicable (parallel with 3)
```

### Refactor

**Trigger:** "refactor X", "extract X into Y", "move X to shared", "split X"

```
Task 1: [Sonnet] Identify all usages and dependents (search)
Task 2: [Sonnet] Extract / move / rename (depends on 1)
Task 3: [Sonnet] Update all imports and references (depends on 2)
Task 4: [Sonnet] Verify tests still pass (depends on 3)
```

### Bug Fix

**Trigger:** "fix X", "X is broken", "X doesn't work"

```
Task 1: [Opus] Root cause analysis (read code, reproduce)
Task 2: [Sonnet] Implement fix (depends on 1)
Task 3: [Sonnet] Add regression test (parallel with 2 if cause is clear)
Task 4: [Opus] Verify fix + no regressions (depends on 2, 3)
```

## Combining Templates

Opus can combine templates for complex requests:

- "Add user management with database" = CRUD Feature + Database Migration
- "Build a dashboard component with API" = UI Component + API Endpoint
- "Refactor auth and add new endpoint" = Refactor + API Endpoint

## Custom Templates

Users can define project-specific templates in their CLAUDE.md:

```markdown
## Hyperflow Templates
### New Domain Module
Task 1: Create domain folder structure
Task 2: Add messages/en.json
Task 3: Create server actions
Task 4: Build page route
Task 5: Add to navigation
```

## Rules

1. **Templates are suggestions.** Opus adapts based on context — skip steps that don't apply, add steps that are needed.
2. **Dependency ordering.** Tasks with dependencies wait. Independent tasks run in parallel.
3. **One template per request.** If a request maps to multiple templates, Opus combines them into a single decomposition.
