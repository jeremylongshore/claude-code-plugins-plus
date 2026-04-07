---
name: fathom-ci-integration
description: |
  Test Fathom integrations in CI/CD pipelines.
  Trigger with phrases like "fathom CI", "fathom github actions", "test fathom pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom CI Integration

## Overview

Set up CI/CD for Fathom meeting intelligence integrations: run unit tests with mocked transcript and action-item responses on every PR, validate live API connectivity against the Fathom meetings endpoint on merge to main. Fathom provides AI-generated meeting summaries, transcripts, and action items, so CI pipelines focus on verifying data parsing logic and webhook handling for real-time meeting events.

## GitHub Actions Workflow

```yaml
# .github/workflows/fathom-ci.yml
name: Fathom CI
on:
  pull_request:
    paths: ['src/fathom/**', 'tests/**']
  push:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm test -- --reporter=verbose

  integration-tests:
    if: github.ref == 'refs/heads/main'
    needs: unit-tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run test:integration
        env:
          FATHOM_API_KEY: ${{ secrets.FATHOM_API_KEY }}
```

## Mock-Based Unit Tests

```typescript
// tests/fathom-service.test.ts
import { describe, it, expect, vi } from 'vitest';
import { extractActionItems } from '../src/fathom-service';

const mockMeeting = {
  id: 'mtg_abc123',
  title: 'Sprint Planning',
  date: '2026-04-01T10:00:00Z',
  transcript: 'We need to fix the login bug by Friday...',
  action_items: [
    { assignee: 'Alice', task: 'Fix login bug', due: '2026-04-05' },
    { assignee: 'Bob', task: 'Update API docs', due: '2026-04-07' },
  ],
};

vi.mock('../src/fathom-client', () => ({
  FathomClient: vi.fn().mockImplementation(() => ({
    getMeeting: vi.fn().mockResolvedValue(mockMeeting),
    listMeetings: vi.fn().mockResolvedValue({ meetings: [mockMeeting], total: 1 }),
  })),
}));

describe('Fathom Service', () => {
  it('extracts action items from meeting transcript', async () => {
    const items = await extractActionItems('mtg_abc123');
    expect(items).toHaveLength(2);
    expect(items[0].assignee).toBe('Alice');
  });
});
```

## Integration Tests

```typescript
// tests/integration/fathom.integration.test.ts
import { describe, it, expect } from 'vitest';

const hasKey = !!process.env.FATHOM_API_KEY;

describe.skipIf(!hasKey)('Fathom Live API', () => {
  it('lists recent meetings', async () => {
    const res = await fetch('https://api.fathom.video/v1/meetings?limit=1', {
      headers: { Authorization: `Bearer ${process.env.FATHOM_API_KEY}` },
    });
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toHaveProperty('meetings');
  });
});
```

## Error Handling

| CI Issue | Cause | Fix |
|----------|-------|-----|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key at fathom.video settings |
| Empty meetings list | No recordings in account | Create a test meeting or use sandbox account |
| Transcript parsing fails | Meeting still processing | Add retry with 30s delay for recent meetings |
| Webhook signature mismatch | Wrong signing secret in CI | Verify `FATHOM_WEBHOOK_SECRET` matches dashboard config |
| Rate limit (429) | Too many API calls in tests | Add request throttling between test cases |

## Resources

- [Fathom API Documentation](https://fathom.video/api)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

## Next Steps

For deployment, see `fathom-deploy-integration`.
