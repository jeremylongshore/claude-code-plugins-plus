---
name: track-regression
description: Track and run regression tests for existing functionality
shortcut: reg
---
# Regression Test Tracker

Track critical tests and ensure new changes don't break existing functionality.

## Purpose

Maintain stability by:
- **Tracking critical tests** - Mark tests for regression suite
- **Automated execution** - Run before deployments
- **Change impact analysis** - Which tests affected by changes
- **Test history** - Track pass/fail over time
- **Flaky test detection** - Identify unreliable tests

## Usage

```bash
/track-regression                    # Run regression suite
/track-regression --mark             # Mark current test as regression
/track-regression --history          # Show test history
/reg                                 # Shortcut
```

## Regression Suite Management

Tag tests as regression tests:

```javascript
// Jest
describe('User Login', () => {
  it('[REGRESSION] should login with valid credentials', async () => {
    // Critical login test
  });
});

// pytest
@pytest.mark.regression
def test_payment_processing():
    # Critical payment test
    pass
```

## Report Format

```
Regression Test Report
======================
Date: 2025-10-11
Suite: Full Regression
Tests: 45 critical tests
Duration: 3m 42s

Results: 44/45 passed (97.8%)

FAILED:
   test_checkout_with_coupon
     Last passed: 2025-10-09
     Failures: 2 consecutive
     Introduced by: commit abc123f

Flaky Tests Detected:
  ️ test_email_delivery
     Pass rate: 85% (17/20 recent runs)
     Recommendation: Investigate timing issues

Impact Analysis:
  Changed files: src/api/orders.js
  Potentially affected: 8 tests
  Recommended: Run full order test suite
```

## Best Practices

- Tag critical business flows
- Run before every deployment
- Keep regression suite fast (<5 min)
- Monitor for flaky tests
- Update when requirements change
