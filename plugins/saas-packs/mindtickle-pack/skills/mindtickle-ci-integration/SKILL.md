---
name: mindtickle-ci-integration
description: 'Ci Integration for MindTickle.

  Trigger: "mindtickle ci integration".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- mindtickle
- sales
compatibility: Designed for Claude Code
---
# MindTickle CI Integration

## Overview

Configure CI pipelines that validate MindTickle sales enablement API integrations using a two-tier testing strategy. Unit tests mock the MindTickle REST client to verify course enrollment, quiz scoring, and user progress logic without consuming API calls. Integration tests run on main-branch merges with a real Bearer token and company ID to confirm course listing, user search, and completion tracking against the live MindTickle API. The dual-header auth pattern (API key plus company ID) requires special CI secret management to avoid silent authentication failures.

## GitHub Actions Workflow

```yaml
# .github/workflows/mindtickle-tests.yml
name: MindTickle API Tests
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run lint && npm run typecheck
      - run: npm test -- --testPathPattern=unit  # No API key or company ID needed

  integration-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm test -- --testPathPattern=integration
        env:
          MINDTICKLE_API_KEY: ${{ secrets.MINDTICKLE_API_KEY }}
          MINDTICKLE_COMPANY_ID: ${{ secrets.MINDTICKLE_COMPANY_ID }}
```

## Mock-Based Unit Tests

```typescript
// tests/unit/course-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { enrollUser } from '../../src/services/course-service';
import * as mtClient from '../../src/lib/mindtickle-client';

vi.mock('../../src/lib/mindtickle-client');

describe('CourseService', () => {
  it('enrolls a user in a training course', async () => {
    vi.mocked(mtClient.post).mockResolvedValue({
      enrollment_id: 'enr-3390',
      user_id: 'usr-512',
      course_id: 'crs-77',
      status: 'enrolled',
      enrolled_at: '2026-04-01T10:00:00Z',
    });

    const result = await enrollUser('usr-512', 'crs-77');
    expect(result.status).toBe('enrolled');
    expect(mtClient.post).toHaveBeenCalledWith('/courses/crs-77/enrollments', {
      user_id: 'usr-512',
    });
  });
});
```

## Integration Tests

```typescript
// tests/integration/user-progress.test.ts
import { describe, it, expect } from 'vitest';
import { MindTickleClient } from '../../src/lib/mindtickle-client';

const canRun = process.env.MINDTICKLE_API_KEY && process.env.MINDTICKLE_COMPANY_ID;

describe.skipIf(!canRun)('MindTickle User Progress (live API)', () => {
  const client = new MindTickleClient({
    apiKey: process.env.MINDTICKLE_API_KEY!,
    companyId: process.env.MINDTICKLE_COMPANY_ID!,
  });

  it('retrieves course completion stats for a user', async () => {
    const users = await client.get('/users', { limit: 1 });
    expect(users.length).toBeGreaterThan(0);

    const progress = await client.get(`/users/${users[0].id}/progress`);
    expect(progress).toHaveProperty('courses_completed');
    expect(typeof progress.courses_completed).toBe('number');
  });
});
```

## CI Cost Management

```typescript
// tests/helpers/api-budget.ts
let callCount = 0;
const MAX_CALLS_PER_RUN = 30; // MindTickle API has per-company rate limits

export function trackApiCall(): void {
  callCount++;
  if (callCount > MAX_CALLS_PER_RUN) {
    throw new Error(
      `CI API budget exceeded: ${callCount}/${MAX_CALLS_PER_RUN} calls. ` +
      'MindTickle enforces per-company rate limits — reduce test scope or paginate less.'
    );
  }
}

export function getCallCount(): number { return callCount; }
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| 401 Unauthorized | Missing or invalid Bearer token | Regenerate `MINDTICKLE_API_KEY` in MindTickle admin and update GitHub Secrets |
| 403 Forbidden | Company ID mismatch or insufficient permissions | Verify `MINDTICKLE_COMPANY_ID` matches the API key's org; check API scope |
| Empty user list | Company has no users in sandbox instance | Provision test users via `POST /users` in a `beforeAll` setup hook |
| Quiz scores return null | Course has no quizzes configured | Use a known test course ID with at least one quiz module |
| Integration tests silently pass | Both env vars undefined so `skipIf` triggers | Add a CI step that asserts secrets are set: `test -n "$MINDTICKLE_API_KEY"` |

## Resources

- [MindTickle Platform Integrations](https://www.mindtickle.com/platform/integrations/)
- [GitHub Actions Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

See `mindtickle-deploy-integration`.
