---
name: running-smoke-tests
description: |
  Execute fast smoke tests validating critical functionality after deployment.
  Use when performing specialized testing.
  Trigger with phrases like "run smoke tests", "quick validation", or "test critical paths".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:smoke-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Smoke Test Runner

## Overview

Execute fast, high-confidence smoke tests that validate critical application functionality after deployment or build. Smoke tests verify that the application starts, core user flows work, and key integrations respond -- without running the full test suite. Designed to complete in under 60 seconds, providing rapid go/no-go feedback for deployments. Supports HTTP health checks, Playwright page loads, CLI command verification, and database connectivity checks.

## Prerequisites

- Application deployed and accessible at a known URL or running locally
- HTTP client available (`curl`, `wget`, `node-fetch`, or Playwright)
- List of critical endpoints and user flows to validate
- Expected response codes and content patterns for each check
- CI/CD pipeline hook for post-deployment validation

## Instructions

1. Identify the critical paths that constitute a "working" application:
   - Health check endpoint returns 200 with expected body.
   - Homepage loads and contains key UI elements.
   - Authentication flow succeeds with test credentials.
   - Primary API endpoint returns valid data.
   - Database connection is active and responding.
2. Create a smoke test configuration listing each check:
   - URL or command to execute.
   - Expected HTTP status code (200, 301, etc.).
   - Response body pattern to match (substring or regex).
   - Maximum acceptable response time (e.g., 3 seconds).
3. Write the smoke test suite as a lightweight script or test file:
   - Use `curl` for HTTP checks or Playwright for browser-based checks.
   - Run checks sequentially for simplicity (parallel for speed if independent).
   - Fail fast on the first critical failure.
   - Log each check result with pass/fail, response time, and status code.
4. Implement timeout guards:
   - Set a global timeout of 60 seconds for the entire smoke suite.
   - Set per-check timeouts of 5-10 seconds.
   - Treat timeouts as failures, not retries.
5. Add deployment-gate integration:
   - On success: proceed with deployment promotion or traffic shifting.
   - On failure: trigger rollback and send alert notification.
   - Report results to CI/CD dashboard and Slack/Teams webhook.
6. Store smoke test results as CI artifacts for audit trail.
7. Schedule periodic smoke runs (every 5 minutes in production) as synthetic monitoring.

## Output

- Smoke test script (`scripts/smoke-test.sh` or `tests/smoke.test.ts`)
- Pass/fail result for each critical check with response times
- Deployment gate verdict (PASS or FAIL with reason)
- CI artifact with timestamped smoke test log
- Alert payload for failed checks (Slack webhook, PagerDuty, etc.)

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Connection refused | Application not yet ready after deployment | Add a startup wait with exponential backoff (max 30 seconds) before running smoke tests |
| 503 Service Unavailable | Application is starting or behind a load balancer draining | Retry with 2-second delay up to 3 times; check load balancer health check status |
| Unexpected redirect (301/302) | URL changed or SSL redirect not accounted for | Follow redirects with `curl -L`; update expected URLs in smoke config |
| Content mismatch | Page content changed but smoke test pattern is too specific | Use broad patterns (check for `<title>` or key element IDs, not exact text) |
| Timeout on database check | Database migration running or connection pool exhausted | Increase timeout for database checks; verify migration completed before smoke tests |

## Examples

**Shell-based smoke test script:**
```bash
#!/bin/bash
set -e
BASE_URL="${1:-http://localhost:3000}"
PASS=0; FAIL=0

check() {
  local name="$1" url="$2" expected="$3"
  status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$url")
  if [ "$status" = "$expected" ]; then
    echo "PASS: $name (HTTP $status)"
    ((PASS++))
  else
    echo "FAIL: $name (expected $expected, got $status)"
    ((FAIL++))
  fi
}

check "Health check" "$BASE_URL/health" "200"
check "Homepage" "$BASE_URL/" "200"
check "API status" "$BASE_URL/api/status" "200"
check "Login page" "$BASE_URL/login" "200"

echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] || exit 1
```

**Playwright smoke test:**
```typescript
import { test, expect } from '@playwright/test';

test('homepage loads with navigation', async ({ page }) => {
  await page.goto('/', { timeout: 10000 });
  await expect(page.locator('nav')).toBeVisible();
  await expect(page).toHaveTitle(/My App/);
});

test('API health endpoint responds', async ({ request }) => {
  const response = await request.get('/api/health');
  expect(response.ok()).toBeTruthy();
  expect(await response.json()).toHaveProperty('status', 'ok');
});
```

## Resources

- Smoke testing methodology: https://martinfowler.com/bliki/SmokeTest.html
- Playwright API testing: https://playwright.dev/docs/api-testing
- curl documentation: https://curl.se/docs/manpage.html
- GitHub Actions deployment gates: https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment
