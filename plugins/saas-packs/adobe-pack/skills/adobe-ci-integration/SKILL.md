---
name: adobe-ci-integration
description: |
  Configure CI/CD pipelines for Adobe integrations with GitHub Actions,
  including OAuth credential injection, PDF Services testing, Firefly API
  smoke tests, and secret scanning for Adobe credential patterns.
  Trigger with phrases like "adobe CI", "adobe GitHub Actions",
  "adobe automated tests", "CI adobe", "adobe pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe CI Integration

## Overview

Set up CI/CD pipelines for Adobe API integrations with proper credential management, unit/integration test separation, and secret scanning for Adobe-specific credential patterns.

## Prerequisites

- GitHub repository with Actions enabled
- Adobe Developer Console credentials for CI (separate from production)
- npm/pnpm project with vitest configured

## Instructions

### Step 1: Store Adobe Credentials as GitHub Secrets

```bash
# Set OAuth Server-to-Server credentials
gh secret set ADOBE_CLIENT_ID --body "your-ci-client-id"
gh secret set ADOBE_CLIENT_SECRET --body "your-ci-client-secret"
gh secret set ADOBE_SCOPES --body "openid,AdobeID,firefly_api"
```

### Step 2: Create CI Workflow

```yaml
# .github/workflows/adobe-integration.yml
name: Adobe Integration Tests

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
        # Unit tests run with mocked Adobe APIs — no credentials needed

  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan for Adobe credentials
        run: |
          FOUND=0
          # Adobe OAuth client secrets start with p8_
          if grep -rE "p8_[A-Za-z0-9_-]{20,}" --include="*.ts" --include="*.js" --include="*.py" --include="*.json" . 2>/dev/null; then
            echo "::error::Adobe client_secret pattern found in source"
            FOUND=1
          fi
          # Adobe IMS access tokens
          if grep -rE "eyJ[A-Za-z0-9_-]{50,}" --include="*.ts" --include="*.js" . 2>/dev/null; then
            echo "::warning::Potential Adobe access token found"
          fi
          exit $FOUND

  integration-tests:
    needs: [unit-tests, secret-scan]
    runs-on: ubuntu-latest
    # Only run on main branch (uses real API credentials)
    if: github.ref == 'refs/heads/main'
    env:
      ADOBE_CLIENT_ID: ${{ secrets.ADOBE_CLIENT_ID }}
      ADOBE_CLIENT_SECRET: ${{ secrets.ADOBE_CLIENT_SECRET }}
      ADOBE_SCOPES: ${{ secrets.ADOBE_SCOPES }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Verify Adobe OAuth credentials
        run: |
          HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
            'https://ims-na1.adobelogin.com/ims/token/v3' \
            -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES}")
          if [ "$HTTP_CODE" != "200" ]; then
            echo "::error::Adobe OAuth token generation failed (HTTP $HTTP_CODE)"
            exit 1
          fi
          echo "Adobe credentials verified"

      - name: Run integration tests
        run: npm run test:integration
        timeout-minutes: 5
```

### Step 3: Write CI-Friendly Integration Tests

```typescript
// tests/integration/adobe-api.test.ts
import { describe, it, expect } from 'vitest';
import { getAccessToken } from '../../src/adobe/client';

const hasCredentials = !!(
  process.env.ADOBE_CLIENT_ID && process.env.ADOBE_CLIENT_SECRET
);

describe.skipIf(!hasCredentials)('Adobe API Integration', () => {
  it('should generate valid OAuth access token', async () => {
    const token = await getAccessToken();
    expect(token).toBeTruthy();
    expect(token.length).toBeGreaterThan(100);
  }, 10_000);

  it('should call Firefly API health endpoint', async () => {
    const token = await getAccessToken();
    const response = await fetch('https://firefly-api.adobe.io/v3/images/generate', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': process.env.ADOBE_CLIENT_ID!,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt: 'solid blue square',
        n: 1,
        size: { width: 512, height: 512 },
      }),
    });

    // 200 = success, 429 = rate limited (acceptable in CI)
    expect([200, 429]).toContain(response.status);
  }, 30_000);
});
```

### Step 4: Release Workflow with Adobe Validation

```yaml
# .github/workflows/release.yml
on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    env:
      ADOBE_CLIENT_ID: ${{ secrets.ADOBE_CLIENT_ID_PROD }}
      ADOBE_CLIENT_SECRET: ${{ secrets.ADOBE_CLIENT_SECRET_PROD }}
      ADOBE_SCOPES: ${{ secrets.ADOBE_SCOPES }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm test
      - name: Verify Adobe production credentials
        run: npm run test:integration
      - run: npm run build
      - run: npm publish
```

## Output

- Unit test pipeline (no credentials needed)
- Secret scanning for Adobe credential patterns
- Integration tests with real API (main branch only)
- Release workflow with credential validation gate

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `invalid_client` in CI | Wrong secret value | Re-set with `gh secret set` |
| Integration test 429 | Rate limited | Accept 429 as valid CI result |
| Secret scan false positive | Test fixture data | Exclude test directories from scan |
| Timeout on Firefly test | API latency | Increase vitest timeout to 30s |

## Resources

- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)
- [Adobe Developer Console](https://developer.adobe.com/console)

## Next Steps

For deployment patterns, see `adobe-deploy-integration`.
