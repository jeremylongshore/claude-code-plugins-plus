---
name: shopify-ci-integration
description: |
  Configure CI/CD pipelines for Shopify apps with GitHub Actions, API version testing,
  and Shopify CLI deployment.
  Use when setting up automated testing, deployment pipelines, or API version monitoring for Shopify apps.
  Trigger with phrases like "shopify CI", "shopify GitHub Actions",
  "shopify automated tests", "CI shopify", "shopify deploy pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify CI Integration

## Overview

Set up CI/CD pipelines for Shopify apps using GitHub Actions, including API version compatibility testing, Shopify CLI deployment, and extension validation.

## Prerequisites

- GitHub repository with Actions enabled
- Shopify Partner account with CLI access
- Test store access token for integration tests

## Instructions

### Step 1: GitHub Actions Workflow

Create a workflow with lint, test, API version check, and deploy jobs.

See [GitHub Actions Workflow](references/github-actions-workflow.md) for the complete `.github/workflows/shopify-ci.yml` file.

### Step 2: Configure Secrets

```bash
# Store these in GitHub repository secrets
gh secret set SHOPIFY_API_KEY --body "your_api_key"
gh secret set SHOPIFY_API_SECRET --body "your_api_secret"
gh secret set SHOPIFY_TEST_STORE --body "your-dev-store.myshopify.com"
gh secret set SHOPIFY_TEST_TOKEN --body "shpat_test_token"
gh secret set SHOPIFY_PARTNERS_TOKEN --body "your_partners_cli_token"
```

### Step 3: Integration Test Structure

Write integration tests that verify store connectivity, required scopes, and rate limit compliance. Tests skip automatically when `SHOPIFY_ACCESS_TOKEN` is not set.

See [Integration Test Structure](references/integration-test-structure.md) for the complete Vitest test file.

## Output

- CI pipeline with lint, typecheck, unit tests, and integration tests
- API version deprecation monitoring
- Automated deployment via Shopify CLI
- Integration tests running against a test store

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `SHOPIFY_PARTNERS_TOKEN` invalid | Token expired | Regenerate at partners.shopify.com |
| Integration tests timeout | Rate limited | Add delays or use test store with Plus |
| API version check fails | Deprecated version | Update to latest supported version |
| Deploy fails | App config mismatch | Run `shopify app config push` first |

## Examples

### Shopify CLI Token for CI

```bash
# Generate a CLI token for CI (no interactive login needed)
# Go to: partners.shopify.com > Settings > CLI tokens
# Create a new token and save as SHOPIFY_PARTNERS_TOKEN secret
```

## Resources

- [Shopify CLI for CI/CD](https://shopify.dev/docs/apps/build/cli-for-apps/ci-cd)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Shopify App Deployment](https://shopify.dev/docs/apps/build/cli-for-apps/deploy)
