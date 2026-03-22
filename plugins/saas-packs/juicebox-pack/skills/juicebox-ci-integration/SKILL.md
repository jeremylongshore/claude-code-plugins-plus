---
name: juicebox-ci-integration
description: |
  Configure Juicebox CI/CD.
  Trigger: "juicebox ci", "juicebox pipeline".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox CI Integration

## GitHub Actions
```yaml
name: Juicebox Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test
  integration:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run test:integration
        env:
          JUICEBOX_API_KEY: ${{ secrets.JUICEBOX_API_KEY }}
```

## Resources
- [Juicebox Docs](https://docs.juicebox.work)

## Next Steps
See `juicebox-deploy-integration`.
