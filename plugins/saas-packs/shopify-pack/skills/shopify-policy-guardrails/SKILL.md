---
name: shopify-policy-guardrails
description: |
  Implement Shopify app policy enforcement with ESLint rules for API key detection,
  query cost budgets, and App Store compliance checks.
  Use when hardening a Shopify app against secret leaks, enforcing query cost limits,
  or preparing for App Store submission review.
  Trigger with phrases like "shopify policy", "shopify lint",
  "shopify guardrails", "shopify compliance", "shopify eslint", "shopify app review".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Policy & Guardrails

## Overview

Automated policy enforcement for Shopify apps: secret detection, query cost budgets, App Store compliance checks, and CI policy validation.

## Prerequisites

- ESLint configured in project
- Pre-commit hooks infrastructure
- CI/CD pipeline with GitHub Actions
- Shopify app with `shopify.app.toml`

## Instructions

### Step 1: Secret Detection Rules

Custom ESLint rule that catches hardcoded Shopify tokens (`shpat_*`, `shpss_*`) and API secrets in string literals and template literals.

See [Secret Detection ESLint](references/secret-detection-eslint.md) for the complete rule implementation.

### Step 2: Query Cost Budget Enforcement

Static analysis of GraphQL queries enforcing budgets: max 100 items per `first:` param, max 3 levels of nesting, and max 500 estimated cost. Runs at build/test time.

See [Query Cost Budget](references/query-cost-budget.md) for the complete implementation.

### Step 3: Pre-Commit Hooks

Git hooks that scan staged changes for Shopify tokens and block `.env` files from being committed.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: shopify-token-scan
        name: Scan for Shopify tokens
        language: system
        entry: bash -c '
          if git diff --cached --diff-filter=d | grep -E "shpat_[a-f0-9]{32}|shpss_[a-f0-9]{32}" ; then
            echo "ERROR: Shopify access token detected in staged changes"
            exit 1
          fi'
        pass_filenames: false

      - id: shopify-env-check
        name: Check .env not staged
        language: system
        entry: bash -c '
          if git diff --cached --name-only | grep -E "^\.env$|^\.env\.local$|^\.env\.production$" ; then
            echo "ERROR: .env file staged for commit"
            exit 1
          fi'
        pass_filenames: false
```

### Step 4: App Store Compliance Checker

Pre-submission script that validates all three GDPR webhooks, token hygiene, CSP headers, and API version stability.

See [Compliance Checker](references/compliance-checker.md) for the complete implementation.

### Step 5: CI Policy Pipeline

GitHub Actions workflow enforcing token scanning, GDPR webhook configuration, and API version stability on every push and PR.

See [CI Policy Pipeline](references/ci-policy-pipeline.md) for the complete workflow.

## Output

- ESLint rules catching hardcoded tokens
- Query cost budgets enforced
- Pre-commit hooks blocking secret leaks
- App Store compliance checker
- CI policy pipeline preventing violations

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| False positive on token | Base64 string matched | Narrow regex pattern |
| Query cost estimate wrong | Complex variable nesting | Use actual debug header in tests |
| Pre-commit bypassed | `--no-verify` flag | Enforce in CI as backup |
| App Store rejection | Missing GDPR webhook | Run compliance checker before submit |

## Examples

### Quick Policy Scan

```bash
# One-liner: check for token leaks in staged changes
git diff --cached | grep -E "shpat_|shpss_" && echo "TOKEN LEAK!" || echo "Clean"

# Check GDPR compliance
grep -c "customers/data_request\|customers/redact\|shop/redact" shopify.app.toml
# Should output: 3
```

## Resources

- [Shopify App Store Requirements](https://shopify.dev/docs/apps/launch/app-requirements)
- [ESLint Plugin Development](https://eslint.org/docs/latest/extend/plugins)
- [git-secrets](https://github.com/awslabs/git-secrets)
