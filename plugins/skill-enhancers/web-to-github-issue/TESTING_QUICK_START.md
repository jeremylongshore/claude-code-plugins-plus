# Testing Quick Start Guide

Fast reference for running tests on the web-to-github-issue plugin.

## Quick Commands

```bash
# Run all tests (single run)
pnpm test

# Run tests in watch mode (auto-rerun on file changes)
pnpm run test:watch

# Run tests with interactive UI (browser-based)
pnpm run test:ui

# Generate coverage report
pnpm run test:coverage

# Generate coverage with interactive UI
pnpm run test:coverage:ui
```

## Current Status

✅ **118 tests passing**
✅ **96.08% statement and line coverage**
✅ **93.2% branch coverage and 100% function coverage**
✅ **Zero failures**
✅ **Fast local execution**

## Test Files

| File | Tests | Coverage | Focus Area |
|------|-------|----------|-----------|
| `github-client.test.js` | 23 | 90.85% statements/lines | GitHub API client, auth, error handling |
| `parser.test.js` | 46 | 100% | Search result parsing, edge cases |
| `formatter.test.js` | 49 | 100% | Markdown formatting, title/label logic |

## Coverage Thresholds

All thresholds **PASSING**:

- ✅ Statements: 96.08% (threshold: 80%)
- ✅ Branches: 93.2% (threshold: 80%)
- ✅ Functions: 100% (threshold: 80%)
- ✅ Lines: 96.08% (threshold: 80%)

## View Coverage Reports

```bash
# Generate coverage
pnpm run test:coverage

# Open HTML report in browser
open coverage/index.html
# or
xdg-open coverage/index.html  # Linux
```

## Troubleshooting

### Tests not running?

```bash
# Reproduce the locked standalone install
pnpm install --ignore-workspace --frozen-lockfile
```

### Coverage files missing?

```bash
# Regenerate the coverage report
pnpm run test:coverage
```

### Need verbose output?

```bash
# Run with reporter
pnpm test -- --reporter=verbose
```

## CI Integration

For continuous integration pipelines:

```yaml
# GitHub Actions
- run: pnpm install --ignore-workspace --frozen-lockfile
- run: pnpm test
- run: pnpm run test:coverage
- uses: codecov/codecov-action@v3
  with:
    files: ./coverage/lcov.info
```

## Before Committing

Always run:

```bash
pnpm run test:coverage
```

Ensure:

- ✅ All tests pass
- ✅ Coverage stays above 80%
- ✅ No new uncovered code

## Documentation

- **Detailed Guide**: `tests/README.md`
- **Test Summary**: `TEST_SUMMARY.md`
- **This Quick Start**: `TESTING_QUICK_START.md`

---

**Framework**: Vitest 3.2.7
**Last Verified**: September 2026
**Status**: ✅ All systems green
