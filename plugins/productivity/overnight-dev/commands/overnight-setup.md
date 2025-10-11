---
description: Setup overnight development with Git hooks for autonomous TDD sessions
shortcut: setup-overnight
---

# Overnight Development Setup

Install Git hooks and configure overnight autonomous development in your project.

## What This Does

This command sets up your repository for overnight autonomous development sessions:

1. **Installs Git Hooks** - pre-commit and commit-msg hooks
2. **Creates Config** - .overnight-dev.json configuration file
3. **Verifies Setup** - Tests that hooks work correctly

## Installation Steps

### 1. Check Prerequisites

First, verify you have:
-  Git repository initialized (`git status` works)
-  Test framework configured (Jest, pytest, etc.)
-  At least 1 passing test
-  Linter set up (ESLint, flake8, etc.)

### 2. Install the Hooks

The plugin will copy Git hooks to `.git/hooks/`:
- **pre-commit** - Runs linting and tests before each commit
- **commit-msg** - Enforces conventional commit format

### 3. Configure Your Project

Create `.overnight-dev.json` in your project root:

```json
{
  "testCommand": "npm test",
  "lintCommand": "npm run lint",
  "requireCoverage": true,
  "minCoverage": 80,
  "autoFix": true,
  "maxAttempts": 50,
  "stopOnMorning": true,
  "morningHour": 7
}
```

**Configuration Options:**

- `testCommand` - Command to run tests (e.g., "pytest", "cargo test")
- `lintCommand` - Command to run linter
- `requireCoverage` - Enforce minimum test coverage
- `minCoverage` - Minimum coverage percentage (default: 80)
- `autoFix` - Automatically fix linting issues
- `maxAttempts` - Maximum commit attempts before alerting
- `stopOnMorning` - Stop work at a specific hour
- `morningHour` - Hour to stop (0-23)

### 4. Test the Setup

Verify the hooks work:

```bash
# Should run tests and linting
git commit --allow-empty -m "test: verify overnight dev hooks"
```

If hooks work correctly, you'll see:
```
 Overnight Dev: Running pre-commit checks...
 Running linting...
 Linting passed
 Running tests...
 All tests passed
 All checks passed! Proceeding with commit...
```

## Project-Specific Examples

### Node.js / JavaScript

```json
{
  "testCommand": "npm test -- --coverage",
  "lintCommand": "npm run lint",
  "autoFix": true
}
```

### Python

```json
{
  "testCommand": "pytest --cov=. --cov-report=term-missing",
  "lintCommand": "flake8 . && black --check .",
  "autoFix": false
}
```

### Rust

```json
{
  "testCommand": "cargo test",
  "lintCommand": "cargo clippy -- -D warnings",
  "autoFix": false
}
```

### Go

```json
{
  "testCommand": "go test ./...",
  "lintCommand": "golangci-lint run",
  "autoFix": false
}
```

## Starting an Overnight Session

Once setup is complete:

1. **Define your goal:**
   ```
   Task: Implement user authentication with JWT
   Success: All tests pass, coverage > 85%
   ```

2. **Start coding:**
   - Write tests first (TDD)
   - Implement features
   - Commit frequently
   - Let the hooks keep you honest

3. **Claude works overnight:**
   - Every commit must pass tests
   - Hooks enforce quality
   - Morning brings fully tested features

## Troubleshooting

### "Hooks not executing"

```bash
# Make hooks executable
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/commit-msg
```

### "Tests failing immediately"

Make sure you have at least 1 passing test before starting:
```bash
npm test  # or pytest, cargo test, etc.
```

### "Linting errors blocking commits"

Enable auto-fix in config:
```json
{
  "autoFix": true
}
```

Or fix manually:
```bash
npm run lint -- --fix
```

## What Happens During Overnight Sessions

1. **You write code** → Claude writes tests and implementation
2. **You try to commit** → Hooks run tests automatically
3. **Tests fail** → Claude debugs and fixes
4. **Tests pass** → Commit succeeds
5. **Repeat** → Until feature is complete
6. **Morning** → Wake up to fully tested code

## Success Metrics

Track your overnight session:
-  All commits have passing tests
-  Coverage maintained or improved
-  No linting errors
-  Clean conventional commit messages
-  Features fully implemented and documented

## Pro Tips

1. **Start with clear goals** - Specific, testable objectives
2. **Have existing tests** - At least 1 passing test before starting
3. **Use TDD** - Write tests first, then implementation
4. **Commit frequently** - Small, passing commits
5. **Trust the process** - Hooks enforce quality automatically

Ready to start? Just begin coding and let the hooks guide you to fully tested features! 
