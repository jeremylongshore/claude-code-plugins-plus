---
name: grammarly-ci-integration
description: |
  Configure Grammarly CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Grammarly tests into your build process.
  Trigger with phrases like "grammarly CI", "grammarly GitHub Actions",
  "grammarly automated tests", "CI grammarly".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly CI Integration

## Instructions

### GitHub Actions — Content Quality Gate

```yaml
name: Content Quality
on: [push, pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    env:
      GRAMMARLY_CLIENT_ID: ${{ secrets.GRAMMARLY_CLIENT_ID }}
      GRAMMARLY_CLIENT_SECRET: ${{ secrets.GRAMMARLY_CLIENT_SECRET }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - name: Score documentation
        run: node scripts/score-docs.js
```

```bash
gh secret set GRAMMARLY_CLIENT_ID --body "client_id"
gh secret set GRAMMARLY_CLIENT_SECRET --body "client_secret"
```

## Resources

- [GitHub Actions](https://docs.github.com/en/actions)

## Next Steps

For deployment, see `grammarly-deploy-integration`.
