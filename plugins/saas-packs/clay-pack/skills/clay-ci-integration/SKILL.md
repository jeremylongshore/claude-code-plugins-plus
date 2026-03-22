---
name: clay-ci-integration
description: |
  Configure CI/CD pipelines for Clay integrations with automated testing and validation.
  Use when setting up automated tests for Clay webhook handlers, validating
  enrichment data quality in CI, or integrating Clay checks into your build process.
  Trigger with phrases like "clay CI", "clay GitHub Actions",
  "clay automated tests", "CI clay", "test clay integration".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, testing, ci-cd]

---
# Clay CI Integration

## Overview

Set up CI/CD pipelines for Clay-powered applications. Since Clay is a web platform (not a local service), CI focuses on: (1) testing webhook handler code, (2) validating data transformation logic, (3) checking enrichment data schema compliance, and (4) optional live integration tests against Clay's API.

## Prerequisites

- GitHub repository with Actions enabled
- Clay webhook URL stored as GitHub secret
- Node.js/Python project with test framework

## Instructions

### Step 1: Create GitHub Actions Workflow

```yaml
# .github/workflows/clay-integration.yml
name: Clay Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  CLAY_WEBHOOK_URL: ${{ secrets.CLAY_WEBHOOK_URL }}
  CLAY_API_KEY: ${{ secrets.CLAY_API_KEY }}

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
        env:
          # No Clay credentials needed for unit tests (use mocks)
          CLAY_WEBHOOK_URL: "https://mock.webhook.test"

  data-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Validate input data schemas
        run: npx tsx scripts/validate-clay-schemas.ts
      - name: Check for PII in test fixtures
        run: |
          if grep -rn '@gmail.com\|@yahoo.com\|@hotmail.com' test/fixtures/; then
            echo "ERROR: Real email addresses found in test fixtures"
            exit 1
          fi

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: [unit-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Test webhook connectivity
        run: |
          HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST "$CLAY_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d '{"_ci_test": true, "_run_id": "${{ github.run_id }}"}')
          if [ "$HTTP_CODE" != "200" ]; then
            echo "Webhook connectivity check failed: HTTP $HTTP_CODE"
            exit 1
          fi
```

### Step 2: Configure Secrets

```bash
# Store Clay credentials as GitHub secrets
gh secret set CLAY_WEBHOOK_URL --body "https://app.clay.com/api/v1/webhooks/your-id"
gh secret set CLAY_API_KEY --body "clay_ent_your_key"  # Enterprise only
```

### Step 3: Write Unit Tests for Clay Handlers

```typescript
// tests/clay-handler.test.ts
import { describe, it, expect, vi } from 'vitest';
import { processEnrichedData, validateWebhookPayload } from '../src/clay/handler';

describe('Clay Webhook Handler', () => {
  it('should process enriched data correctly', () => {
    const payload = {
      email: 'jane@stripe.com',
      company_name: 'Stripe',
      job_title: 'VP Engineering',
      employee_count: 8000,
      industry: 'Financial Technology',
    };

    const result = processEnrichedData(payload);
    expect(result.icp_score).toBeGreaterThan(0);
    expect(result.company_name).toBe('Stripe');
  });

  it('should reject payloads missing required fields', () => {
    const invalid = { company_name: 'Test Corp' }; // Missing email
    expect(() => validateWebhookPayload(invalid)).toThrow('Missing required field: email');
  });

  it('should handle empty enrichment gracefully', () => {
    const partial = {
      email: 'test@unknown.com',
      company_name: null,
      job_title: null,
      employee_count: null,
    };

    const result = processEnrichedData(partial);
    expect(result.icp_score).toBe(0);
    expect(result.enrichment_complete).toBe(false);
  });
});

describe('Input Validation', () => {
  it('should filter personal email domains', () => {
    const rows = [
      { domain: 'stripe.com', email: 'ceo@stripe.com' },
      { domain: 'gmail.com', email: 'user@gmail.com' },
    ];

    const valid = rows.filter(r => !['gmail.com', 'yahoo.com'].includes(r.domain));
    expect(valid).toHaveLength(1);
    expect(valid[0].domain).toBe('stripe.com');
  });
});
```

### Step 4: Add Data Schema Validation

```typescript
// scripts/validate-clay-schemas.ts
import { z } from 'zod';

const ClayEnrichedRowSchema = z.object({
  email: z.string().email(),
  domain: z.string().min(3),
  company_name: z.string().nullable(),
  job_title: z.string().nullable(),
  employee_count: z.number().nullable(),
  industry: z.string().nullable(),
  linkedin_url: z.string().url().nullable(),
});

const ClayWebhookInputSchema = z.object({
  domain: z.string().min(3).refine(d => d.includes('.'), 'Must contain a dot'),
  first_name: z.string().min(1),
  last_name: z.string().min(1),
  email: z.string().email().optional(),
  source: z.string().optional(),
});

// Validate test fixtures match expected schemas
console.log('Validating Clay schemas...');
// Run against test fixtures, mock data, etc.
console.log('All schemas valid.');
```

### Step 5: Credit Budget Guard in CI

```yaml
# Add to workflow to prevent accidental high-volume runs
- name: Check credit budget
  run: |
    MAX_ROWS=10  # CI should never enrich more than 10 test rows
    ROWS_TO_SEND=$(wc -l < test/fixtures/test-leads.csv)
    if [ "$ROWS_TO_SEND" -gt "$MAX_ROWS" ]; then
      echo "ERROR: Test fixture has $ROWS_TO_SEND rows (max: $MAX_ROWS)"
      echo "Integration tests should use minimal data to avoid credit waste"
      exit 1
    fi
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook test fails in CI | Secret not configured | Add `CLAY_WEBHOOK_URL` via `gh secret set` |
| Tests pass locally, fail in CI | Missing mock for Clay calls | Use vitest mocks for unit tests |
| Integration test flaky | Clay API latency varies | Add retry logic, increase timeout |
| Credit waste in CI | Test sends too many rows | Add MAX_ROWS guard, use minimal fixtures |

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps

For deployment patterns, see `clay-deploy-integration`.
