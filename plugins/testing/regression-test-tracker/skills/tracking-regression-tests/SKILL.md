---
name: tracking-regression-tests
description: |
  Track and manage regression test suites across releases.
  Use when performing specialized testing.
  Trigger with phrases like "track regressions", "manage regression suite", or "validate against baseline".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:regression-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Regression Test Tracker

## Overview

Track, manage, and maintain regression test suites across releases to ensure previously fixed bugs stay fixed and existing features remain stable. Maps regression tests to bug tickets, monitors test health over time, and identifies gaps where fixed bugs lack corresponding regression tests.

## Prerequisites

- Test framework with tagging or marking support (`@tag`, `pytest.mark`, JUnit `@Tag`)
- Bug tracking system with issue IDs (GitHub Issues, Jira, Linear)
- Git history accessible for correlating bug fixes with test additions
- Existing test suite with named test cases
- CI pipeline producing test result artifacts (JUnit XML or JSON)

## Instructions

1. Scan the codebase with Grep for bug-fix commits by searching commit messages for patterns like `fix:`, `bugfix`, `closes #`, or Jira ticket IDs.
2. For each bug-fix commit, check whether a corresponding regression test exists:
   - Search test files for the bug ticket ID in test names, comments, or tags.
   - Verify the test exercises the specific code path that was fixed.
   - Flag fixes without regression tests as coverage gaps.
3. Create a regression test inventory file (`regression-tests.json` or `regression-tests.md`) mapping:
   - Bug ticket ID to test file and test name.
   - Severity of the original bug (critical, high, medium, low).
   - Date the regression test was added.
   - Current test status (passing, failing, skipped).
4. Tag existing regression tests with metadata for traceability:
   - Jest: Add `// @regression BUG-123` comments or use `describe.each` with ticket data.
   - pytest: Apply `@pytest.mark.regression` and `@pytest.mark.bug("BUG-123")` markers.
   - JUnit: Use `@Tag("regression")` and `@DisplayName("BUG-123: description")`.
5. Generate a regression coverage report showing:
   - Total bugs fixed vs. bugs with regression tests (coverage percentage).
   - Untested regressions ranked by severity.
   - Tests that have become flaky or were disabled.
6. Set up a CI check that fails the build if a bug-fix PR does not include at least one regression test.
7. Schedule periodic audits (weekly or per-release) to verify all regression tests still pass and remain relevant.

## Output

- Regression test inventory file mapping bugs to tests
- Tagged test files with regression markers and ticket references
- Coverage gap report listing bug fixes without regression tests
- CI configuration for regression test enforcement
- Release readiness checklist based on regression suite pass rate

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Regression test passes but bug reappears | Test does not cover the exact failure condition | Review the original bug report; update the test to assert against the specific edge case |
| Orphaned regression tags | Bug ticket was closed as duplicate or invalid | Audit tags quarterly; remove or reassign tests for invalid tickets |
| Regression test consistently skipped | Test marked as `skip` due to environment issues | Fix the environment dependency or convert to an integration test with proper setup |
| False coverage gap | Bug was fixed by a refactor that removed the vulnerable code path | Mark as "resolved by removal" in the inventory; add a comment explaining why no test is needed |
| Flaky regression test | Non-deterministic timing or data dependency | Stabilize with retries, fixed seeds, or mocked clocks; tag as `@flaky` for monitoring |

## Examples

**pytest regression test with marker:**
```python
import pytest

@pytest.mark.regression
@pytest.mark.bug("GH-1042")  # 1042 = configured value
def test_csv_export_handles_unicode_characters():
    """Regression: GH-1042 -- CSV export crashed on non-ASCII names."""
    result = export_csv([{"name": "Rene"}])
    assert "Rene" in result
    assert result.startswith("name\n")
```

**Jest regression test with ticket reference:**
```typescript
describe('BUG-789: Cart total calculation', () => {  # 789 = configured value
  it('applies percentage discount before tax', () => {
    const cart = createCart([{ price: 100, qty: 2 }]);
    cart.applyDiscount({ type: 'percent', value: 10 });
    expect(cart.subtotal).toBe(180);
    expect(cart.tax).toBe(18); // 10% tax on discounted subtotal
  });
});
```

**Regression inventory entry:**
```json
{
  "BUG-1042": {  # 1042 = configured value
    "test_file": "tests/test_export.py::test_csv_export_handles_unicode_characters",
    "severity": "high",
    "added": "2026-01-15",  # 2026 year
    "status": "passing"
  }
}
```

## Resources

- pytest markers: https://docs.pytest.org/en/stable/how-to/mark.html
- JUnit 5 tags: https://junit.org/junit5/docs/current/user-guide/#writing-tests-tagging-and-filtering
- Jest describe/test organization: https://jestjs.io/docs/api#describename-fn
- Regression testing best practices: https://martinfowler.com/bliki/SelfTestingCode.html