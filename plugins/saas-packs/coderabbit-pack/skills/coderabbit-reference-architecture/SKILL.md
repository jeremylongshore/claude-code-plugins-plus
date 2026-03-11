---
name: coderabbit-reference-architecture
description: |
  Implement CodeRabbit reference architecture with best-practice project layout.
  Use when designing new CodeRabbit integrations, reviewing project structure,
  or establishing architecture standards for CodeRabbit applications.
  Trigger with phrases like "coderabbit architecture", "coderabbit best practices",
  "coderabbit project structure", "how to organize coderabbit", "coderabbit layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# CodeRabbit Reference Architecture

## Overview
Configure CodeRabbit AI code review for team workflows. Covers repository configuration, custom review instructions, path-based rules, and integration with CI pipelines for automated review enforcement.

## Prerequisites
- CodeRabbit GitHub/GitLab app installed
- Repository admin access for configuration
- Understanding of team coding standards
- CI pipeline for review status checks

## Architecture Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Developer   │────▶│  Pull        │────▶│  CodeRabbit  │
│  Push/PR     │     │  Request     │     │  AI Review   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                     ┌────────────────────────────┤
                     │                            │
                     ▼                            ▼
              ┌──────────────┐          ┌──────────────┐
              │ Line-level   │          │ Summary      │
              │ Comments     │          │ Review       │
              └──────┬───────┘          └──────┬───────┘
                     │                          │
                     ▼                          ▼
              ┌──────────────┐          ┌──────────────┐
              │ Developer    │          │ CI Status    │
              │ Response     │          │ Check        │
              └──────────────┘          └──────────────┘
```

## Instructions

### Step 1: Create Repository Configuration
```yaml
# .coderabbit.yaml - Root configuration
language: "en-US"
early_access: false

reviews:
  profile: "assertive"        # Options: chill, assertive, proactive
  request_changes_workflow: true
  high_level_summary: true
  poem: false
  review_status: true
  collapse_walkthrough: false
  path_instructions:
    - path: "src/api/**"
      instructions: |
        Review for REST API best practices:
        - Validate all inputs with zod schemas
        - Return proper HTTP status codes
        - Include error response bodies per RFC 7807  # 7807 = configured value
        - Check for SQL injection in query parameters
    - path: "src/components/**"
      instructions: |
        Review React components for:
        - Proper use of hooks (no conditional hooks)
        - Memoization where appropriate
        - Accessibility (aria labels, keyboard navigation)
        - Component size (flag if >200 lines)  # HTTP 200 OK
    - path: "**/*.test.*"
      instructions: |
        Review tests for:
        - Meaningful test descriptions
        - Edge cases covered
        - No implementation details tested
        - Proper async handling

  auto_review:
    enabled: true
    drafts: false
    base_branches:
      - "main"
      - "develop"
    ignore_title_keywords:
      - "WIP"
      - "DO NOT MERGE"

chat:
  auto_reply: true
```

### Step 2: Configure Path-Based Review Rules
```yaml
# .coderabbit.yaml continued
reviews:
  path_filters:
    # Skip auto-generated files
    - "!**/*.generated.ts"
    - "!**/generated/**"
    - "!package-lock.json"
    - "!pnpm-lock.yaml"
    - "!**/*.min.js"
    - "!dist/**"

    # Always review security-sensitive paths
    - "+src/auth/**"
    - "+src/middleware/**"
    - "+**/migrations/**"

  tools:
    eslint:
      enabled: true
    biome:
      enabled: true
    shellcheck:
      enabled: true
    markdownlint:
      enabled: true
```

### Step 3: Custom Review Instructions for Team Standards
```yaml
# .coderabbit.yaml - Team-specific instructions
reviews:
  path_instructions:
    - path: "**"
      instructions: |
        Team coding standards:
        1. All exported functions must have JSDoc comments
        2. Use named exports, never default exports
        3. Prefer const assertions for literal types
        4. Error handling: never catch and ignore silently
        5. Logging: use structured logger, never console.log in production

    - path: "src/db/**"
      instructions: |
        Database layer rules:
        - All queries must use parameterized statements
        - Include index hints for complex queries
        - Transactions required for multi-table mutations
        - Migration files must be reversible

    - path: ".github/workflows/**"
      instructions: |
        CI/CD pipeline rules:
        - Pin all action versions to SHA, not tags
        - Never use secrets in step names or logs
        - Include timeout-minutes on all jobs
        - Use OIDC for cloud provider auth
```

### Step 4: Integrate with CI Pipeline
```yaml
# .github/workflows/pr-checks.yml
name: PR Checks

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  wait-for-coderabbit:
    runs-on: ubuntu-latest
    steps:
      - name: Wait for CodeRabbit review
        uses: actions/github-script@v7
        with:
          script: |
            // Check if CodeRabbit has reviewed
            const reviews = await github.rest.pulls.listReviews({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
            });

            const coderabbitReview = reviews.data.find(
              r => r.user.login === 'coderabbitai[bot]'
            );

            if (!coderabbitReview) {
              core.info('Waiting for CodeRabbit review...');
            }
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Review not triggered | PR to non-configured branch | Add branch to `base_branches` |
| Too many comments | Profile too aggressive | Switch to `chill` profile |
| Ignoring config changes | YAML syntax error | Validate YAML before committing |
| Reviewing generated files | Missing path filter | Add `!` exclusion patterns |

## Examples

### Minimal Configuration
```yaml
# .coderabbit.yaml - Quick start
reviews:
  profile: "assertive"
  auto_review:
    enabled: true
    drafts: false
```

## Resources
- [CodeRabbit Configuration](https://docs.coderabbit.ai/configuration)
- [CodeRabbit Path Instructions](https://docs.coderabbit.ai/guides/review-instructions)
- [CodeRabbit Tools](https://docs.coderabbit.ai/tools)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale