---
name: flyio-ci-integration
description: |
  Configure CI/CD pipelines for Fly.io with GitHub Actions, Docker builds,
  deploy tokens, and automated deployment workflows.
  Trigger: "fly.io CI", "fly.io GitHub Actions", "fly deploy CI/CD".
allowed-tools: Read, Write, Edit, Bash(fly:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io CI Integration

## Overview

Set up CI/CD for Fly.io with GitHub Actions: build Docker images, deploy on push to main, and use deploy tokens for secure automation.

## Instructions

### GitHub Actions Workflow

```yaml
# .github/workflows/fly-deploy.yml
name: Deploy to Fly.io
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
        with: { node-version: '20' }
      - run: npm ci && npm test

  deploy-staging:
    needs: test
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: fly deploy -a my-app-staging --config fly.staging.toml
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_DEPLOY_TOKEN_STAGING }}

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: fly deploy -a my-app
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_DEPLOY_TOKEN }}
      - run: |
          fly status -a my-app
          curl -sf https://my-app.fly.dev/health
```

### Create Deploy Token

```bash
# Scoped to a single app — use this in CI
fly tokens create deploy -a my-app
# Add as GitHub secret: FLY_DEPLOY_TOKEN
```

## Resources

- [Fly.io GitHub Actions](https://fly.io/docs/launch/continuous-deployment/github-actions/)
- [Deploy Tokens](https://fly.io/docs/reference/deploy-tokens/)

## Next Steps

For deployment strategies, see `flyio-deploy-integration`.
