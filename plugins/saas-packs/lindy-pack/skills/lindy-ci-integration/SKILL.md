---
name: lindy-ci-integration
description: |
  Configure CI/CD pipelines for testing Lindy AI agent integrations.
  Use when setting up automated testing, configuring GitHub Actions
  for webhook receiver tests, or validating agent connectivity in CI.
  Trigger with phrases like "lindy CI", "lindy GitHub Actions",
  "lindy automated tests", "CI lindy pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, testing, ci-cd]

---
# Lindy CI Integration

## Overview
Lindy agents run on Lindy's managed platform — CI/CD tests your **integration code**:
webhook receivers, callback handlers, and application logic that interacts with Lindy
agents. Test webhook signature verification, payload processing, and error handling
without hitting live Lindy endpoints.

## Prerequisites
- GitHub repository with Actions enabled
- Lindy API key and webhook secret stored as GitHub secrets
- Node.js project with webhook receiver code
- Completed `lindy-install-auth` setup

## Instructions

### Step 1: Store Secrets in GitHub
```bash
gh secret set LINDY_API_KEY --body "lnd_live_xxxxxxxxxxxx"
gh secret set LINDY_WEBHOOK_SECRET --body "whsec_xxxxxxxxxxxx"
```

### Step 2: Create GitHub Actions Workflow
```yaml
# .github/workflows/lindy-integration.yml
name: Lindy Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci

      - name: Run unit tests
        run: npm test
        env:
          LINDY_WEBHOOK_SECRET: ${{ secrets.LINDY_WEBHOOK_SECRET }}

      - name: Validate webhook handler
        run: npm run test:webhook

      - name: Connectivity check (non-blocking)
        continue-on-error: true
        run: |
          curl -s -o /dev/null -w "%{http_code}" \
            -X POST "https://public.lindy.ai/api/v1/webhooks/health" \
            -H "Authorization: Bearer ${{ secrets.LINDY_API_KEY }}"
```

### Step 3: Write Webhook Handler Tests
```typescript
// __tests__/webhook-handler.test.ts
import { describe, it, expect, vi } from 'vitest';
import request from 'supertest';
import { app } from '../src/server';

describe('Lindy Webhook Handler', () => {
  const VALID_SECRET = process.env.LINDY_WEBHOOK_SECRET || 'test-secret';

  it('rejects requests without auth header', async () => {
    const res = await request(app)
      .post('/lindy/callback')
      .send({ event: 'test' });
    expect(res.status).toBe(401);
  });

  it('rejects requests with wrong auth token', async () => {
    const res = await request(app)
      .post('/lindy/callback')
      .set('Authorization', 'Bearer wrong-token')
      .send({ event: 'test' });
    expect(res.status).toBe(401);
  });

  it('accepts requests with valid auth token', async () => {
    const res = await request(app)
      .post('/lindy/callback')
      .set('Authorization', `Bearer ${VALID_SECRET}`)
      .set('Content-Type', 'application/json')
      .send({
        taskId: 'task_123',
        status: 'completed',
        result: { summary: 'Test result' },
      });
    expect(res.status).toBe(200);
    expect(res.body.received).toBe(true);
  });

  it('handles malformed payload gracefully', async () => {
    const res = await request(app)
      .post('/lindy/callback')
      .set('Authorization', `Bearer ${VALID_SECRET}`)
      .set('Content-Type', 'application/json')
      .send('not-json');
    expect(res.status).toBeLessThan(500);
  });

  it('processes webhook payload fields correctly', async () => {
    const payload = {
      taskId: 'task_456',
      status: 'completed',
      result: {
        classification: 'billing',
        sentiment: 'neutral',
        summary: 'Customer asks about invoice #789',
      },
    };

    const res = await request(app)
      .post('/lindy/callback')
      .set('Authorization', `Bearer ${VALID_SECRET}`)
      .set('Content-Type', 'application/json')
      .send(payload);

    expect(res.status).toBe(200);
  });
});
```

### Step 4: Add Smoke Test for Live Connectivity
```typescript
// __tests__/connectivity.test.ts
import { describe, it, expect } from 'vitest';

describe('Lindy Connectivity (smoke)', () => {
  it('can reach Lindy webhook endpoint', async () => {
    const webhookUrl = process.env.LINDY_WEBHOOK_URL;
    if (!webhookUrl) {
      console.warn('LINDY_WEBHOOK_URL not set, skipping connectivity test');
      return;
    }

    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.LINDY_WEBHOOK_SECRET}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ test: true, ci: true }),
    });

    expect(response.ok).toBe(true);
  });
});
```

### Step 5: PR Status Check
```yaml
# Add to existing workflow
      - name: Post test results
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const status = '${{ job.status }}' === 'success' ? 'Passed' : 'Failed';
            if (context.payload.pull_request) {
              github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.payload.pull_request.number,
                body: `Lindy Integration Tests: **${status}**`
              });
            }
```

## Test Categories

| Category | What It Tests | Requires Live Lindy? |
|----------|-------------|---------------------|
| Auth verification | Webhook signature checking | No |
| Payload processing | Data extraction and transformation | No |
| Error handling | Malformed input, edge cases | No |
| Connectivity | Webhook endpoint reachability | Yes (non-blocking) |
| End-to-end | Full trigger -> callback cycle | Yes |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found in CI | Not configured | `gh secret set LINDY_WEBHOOK_SECRET` |
| Connectivity test fails | Lindy endpoint unreachable in CI | Mark as `continue-on-error: true` |
| Tests timeout | Network latency | Set `timeout-minutes: 10` on job |
| Flaky live tests | Lindy processing delay | Add retry logic or mock external calls |

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vitest Documentation](https://vitest.dev)
- [Lindy Webhooks](https://docs.lindy.ai/skills/by-lindy/webhooks)

## Next Steps
Proceed to `lindy-deploy-integration` for deployment automation.
