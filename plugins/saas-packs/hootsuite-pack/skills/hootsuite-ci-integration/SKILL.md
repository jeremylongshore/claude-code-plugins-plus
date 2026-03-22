---
name: hootsuite-ci-integration
description: |
  Configure Hootsuite CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Hootsuite tests into your build process.
  Trigger with phrases like "hootsuite CI", "hootsuite GitHub Actions",
  "hootsuite automated tests", "CI hootsuite".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media]
compatible-with: claude-code
---

# Hootsuite CI Integration

## Instructions

### GitHub Actions Workflow

```yaml
name: Hootsuite Integration
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm test  # Mocked tests, no API access needed

  integration:
    if: github.ref == 'refs/heads/main'
    needs: test
    runs-on: ubuntu-latest
    env:
      HOOTSUITE_CLIENT_ID: ${{ secrets.HOOTSUITE_CLIENT_ID }}
      HOOTSUITE_CLIENT_SECRET: ${{ secrets.HOOTSUITE_CLIENT_SECRET }}
      HOOTSUITE_REFRESH_TOKEN: ${{ secrets.HOOTSUITE_REFRESH_TOKEN }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - name: Refresh token and test API
        run: node scripts/test-api-connection.js
```

### Configure Secrets

```bash
gh secret set HOOTSUITE_CLIENT_ID --body "client_id"
gh secret set HOOTSUITE_CLIENT_SECRET --body "client_secret"
gh secret set HOOTSUITE_REFRESH_TOKEN --body "refresh_token"
```

## Resources

- [GitHub Actions](https://docs.github.com/en/actions)

## Next Steps

For deployment, see `hootsuite-deploy-integration`.
