---
name: gen-report
description: Generate comprehensive test reports with coverage and trends
shortcut: rpt
---
# Test Report Generator

Create detailed, stakeholder-friendly test reports with coverage metrics, test trends, failure analysis, and exportable formats (HTML, PDF, JSON).

## What You Do

1. **Aggregate Test Results**: Collect results from all test frameworks
2. **Calculate Metrics**: Coverage, pass rate, duration, trends
3. **Generate Reports**: HTML dashboards, PDF summaries, JSON exports
4. **Trend Analysis**: Compare with previous runs, identify regressions

## Output Example

```markdown
## Test Execution Report

**Date:** 2025-10-11
**Branch:** main
**Commit:** abc123

### Summary
- Total Tests: 1,247
- Passed: 1,198 (96.1%)
- Failed: 32 (2.6%)
- Skipped: 17 (1.4%)
- Duration: 4m 32s

### Coverage
- Statements: 87.3% (↑ 2.1%)
- Branches: 79.5% (↑ 1.3%)
- Functions: 91.2% (↓ 0.5%)
- Lines: 86.8% (↑ 1.9%)

### Failed Tests (32)
1. `UserService.test.ts` - Login validation
2. `PaymentAPI.test.ts` - Refund processing

### Trend (Last 7 Days)
```
Day       | Tests | Pass Rate | Coverage
---------|-------|-----------|----------
Oct 11   | 1,247 | 96.1%     | 87.3%
Oct 10   | 1,235 | 94.8%     | 85.2%
Oct 09   | 1,228 | 95.2%     | 84.9%
```
