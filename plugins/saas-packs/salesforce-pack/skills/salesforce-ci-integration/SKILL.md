---
name: salesforce-ci-integration
description: |
  Configure Salesforce CI/CD with GitHub Actions, SFDX deployments, and Apex testing.
  Use when setting up automated testing, configuring CI pipelines for metadata deployment,
  or integrating Salesforce tests into your build process.
  Trigger with phrases like "salesforce CI", "salesforce GitHub Actions",
  "salesforce automated tests", "CI salesforce", "sfdx deploy CI".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(sf:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce CI Integration

## Overview
Set up CI/CD pipelines for Salesforce using GitHub Actions with JWT-based authentication, automated Apex testing, and metadata deployment.

## Prerequisites
- GitHub repository with Actions enabled
- Salesforce Connected App with JWT Bearer flow configured
- RSA key pair (private key stored as GitHub Secret)
- Scratch org or sandbox for test execution

## Instructions

### Step 1: Create GitHub Actions Workflow
Create `.github/workflows/salesforce-ci.yml`:

```yaml
name: Salesforce CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install Salesforce CLI
        run: npm install -g @salesforce/cli

      - name: Authenticate to Salesforce (JWT)
        run: |
          echo "${{ secrets.SF_JWT_KEY }}" > server.key
          sf org login jwt \
            --client-id ${{ secrets.SF_CLIENT_ID }} \
            --jwt-key-file server.key \
            --username ${{ secrets.SF_USERNAME }} \
            --set-default \
            --alias ci-org
          rm server.key

      - name: Validate Metadata Deployment (dry run)
        run: |
          sf project deploy start \
            --target-org ci-org \
            --dry-run \
            --wait 30

      - name: Run Apex Tests
        run: |
          sf apex run test \
            --target-org ci-org \
            --result-format human \
            --code-coverage \
            --wait 20

      - name: Check API Limits
        run: |
          sf limits api display --target-org ci-org --json | \
            jq '.result[] | select(.name == "DailyApiRequests") | "\(.name): \(.remaining)/\(.max)"'

  integration-tests:
    runs-on: ubuntu-latest
    needs: validate
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Run jsforce Integration Tests
        env:
          SF_LOGIN_URL: https://test.salesforce.com
          SF_USERNAME: ${{ secrets.SF_USERNAME }}
          SF_PASSWORD: ${{ secrets.SF_PASSWORD }}
          SF_SECURITY_TOKEN: ${{ secrets.SF_SECURITY_TOKEN }}
        run: npm run test:integration
```

### Step 2: Configure GitHub Secrets
```bash
# JWT private key (from your RSA key pair)
gh secret set SF_JWT_KEY < server.key

# Connected App consumer key
gh secret set SF_CLIENT_ID --body "3MVG9..."

# Integration user credentials
gh secret set SF_USERNAME --body "ci-user@yourcompany.com"
gh secret set SF_PASSWORD --body "password"
gh secret set SF_SECURITY_TOKEN --body "token"
```

### Step 3: Generate JWT Key Pair
```bash
# Generate RSA key pair for JWT Bearer flow
openssl genrsa -out server.key 2048
openssl req -new -x509 -key server.key -out server.crt -days 365 \
  -subj "/CN=Salesforce CI/O=YourCompany"

# Upload server.crt to Connected App in Salesforce Setup:
# Setup > App Manager > Your App > Edit > Use Digital Signatures > Choose File
```

### Step 4: Write Integration Tests
```typescript
import { describe, it, expect } from 'vitest';
import jsforce from 'jsforce';

describe('Salesforce Integration', () => {
  const conn = new jsforce.Connection({
    loginUrl: process.env.SF_LOGIN_URL || 'https://test.salesforce.com',
  });

  beforeAll(async () => {
    await conn.login(
      process.env.SF_USERNAME!,
      process.env.SF_PASSWORD! + process.env.SF_SECURITY_TOKEN!
    );
  });

  it('should query Accounts via SOQL', async () => {
    const result = await conn.query('SELECT Id, Name FROM Account LIMIT 1');
    expect(result.totalSize).toBeGreaterThanOrEqual(0);
    expect(result.done).toBe(true);
  });

  it('should check API limits are not exhausted', async () => {
    const limits = await conn.request('/services/data/v59.0/limits/');
    const remaining = limits.DailyApiRequests.Remaining;
    const max = limits.DailyApiRequests.Max;
    expect(remaining / max).toBeGreaterThan(0.1); // At least 10% remaining
  });

  it('should describe Account sObject', async () => {
    const meta = await conn.sobject('Account').describe();
    expect(meta.name).toBe('Account');
    expect(meta.fields.length).toBeGreaterThan(0);
    expect(meta.fields.find(f => f.name === 'Name')).toBeDefined();
  });
});
```

### Step 5: Metadata Deployment Pipeline
```yaml
# Deploy on merge to main
deploy:
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  needs: [validate, integration-tests]
  steps:
    - uses: actions/checkout@v4
    - name: Install Salesforce CLI
      run: npm install -g @salesforce/cli
    - name: Authenticate
      run: |
        echo "${{ secrets.SF_JWT_KEY_PROD }}" > server.key
        sf org login jwt \
          --client-id ${{ secrets.SF_CLIENT_ID_PROD }} \
          --jwt-key-file server.key \
          --username ${{ secrets.SF_USERNAME_PROD }} \
          --set-default
        rm server.key
    - name: Deploy to Production
      run: |
        sf project deploy start \
          --target-org ${{ secrets.SF_USERNAME_PROD }} \
          --test-level RunLocalTests \
          --wait 30
```

## Output
- JWT-authenticated CI pipeline
- Automated Apex test execution on PR
- Integration tests validating jsforce operations
- Metadata deployment on merge to main
- API limit monitoring in CI

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `INVALID_GRANT` | JWT cert not uploaded or user not pre-authorized | Upload cert to Connected App; add user to pre-authorized profiles |
| Apex test failures | Test data dependencies | Use `@testSetup` methods for test isolation |
| Deploy validation errors | Missing dependencies | Check component dependencies with `sf project deploy report` |
| API limit in CI | Too many test runs/day | Use sandbox instead of production for CI |

## Resources
- [Salesforce CLI JWT Auth](https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_jwt_flow.htm)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Apex Testing Best Practices](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing.htm)

## Next Steps
For deployment patterns, see `salesforce-deploy-integration`.
