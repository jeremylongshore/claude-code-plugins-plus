# The 7-Step Workflow

This is the operational core of zero-tech-debt. Walk the steps in order. Don't skip step 1.

## 1. Define the Intended End State

Before touching code, describe in 1-3 concise paragraphs:

- **What the final UX should feel like** — what the user / operator / caller sees and does
- **What the clean architecture should look like** — one coherent flow, one source of truth, one ownership boundary
- **What the public surface area actually needs to be** — every other function/route/export is private
- **What developers should intuitively expect** — what a new hire would guess without reading the code

If the intended end state is unclear, **stop and clarify before refactoring**. Code is the wrong medium for thinking through architecture; prose is faster and revisable.

## 2. Audit Reality Against Intent

Identify everything in the current implementation that doesn't serve the end state:

- Compatibility shims, legacy wrappers, route aliases, duplicate flows
- Feature flags that became permanent architecture
- State duplicated across layers
- "Just in case" abstractions that turned out never to be needed
- Dead props, modes, handlers, and APIs
- Historical naming that no longer reflects product intent

Document, for each candidate for removal:

- **Why it exists** — what problem was it solving when it was written?
- **Who currently calls it** — is anyone still using it, or is it cargo-culted?
- **Whether it still provides real value** — does the user-visible behavior change if it's gone?

See [`04-audit-patterns.md`](04-audit-patterns.md) for concrete grep targets.

## 3. Delete Before Adding

Before introducing **a new abstraction / hook / config layer / flag / adapter / state container**, attempt to:

- Remove obsolete logic
- Collapse duplicated paths
- Simplify ownership boundaries
- Unify flows
- Flatten unnecessary indirection

**Prefer subtraction over architecture theater.** A refactor that adds three new abstractions to "fix" tech debt has not paid down debt — it has moved it.

Important: don't introduce a new abstraction in the *same change* that removes an old one. Split into two reviewable steps so the reviewer can evaluate the deletion separately from the addition.

## 4. Optimize Around the Final Shape

Refactor toward the system that **should exist today**, not the system that minimizes diff.

Do not preserve bad boundaries simply because:

- They existed historically
- They reduced diff size
- They avoided touching multiple files
- They were once needed during migration

Prefer:

- One coherent flow
- One authoritative source of truth
- One obvious ownership boundary
- One naming system
- One predictable state model

## 5. Collapse Duplicate Decision Logic

Rules should exist in one place. Don't duplicate:

- Permission checks
- Feature gating
- Route logic
- URL parsing
- State derivation
- Validation rules
- Retry behavior
- Command naming
- Orchestration logic

**View components should not secretly own domain policy.** If your React component has a permission check inline, that policy is now duplicated wherever else the resource is accessed. Lift it to one authoritative location.

## 6. Remove Historical Leakage

The codebase should describe **current product intent**, **current domain language**, **current operational reality** — not old implementation history.

Rename:

- Legacy terminology that no longer matches the product
- Migration-oriented naming (`*_v2`, `*_new`, `Legacy*`)
- Implementation-leaked concepts (e.g., a class called `MongoOrderStore` when Mongo was replaced with Postgres last year)
- Misleading abstractions whose names suggest one responsibility but implement another

Prefer names aligned with:

- User behavior
- Domain intent
- System responsibility

A rename without redirecting callers leaves a search-and-find trail of broken references. Always update every caller in the same commit as the rename.

## 7. Validate the New Shape

After refactoring, verify:

- **Deleted paths truly have no callers** — re-grep, including in test files, config files, docs, and CI
- **Navigation still works** — for UI work, click through the affected flows manually, don't rely on snapshot tests
- **Persisted state still behaves correctly** — for storage refactors, migrate-up then migrate-down then migrate-up again on a real database snapshot
- **Permission boundaries remain correct** — re-walk the auth flow with a non-admin account
- **APIs remain coherent** — for public surfaces, run any contract tests; for internal APIs, walk the call graph
- **Tests validate intended behavior** rather than historical quirks — if a test references a deleted concept, the test was probably wrong, not the refactor

Add regression coverage for:

- Removed assumptions
- State transitions
- Orchestration boundaries
- Routing behavior
- Migration-sensitive logic

The new tests should describe the *intended shape*, not the historical shape. If you find yourself writing a test that asserts the old behavior, stop and ask whether the old behavior was actually correct.
