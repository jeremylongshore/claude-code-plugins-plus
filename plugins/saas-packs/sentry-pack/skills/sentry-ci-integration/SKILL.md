---
name: sentry-ci-integration
description: |
  Integrate Sentry with CI/CD pipelines.
  Use when setting up GitHub Actions, GitLab CI, or other CI systems
  with Sentry releases and source maps.
  Trigger with phrases like "sentry github actions", "sentry CI",
  "sentry pipeline", "automate sentry releases".
allowed-tools: Read, Write, Edit, Bash(gh:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry CI Integration

## Overview
Automate Sentry releases and source map uploads in CI/CD pipelines.

## GitHub Actions

### Complete Workflow
```yaml
# .github/workflows/release.yml
name: Release with Sentry

on:
  push:
    branches: [main]

env:
  SENTRY_ORG: your-org
  SENTRY_PROJECT: your-project

jobs:
  build-and-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build
        env:
          SENTRY_RELEASE: ${{ github.sha }}

      - name: Create Sentry Release
        uses: getsentry/action-release@v1
        env:
          SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
        with:
          environment: production
          version: ${{ github.sha }}
          sourcemaps: ./dist

      - name: Deploy
        run: npm run deploy
```

### Source Maps Only
```yaml
- name: Upload Source Maps
  run: |
    npm install -g @sentry/cli
    sentry-cli releases new ${{ github.sha }}
    sentry-cli releases files ${{ github.sha }} upload-sourcemaps ./dist
    sentry-cli releases finalize ${{ github.sha }}
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: your-org
    SENTRY_PROJECT: your-project
```

## GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - build
  - release
  - deploy

variables:
  SENTRY_ORG: your-org
  SENTRY_PROJECT: your-project

build:
  stage: build
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/

sentry-release:
  stage: release
  image: getsentry/sentry-cli
  script:
    - sentry-cli releases new $CI_COMMIT_SHA
    - sentry-cli releases files $CI_COMMIT_SHA upload-sourcemaps ./dist
    - sentry-cli releases set-commits $CI_COMMIT_SHA --auto
    - sentry-cli releases finalize $CI_COMMIT_SHA
    - sentry-cli releases deploys $CI_COMMIT_SHA new -e production
  only:
    - main
```

## CircleCI

```yaml
# .circleci/config.yml
version: 2.1

orbs:
  sentry: sentry-io/sentry-cli@0.1.0

jobs:
  build-and-release:
    docker:
      - image: cimg/node:20.0
    steps:
      - checkout
      - run: npm ci
      - run: npm run build
      - sentry/install_sentry_cli
      - run:
          name: Create Sentry Release
          command: |
            export SENTRY_RELEASE=$(git rev-parse --short HEAD)
            sentry-cli releases new $SENTRY_RELEASE
            sentry-cli releases files $SENTRY_RELEASE upload-sourcemaps ./dist
            sentry-cli releases finalize $SENTRY_RELEASE

workflows:
  deploy:
    jobs:
      - build-and-release:
          context: sentry
```

## Required Secrets

```bash
# Generate auth token at:
# https://sentry.io/settings/auth-tokens/

# GitHub
gh secret set SENTRY_AUTH_TOKEN --body "your-token"

# GitLab
# Settings > CI/CD > Variables
# Add SENTRY_AUTH_TOKEN

# Environment variables needed:
SENTRY_AUTH_TOKEN=your-auth-token
SENTRY_ORG=your-org
SENTRY_PROJECT=your-project
```

## Commit Tracking

```yaml
# Include commits in release
- name: Create Release with Commits
  run: |
    sentry-cli releases new $VERSION
    sentry-cli releases set-commits $VERSION --auto
    sentry-cli releases finalize $VERSION
```

## Deploy Notifications

```yaml
# Notify Sentry of deployment
- name: Notify Deployment
  run: |
    sentry-cli releases deploys $VERSION new \
      --env production \
      --started $(date +%s) \
      --finished $(date +%s)
```

## Resources
- [Sentry CI/CD](https://docs.sentry.io/product/releases/setup/release-automation/)
- [GitHub Action](https://github.com/getsentry/action-release)
