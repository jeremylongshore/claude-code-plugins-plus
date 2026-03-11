---
name: generating-test-reports
description: |
  Generate comprehensive test reports with metrics, coverage, and visualizations.
  Use when performing specialized testing.
  Trigger with phrases like "generate test report", "create test documentation", or "show test metrics".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:report-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Test Report Generator

## Overview

Generate structured, human-readable test reports from raw test runner output including JUnit XML, Jest JSON, pytest results, and coverage data. Produces Markdown summaries, HTML dashboards, and CI-compatible annotations. Aggregates metrics across test suites to surface pass rates, coverage trends, slowest tests, and flaky test patterns.

## Prerequisites

- Test results in a parseable format (JUnit XML, Jest `--json`, pytest `--junitxml`, or TAP)
- Coverage data files (Istanbul `coverage-summary.json`, `lcov.info`, or `coverage.xml`)
- Node.js or Python available for report generation scripts
- Git history accessible for trend analysis across commits

## Instructions

1. Locate all test result files using Glob patterns (`**/junit.xml`, `**/test-results.json`, `**/coverage/lcov.info`).
2. Parse each result file and extract:
   - Total test count, passed, failed, skipped, and error counts.
   - Execution duration per test suite and per individual test.
   - Failure messages, stack traces, and assertion details.
3. Parse coverage data and extract:
   - Line, branch, function, and statement coverage percentages.
   - Per-file coverage breakdown identifying files below threshold.
   - Uncovered line ranges for targeted improvement.
4. Compute aggregate metrics:
   - Overall pass rate as a percentage.
   - Total execution time and average test duration.
   - Top 10 slowest tests with file paths and durations.
   - Coverage delta compared to the previous commit (if git history is available).
5. Generate a Markdown report with sections for summary, failures, coverage, and performance.
6. Optionally generate an HTML report with sortable tables and coverage heatmaps.
7. Write CI-compatible output (GitHub Actions job summary, GitLab report artifacts, or Slack webhook payload).

## Output

- `test-report.md` -- Markdown summary with pass/fail table, coverage stats, and failure details
- `test-report.html` -- Self-contained HTML report (optional)
- Coverage summary table with per-file breakdown and delta from baseline
- Slowest tests list ranked by execution time
- CI annotation comments on failed test lines (GitHub Actions `::error` format)

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| No test result files found | Tests did not run or output path is incorrect | Verify test runner `--outputFile` or `--junitxml` flag; check the output directory exists |
| Malformed JUnit XML | Test runner crashed mid-output or encoding issues | Validate XML with `xmllint`; re-run failed test suite; check for binary output in XML |
| Coverage data missing | Tests ran without `--coverage` flag | Add `--coverage` to the test command; verify coverage reporter is configured |
| Metric trend unavailable | No previous report to compare against | Generate baseline report first; store reports as CI artifacts for historical comparison |
| Report exceeds GitHub comment limit | Too many failures produce oversized Markdown | Truncate failure details to top 20; link to full report artifact |

## Examples

**Markdown report structure:**
```markdown
## Test Results -- 2026-03-10

| Metric | Value |
|--------|-------|
| Total Tests | 847 |
| Passed | 839 (99.1%) |
| Failed | 5 |
| Skipped | 3 |
| Duration | 42.3s |

### Coverage
| Category | Current | Threshold | Status |
|----------|---------|-----------|--------|
| Lines | 87.2% | 80% | PASS |
| Branches | 74.1% | 70% | PASS |
| Functions | 91.5% | 85% | PASS |

### Failed Tests
1. `src/utils/parser.test.ts` -- "handles malformed input" -- Expected Error but received null
2. `src/api/auth.test.ts` -- "rejects expired tokens" -- Timeout after 5000ms
```

**GitHub Actions job summary integration:**
```bash
cat test-report.md >> "$GITHUB_STEP_SUMMARY"
```

## Resources

- Jest `--json` reporter: https://jestjs.io/docs/cli#--json
- JUnit XML format specification: https://github.com/testmoapp/junitxml
- Istanbul coverage reporters: https://istanbul.js.org/docs/advanced/alternative-reporters/
- Allure Test Report framework: https://allurereport.org/
- GitHub Actions job summaries: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#adding-a-job-summary
