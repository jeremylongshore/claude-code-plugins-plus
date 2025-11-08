# Testing Quick Start Guide

Fast reference for running tests on the web-to-github-issue plugin.

## Quick Commands

```bash
# Run all tests (single run)
npm test

# Run tests in watch mode (auto-rerun on file changes)
npm run test:watch

# Run tests with interactive UI (browser-based)
npm run test:ui

# Generate coverage report
npm run test:coverage

# Generate coverage with interactive UI
npm run test:coverage:ui
```

## Current Status

✅ **118 tests passing**
✅ **100% code coverage** (statements, functions, lines)
✅ **98.8% branch coverage**
✅ **Zero failures**
✅ **Fast execution** (~1.5 seconds)

## Test Files

| File | Tests | Coverage | Focus Area |
|------|-------|----------|-----------|
| `github-client.test.js` | 23 | 100% | GitHub API client, auth, error handling |
| `parser.test.js` | 46 | 100% | Search result parsing, edge cases |
| `formatter.test.js` | 49 | 100% | Markdown formatting, title/label logic |

## Coverage Thresholds

All thresholds **PASSING**:
- ✅ Statements: 100% (threshold: 80%)
- ✅ Branches: 98.8% (threshold: 80%)
- ✅ Functions: 100% (threshold: 80%)
- ✅ Lines: 100% (threshold: 80%)

## View Coverage Reports

```bash
# Generate coverage
npm run test:coverage

# Open HTML report in browser
open coverage/index.html
# or
xdg-open coverage/index.html  # Linux
```

## Troubleshooting

### Tests not running?
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### Coverage files missing?
```bash
# Clean and regenerate
rm -rf coverage/
npm run test:coverage
```

### Need verbose output?
```bash
# Run with reporter
npm test -- --reporter=verbose
```

## CI Integration

For continuous integration pipelines:

```yaml
# GitHub Actions
- run: npm test
- run: npm run test:coverage
- uses: codecov/codecov-action@v3
  with:
    files: ./coverage/lcov.info
```

## Before Committing

Always run:
```bash
npm run test:coverage
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

**Framework**: Vitest 3.2.4
**Last Updated**: January 2025
**Status**: ✅ All systems green
