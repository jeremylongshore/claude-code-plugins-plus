---
name: coderabbit-deploy-integration
description: |
  Deploy CodeRabbit integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying CodeRabbit-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy coderabbit", "coderabbit Vercel",
  "coderabbit production deploy", "coderabbit Cloud Run", "coderabbit Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# CodeRabbit Deploy Integration

## Overview
Deploy CodeRabbit AI code review integration across your repositories and CI/CD pipelines. CodeRabbit is a GitHub/GitLab App, so deployment means configuring the App installation, customizing review behavior via `.coderabbit.yaml`, and integrating review status into your merge workflows.

## Prerequisites
- GitHub or GitLab organization admin access
- CodeRabbit GitHub App installed from coderabbit.ai
- Repository access configured for CodeRabbit
- `.coderabbit.yaml` configuration file

## Instructions

### Step 1: Install CodeRabbit GitHub App
```markdown
1. Visit https://github.com/apps/coderabbitai
2. Click "Install" and select your organization
3. Choose repositories (all or select specific ones)
4. Authorize the required permissions
```

### Step 2: Configure Review Behavior
```yaml
# .coderabbit.yaml (repository root)
language: en
reviews:
  auto_review:
    enabled: true
    drafts: false
    base_branches:
      - main
      - develop
  path_filters:
    - "!dist/**"
    - "!**/*.min.js"
    - "!**/generated/**"
    - "!**/*.lock"
  review_instructions:
    - path: "src/api/**"
      instructions: "Focus on security, authentication, and input validation"
    - path: "src/db/**"
      instructions: "Check for SQL injection and proper transaction handling"
    - path: "**/*.test.*"
      instructions: "Verify test coverage and edge cases"
chat:
  auto_reply: true
```

### Step 3: Branch Protection Rules
```bash
# Require CodeRabbit approval before merge
gh api repos/$OWNER/$REPO/branches/main/protection -X PUT \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field required_status_checks='{"strict":true,"contexts":["coderabbitai"]}'
```

### Step 4: CI Integration
```yaml
# .github/workflows/pr-check.yml
name: PR Checks
on: [pull_request]

jobs:
  wait-for-coderabbit:
    runs-on: ubuntu-latest
    steps:
      - name: Wait for CodeRabbit review
        uses: lewagon/wait-on-check-action@v1.3.4
        with:
          ref: ${{ github.event.pull_request.head.sha }}
          check-name: "coderabbitai"
          repo-token: ${{ secrets.GITHUB_TOKEN }}
          wait-interval: 30
```

### Step 5: Organization-Wide Configuration
```yaml
# .github/.coderabbit.yaml (organization-level defaults)
language: en
reviews:
  auto_review:
    enabled: true
  path_filters:
    - "!**/*.generated.*"
chat:
  auto_reply: true
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Review not triggered | App not installed on repo | Check GitHub App installation |
| Config not applied | YAML syntax error | Validate `.coderabbit.yaml` syntax |
| Review takes too long | Large PR | Split into smaller PRs |
| False positives | Missing context | Add `review_instructions` for specific paths |

## Examples

### Verify Installation
```bash
gh api repos/$OWNER/$REPO/installation --jq '.app_slug'
# Should output: coderabbitai
```

## Resources
- [CodeRabbit Setup Guide](https://docs.coderabbit.ai/getting-started)
- [Configuration Reference](https://docs.coderabbit.ai/configuration)
- [GitHub App Permissions](https://docs.coderabbit.ai/permissions)

## Next Steps
For multi-environment config, see `coderabbit-multi-env-setup`.
