---
name: analyzing-test-coverage
description: |
  Analyze code coverage metrics and identify untested code paths.
  Use when analyzing untested code or coverage gaps.
  Trigger with phrases like "analyze coverage", "check test coverage", or "find untested code".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:coverage-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Test Coverage Analyzer

## Current State
!`ls package.json pyproject.toml Cargo.toml go.mod 2>/dev/null || echo 'No project manifest found'`
!`node -v 2>/dev/null || python3 --version 2>/dev/null || echo 'No runtime detected'`

## Overview

Analyze code coverage metrics to identify untested code paths, dead code, and coverage gaps across line, branch, function, and statement dimensions. Supports Istanbul/nyc (JavaScript/TypeScript), coverage.py (Python), JaCoCo (Java), and Go coverage tools.

## Prerequisites

- Coverage tool installed and configured (Istanbul/nyc, c8, coverage.py, JaCoCo, or `go test -cover`)
- Test suite that can run with coverage instrumentation enabled
- Coverage threshold targets defined (recommended: 80% lines, 70% branches)
- Coverage output format set to JSON or LCOV for programmatic analysis
- Git history available for coverage trend comparison

## Instructions

1. Run the test suite with coverage instrumentation enabled:
   - JavaScript: `npx jest --coverage --coverageReporters=json-summary,lcov`
   - Python: `pytest --cov=src --cov-report=json --cov-report=term-missing`
   - Go: `go test -coverprofile=coverage.out ./...`
   - Java: Configure JaCoCo Maven/Gradle plugin with XML report output.
2. Parse the coverage report and extract per-file metrics:
   - Line coverage percentage per file.
   - Branch coverage percentage per file.
   - Function coverage percentage per file.
   - Uncovered line ranges (specific line numbers).
3. Identify critical coverage gaps by prioritizing:
   - Files with coverage below the threshold (sort ascending by coverage %).
   - Files with high complexity but low coverage (use cyclomatic complexity if available).
   - Recently modified files with decreasing coverage trends.
   - Public API functions and exported modules lacking any tests.
4. Analyze uncovered branches specifically:
   - Find `if/else` blocks where only one branch is tested.
   - Identify `switch/case` statements with missing case coverage.
   - Locate error handling paths (`catch`, `except`) never exercised.
   - Check `||` and `&&` short-circuit conditions.
5. Generate a prioritized action plan:
   - List top 10 files needing coverage improvement with specific line ranges.
   - Suggest test scenarios for each uncovered branch.
   - Estimate effort (small/medium/large) for each coverage improvement.
6. Compare current coverage against the previous commit or baseline:
   - Calculate coverage delta per file.
   - Flag files where coverage decreased.
   - Verify new code added since baseline has adequate coverage.
7. Write coverage enforcement configuration (coverage thresholds in Jest config, `.coveragerc`, or CI checks).

## Output

- Coverage summary report with overall and per-file metrics
- Prioritized list of uncovered code paths with file:line references
- Coverage delta report comparing against baseline
- Suggested test cases for top coverage gaps
- Coverage threshold configuration file for CI enforcement

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Coverage report shows 0% | Tests ran but coverage instrumentation was not enabled | Verify `--coverage` flag is passed; check that source files are not excluded by config |
| Coverage includes `node_modules` | Coverage collection scope too broad | Add `collectCoverageFrom` in Jest config; set `--cov=src` in pytest; exclude vendor dirs |
| Branch coverage much lower than line coverage | Conditional logic is only partially tested | Write tests for both truthy and falsy conditions on each branch; focus on edge cases |
| Coverage drops after refactor | New code added without corresponding tests | Set `coverageThreshold` with `global` minimums; add `--changedSince` for incremental checks |
| Flaky coverage numbers between runs | Non-deterministic test execution skipping code paths | Sort tests deterministically; run coverage with `--runInBand` for consistent results |

## Examples

**Jest coverage configuration with thresholds:**
```json
{
  "jest": {
    "coverageThreshold": {
      "global": {
        "branches": 70,
        "functions": 80,
        "lines": 80,
        "statements": 80
      },
      "src/utils/": {
        "branches": 90,
        "lines": 95
      }
    },
    "collectCoverageFrom": [
      "src/**/*.{ts,tsx}",
      "!src/**/*.d.ts",
      "!src/**/index.ts"
    ]
  }
}
```

**Coverage gap analysis output:**
```
Coverage Gaps (sorted by impact):
1. src/auth/oauth.ts        Lines: 45%  Branches: 30%  [Lines 42-67, 89-103 uncovered]
   Suggestion: Add tests for token refresh failure and expired session handling
2. src/api/middleware.ts     Lines: 62%  Branches: 41%  [Lines 28-35, 71-80 uncovered]
   Suggestion: Test rate limiting edge cases and malformed header handling
3. src/utils/parser.ts       Lines: 71%  Branches: 55%  [Lines 112-130 uncovered]
   Suggestion: Test malformed input, empty string, and encoding edge cases
```

## Resources

- Istanbul/nyc: https://istanbul.js.org/
- c8 (Node.js native coverage): https://github.com/bcoe/c8
- coverage.py: https://coverage.readthedocs.io/
- JaCoCo: https://www.jacoco.org/jacoco/
- Go test coverage: https://go.dev/blog/cover
- Code coverage best practices: https://testing.googleblog.com/2020/08/code-coverage-best-practices.html