---
name: overnight-development
description: |
  Automates software development overnight using Git hooks to enforce test-driven development (TDD).
  This skill should be used when Claude needs to build new features, refactor existing code, or fix bugs autonomously,
  ensuring all changes are fully tested and meet specified quality standards. Use when the user mentions "overnight development",
  "autonomous coding", or asks about TDD workflows and Git hooks. This skill leverages Git hooks to block commits until all tests pass,
  enforcing a rigorous TDD process and ensuring high-quality, production-ready code.
allowed-tools: - Read
- Write
- Bash
version: 1.0.0
---

# Overnight Development

## Overview

This skill automates software development overnight by leveraging Git hooks to enforce test-driven development (TDD). It ensures that all code changes are fully tested and meet specified quality standards before being committed. This approach allows Claude to work autonomously, building new features, refactoring existing code, or fixing bugs while adhering to a rigorous TDD process.

## Core Capabilities

-   Enforces test-driven development (TDD) using Git hooks.
-   Automates debugging and code fixing until all tests pass.
-   Tracks progress and logs activities during overnight sessions.
-   Supports flexible configuration for various testing frameworks and languages.
-   Provides guidance and support through the `overnight-dev-coach` agent.

## Workflow

### Phase 1: Project Setup and Configuration

To prepare the project for overnight development:

1.  **Verify Prerequisites:** Ensure the project is a Git repository, has a configured test framework, and includes at least one passing test.
    ```bash
    git init
    npm install --save-dev jest # Example for Node.js
    ```

2.  **Install the Plugin:** Add the Claude Code Plugin marketplace and install the `overnight-dev` plugin.
    ```bash
    /plugin marketplace add jeremylongshore/claude-code-plugins
    /plugin install overnight-dev@claude-code-plugins-plus
    ```

3.  **Run Setup Command:** Execute the `/overnight-setup` command to create necessary Git hooks and configuration files.
    ```bash
    /overnight-setup
    ```

### Phase 2: Task Definition and Planning

To define the task for the overnight session:

1.  **Define a Clear Goal:** Specify a clear and testable goal for the overnight session, such as "Build user authentication with JWT (90% coverage)."
    ```text
    Task: Build user authentication with JWT (90% coverage)
    Success: All tests pass, 90%+ coverage, fully documented
    ```

2.  **Start Coding:** Begin implementing the feature by writing tests first, following the TDD approach.
    ```javascript
    // Example test case (Node.js with Jest)
    it('should authenticate a user with valid credentials', async () => {
      // Test implementation
    });
    ```

3.  **Attempt to Commit:** Try to commit the changes, which will trigger the Git hooks and run the tests.
    ```bash
    git commit -m "feat: implement user authentication"
    ```

### Phase 3: Autonomous Development and Debugging

To allow Claude to work autonomously:

1.  **Git Hooks Enforcement:** The Git hooks will block the commit if any tests fail, providing Claude with the error messages.
    ```text
    Overnight Dev: Running pre-commit checks...
    Running linting...
    Linting passed
    Running tests...
    12 tests failing
    Commit blocked!
    ```

2.  **Automated Debugging:** Claude analyzes the error messages, identifies the issues, and attempts to fix the code.
    ```text
    Claude: Fixing test failures in user authentication module.
    ```

3.  **Retry Commits:** Claude retries the commit after making the necessary fixes, repeating the process until all tests pass.
    ```bash
    git commit -m "fix: address test failures in user authentication"
    ```

### Phase 4: Progress Tracking and Completion

To monitor the progress and finalize the session:

1.  **Monitor Progress:** Track the progress of the overnight session by viewing the log file.
    ```bash
    cat .overnight-dev-log.txt
    ```

2.  **Review Results:** Wake up to fully tested code, complete features, and a clean Git history.
    ```text
    7 AM: You wake up to:
    - 47 passing tests (0 failing)
    - 94% test coverage
    - Clean conventional commit history
    - Fully documented JWT authentication
    - Production-ready code
    ```

3.  **Session Completion:** The session completes when all tests pass, the code meets the specified quality standards, and the changes are committed.

## Using Bundled Resources

### Scripts

To automate the setup process, use the `overnight-setup.sh` script:

```bash
./scripts/overnight-setup.sh
```

To track the progress of the overnight session, use the `progress-tracker.py` script:

```bash
./scripts/progress-tracker.py --log .overnight-dev-log.txt
```

### References

For detailed configuration options, load:

-   [Configuration Reference](./references/configuration_reference.md)

For best practices on writing effective tests, load:

-   [Testing Best Practices](./references/testing_best_practices.md)

### Assets

Available templates:

-   `assets/commit-template.txt` - Template for generating commit messages.
-   `assets/readme-template.md` - Template for generating README files.

## Examples

### Example 1: Building JWT Authentication

User request: "Implement JWT authentication with 90% test coverage overnight."

Workflow:

1.  Claude writes failing authentication tests (TDD).
2.  Claude implements JWT signing (tests still failing).
3.  Claude debugs token generation (commit blocked, keeps trying).
4.  Tests pass! Commit succeeds.
5.  Claude adds middleware (writes tests first).
6.  Integration tests (debugging edge cases).
7.  All tests green (Coverage: 94%).
8.  Claude adds docs, refactors, still green.
9.  Session complete.

### Example 2: Refactoring Database Layer

User request: "Refactor the database layer to use the repository pattern overnight."

Workflow:

1.  Claude analyzes existing tests to ensure no regression.
2.  Claude implements the repository pattern.
3.  Tests are run; some fail due to changes in data access.
4.  Claude updates tests to align with the new repository pattern.
5.  All tests pass; commit succeeds.
6.  Claude documents the refactored database layer.
7.  Session complete.

### Example 3: Fixing a Bug in Payment Processing

User request: "Fix the bug in payment processing that causes incorrect amounts to be charged overnight."

Workflow:

1.  Claude reproduces the bug and writes a failing test case.
2.  Claude analyzes the code and identifies the root cause of the bug.
3.  Claude fixes the bug and runs the tests.
4.  The failing test case now passes; all other tests also pass.
5.  Commit succeeds.
6.  Claude adds a comment to the code explaining the fix.
7.  Session complete.

## Best Practices

-   Ensure that the task is well-defined and testable.
-   Follow the TDD approach by writing tests before implementing features.
-   Monitor the progress of the overnight session by viewing the log file.
-   Configure the Git hooks and settings appropriately for the project.
-   Use the `overnight-dev-coach` agent for guidance and support.

## Troubleshooting

**Issue:** Hooks are not running.

**Solution:** Make sure the hooks are executable:

```bash
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
```

**Issue:** Tests are failing immediately.

**Solution:** Ensure you have at least one passing test:

```bash
npm test # Should see: Tests passed
```

**Issue:** Lint errors are blocking everything.

**Solution:** Enable auto-fix:

```json
{
  "autoFix": true
}
```

Or fix manually:

```bash
npm run lint -- --fix
```

## Integration

This skill integrates with Git repositories and various testing frameworks. It uses Git hooks to enforce TDD and ensure that all code changes are fully tested. The `overnight-dev-coach` agent provides guidance and support throughout the process.

```bash
# Example integration with Jest (Node.js)
{
  "testCommand": "npm test -- --coverage --watchAll=false",
  "lintCommand": "npm run lint",
  "autoFix": true
}
```

```bash
# Example integration with pytest (Python)
{
  "testCommand": "pytest --cov=. --cov-report=term-missing",
  "lintCommand": "flake8 . && black --check .",
  "autoFix": false
}
```
```
