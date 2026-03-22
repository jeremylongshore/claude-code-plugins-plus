---
name: hubspot-ci-integration
description: |
  Configure CI/CD pipelines for HubSpot integrations with GitHub Actions.
  Use when setting up automated testing, configuring CI with HubSpot secrets,
  or integrating HubSpot API tests into your build process.
  Trigger with phrases like "hubspot CI", "hubspot GitHub Actions",
  "hubspot automated tests", "CI hubspot", "hubspot pipeline test".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot CI Integration

## Overview

Set up GitHub Actions CI/CD for HubSpot integrations with unit tests, integration tests against a developer test account, and secret management.

## Prerequisites

- GitHub repository with Actions enabled
- HubSpot developer test account token
- npm/pnpm project with test suite

## Instructions

### Step 1: Create GitHub Actions Workflow

```yaml
# .github/workflows/hubspot-ci.yml
name: HubSpot Integration CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

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
      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    # Only run integration tests on main branch pushes
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      HUBSPOT_ACCESS_TOKEN: ${{ secrets.HUBSPOT_TEST_ACCESS_TOKEN }}
      HUBSPOT_PORTAL_ID: ${{ secrets.HUBSPOT_TEST_PORTAL_ID }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Run HubSpot integration tests
        run: HUBSPOT_TEST=true npm run test:integration
      - name: Verify HubSpot connectivity
        run: |
          STATUS=$(curl -so /dev/null -w "%{http_code}" \
            https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
            -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN")
          echo "HubSpot API status: $STATUS"
          [ "$STATUS" = "200" ] || exit 1
```

### Step 2: Configure Secrets

```bash
# Store HubSpot test account credentials
gh secret set HUBSPOT_TEST_ACCESS_TOKEN --body "pat-na1-test-xxxxx"
gh secret set HUBSPOT_TEST_PORTAL_ID --body "12345678"

# For production deployments
gh secret set HUBSPOT_PROD_ACCESS_TOKEN --body "pat-na1-prod-xxxxx"
```

### Step 3: Write CI-Friendly Tests

```typescript
// tests/hubspot.integration.test.ts
import { describe, it, expect, afterAll } from 'vitest';
import * as hubspot from '@hubspot/api-client';

const shouldRun = process.env.HUBSPOT_TEST === 'true';
const createdIds: string[] = [];

describe.skipIf(!shouldRun)('HubSpot Integration', () => {
  const client = new hubspot.Client({
    accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
    numberOfApiCallRetries: 3,
  });

  it('should list contacts', async () => {
    const page = await client.crm.contacts.basicApi.getPage(
      5, undefined, ['email', 'firstname']
    );
    expect(page.results).toBeDefined();
    expect(Array.isArray(page.results)).toBe(true);
  });

  it('should create and archive a test contact', async () => {
    const testEmail = `ci-test-${Date.now()}@example.com`;
    const contact = await client.crm.contacts.basicApi.create({
      properties: {
        email: testEmail,
        firstname: 'CI',
        lastname: 'Test',
      },
      associations: [],
    });
    expect(contact.id).toBeDefined();
    createdIds.push(contact.id);
  });

  it('should search contacts by email', async () => {
    const results = await client.crm.contacts.searchApi.doSearch({
      filterGroups: [{
        filters: [{ propertyName: 'email', operator: 'CONTAINS_TOKEN', value: '*@example.com' }],
      }],
      properties: ['email'],
      limit: 5, after: 0, sorts: [],
    });
    expect(results.total).toBeGreaterThanOrEqual(0);
  });

  it('should list deal pipelines', async () => {
    const pipelines = await client.crm.pipelines.pipelinesApi.getAll('deals');
    expect(pipelines.results.length).toBeGreaterThan(0);
    expect(pipelines.results[0].stages.length).toBeGreaterThan(0);
  });

  // Clean up test data
  afterAll(async () => {
    for (const id of createdIds) {
      try {
        await client.crm.contacts.basicApi.archive(id);
      } catch { /* ignore cleanup errors */ }
    }
  });
});
```

### Step 4: Secret Scanning in CI

```yaml
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan for HubSpot tokens
        run: |
          if grep -rE "pat-[a-z]{2}[0-9]-[a-f0-9-]{36}" \
            --include="*.ts" --include="*.js" --include="*.json" \
            --exclude-dir=node_modules .; then
            echo "::error::HubSpot access token found in source code!"
            exit 1
          fi
      - name: Scan for hardcoded API keys
        run: |
          if grep -rE "hapikey=[a-f0-9-]{36}" \
            --include="*.ts" --include="*.js" .; then
            echo "::error::Deprecated HubSpot API key found!"
            exit 1
          fi
```

## Output

- Unit tests running on every PR (no API credentials needed)
- Integration tests on main branch using test account
- Secret scanning preventing token leaks
- Coverage reports uploaded as artifacts

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found in CI | Missing `gh secret set` | Add secret via GitHub Settings or CLI |
| Integration test flaky | Rate limited on test account | Add `numberOfApiCallRetries: 3` |
| 401 in CI | Token expired or regenerated | Update `HUBSPOT_TEST_ACCESS_TOKEN` secret |
| Test data pollution | Tests not cleaning up | Add `afterAll` cleanup block |

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [HubSpot Developer Test Accounts](https://developers.hubspot.com/docs/guides/apps/developer-test-accounts)

## Next Steps

For deployment patterns, see `hubspot-deploy-integration`.
