## Examples

### Example 1: Building JWT Authentication

User request: "Implement JWT authentication with 90% test coverage overnight."

Workflow:

1. Claude writes failing authentication tests (TDD).
2. Claude implements JWT signing (tests still failing).
3. Claude debugs token generation (commit blocked, keeps trying).
4. Tests pass! Commit succeeds.
5. Claude adds middleware (writes tests first).
6. Integration tests (debugging edge cases).
7. All tests green (Coverage: 94%).
8. Claude adds docs, refactors, still green.
9. Session complete.

### Example 2: Refactoring Database Layer

User request: "Refactor the database layer to use the repository pattern overnight."

Workflow:

1. Claude analyzes existing tests to ensure no regression.
2. Claude implements the repository pattern.
3. Tests are run; some fail due to changes in data access.
4. Claude updates tests to align with the new repository pattern.
5. All tests pass; commit succeeds.
6. Claude documents the refactored database layer.
7. Session complete.

### Example 3: Fixing a Bug in Payment Processing

User request: "Fix the bug in payment processing that causes incorrect amounts to be charged overnight."

Workflow:

1. Claude reproduces the bug and writes a failing test case.
2. Claude analyzes the code and identifies the root cause of the bug.
3. Claude fixes the bug and runs the tests.
4. The failing test case now passes; all other tests also pass.
5. Commit succeeds.
6. Claude adds a comment to the code explaining the fix.
7. Session complete.

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
