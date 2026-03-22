---
name: coderabbit-reference-architecture
description: |
  Implement CodeRabbit reference architecture with production-grade .coderabbit.yaml configuration.
  Use when designing review configuration for a new project, establishing team standards,
  or building a comprehensive review setup from scratch.
  Trigger with phrases like "coderabbit architecture", "coderabbit best practices",
  "coderabbit project structure", "coderabbit reference config", "coderabbit full setup".
allowed-tools: Read, Write, Edit, Bash(gh:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, reference-architecture, best-practices]

---
# CodeRabbit Reference Architecture

## Overview
Complete reference architecture for CodeRabbit AI code review in a production team. Covers the full configuration file, path-specific review instructions per project type, tool integrations, CI pipeline integration, and the review lifecycle. Use this as a starting template and customize for your team.

## Architecture Diagram
```
Developer pushes code
         │
         ▼
┌─────────────────────────┐
│     Pull Request        │
│  (targets base branch)  │
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│   CodeRabbit AI Review  │
│  Reads: .coderabbit.yaml│
│  from base branch       │
│                         │
│  Outputs:               │
│  ├── Walkthrough summary│
│  ├── Sequence diagrams  │
│  ├── Line-level comments│
│  └── Review state       │
└─────────┬───────────────┘
          │
    ┌─────┴──────┐
    │            │
    ▼            ▼
┌────────┐  ┌────────────┐
│ APPROVED│  │ CHANGES    │
│         │  │ REQUESTED  │
└────┬───┘  └─────┬──────┘
     │            │
     ▼            ▼
  Merge      Developer fixes
  (if branch   and pushes
  protection   (incremental
  passes)      re-review)
```

## Instructions

### Step 1: Full Reference Configuration
```yaml
# .coderabbit.yaml - Production Reference Architecture
# Copy this file and customize for your project.

language: "en-US"
early_access: false

# Tone customization
tone_instructions: |
  Be concise and direct. Use bullet points for multiple suggestions.
  Include code examples for non-obvious fixes.
  Rate severity: Critical > Warning > Suggestion > Nitpick.

reviews:
  # Review behavior
  profile: "assertive"
  request_changes_workflow: true
  high_level_summary: true
  high_level_summary_in_walkthrough: true
  review_status: true
  collapse_walkthrough: false
  sequence_diagrams: true
  poem: false

  # Automatic review triggers
  auto_review:
    enabled: true
    drafts: false
    base_branches:
      - main
      - develop
      - "release/*"
    ignore_title_keywords:
      - "WIP"
      - "DO NOT MERGE"
      - "chore: bump"
      - "chore(deps)"

  # File exclusions (skip files with no review value)
  path_filters:
    - "!**/*.lock"
    - "!**/package-lock.json"
    - "!**/pnpm-lock.yaml"
    - "!**/yarn.lock"
    - "!**/*.snap"
    - "!**/*.generated.*"
    - "!**/generated/**"
    - "!dist/**"
    - "!build/**"
    - "!**/*.min.js"
    - "!**/*.min.css"
    - "!vendor/**"
    - "!**/__mocks__/**"
    - "!**/fixtures/**"

  # Path-specific review instructions
  path_instructions:
    # API layer
    - path: "src/api/**"
      instructions: |
        Review for:
        - Input validation on all request parameters
        - Proper HTTP status codes (don't use 200 for errors)
        - Auth middleware applied to protected routes
        - Error response format (consistent structure)
        - Rate limiting on public endpoints
        Flag: missing error handling, unvalidated input, SQL injection

    # Database layer
    - path: "src/db/**"
      instructions: |
        Review for:
        - Parameterized queries (no string concatenation in SQL)
        - Transaction boundaries on multi-table mutations
        - Connection cleanup (no connection leaks)
        - Index usage for complex queries
        Flag: N+1 query patterns, raw SQL with user input

    # Authentication
    - path: "src/auth/**"
      instructions: |
        SECURITY-CRITICAL. Review for:
        - Password hashing (bcrypt/argon2 only, never MD5/SHA)
        - Token expiry configuration
        - Session management and fixation prevention
        - CSRF protection on state-changing operations
        - Brute force protection

    # Frontend components
    - path: "src/components/**"
      instructions: |
        Review for:
        - Accessibility (aria labels, keyboard navigation, screen reader support)
        - Performance (memoization, lazy loading, bundle size impact)
        - Proper state management (no prop drilling beyond 2 levels)
        Ignore: CSS naming conventions, import order

    # Tests
    - path: "**/*.test.*"
      instructions: |
        Review for:
        - Assertion completeness (not just checking status codes)
        - Edge case coverage (null, empty, boundary values)
        - Proper async handling (await, done callbacks)
        - Test isolation (no shared mutable state)
        Do NOT comment on: test naming conventions, import order

    # CI/CD pipelines
    - path: ".github/workflows/**"
      instructions: |
        Review for:
        - Pin action versions to SHA commit hash (not tags)
        - No secrets in step names, echo, or log output
        - timeout-minutes on all jobs
        - Use OIDC for cloud provider auth
        - Minimal permissions on GITHUB_TOKEN

    # Infrastructure
    - path: "**/*.tf"
      instructions: |
        Review for:
        - No hardcoded credentials or keys
        - Encryption enabled on storage and databases
        - Security groups: no 0.0.0.0/0 ingress except 443
        - IAM: least privilege, no wildcard actions

  # Finishing touches (Pro+)
  finishing_touches:
    docstrings:
      enabled: true

  # Linter tool integrations
  tools:
    eslint:
      enabled: true
    biome:
      enabled: true
    shellcheck:
      enabled: true
    markdownlint:
      enabled: true

chat:
  auto_reply: true
```

### Step 2: Project-Specific Templates

**Node.js/TypeScript Backend:**
```yaml
# Add to path_instructions:
    - path: "src/middleware/**"
      instructions: "Review for proper error propagation, request/response typing."
    - path: "src/services/**"
      instructions: "Review for dependency injection, proper error handling, testability."
    - path: "prisma/migrations/**"
      instructions: "Verify: backward compatibility, rollback safety, no data loss."
```

**React/Next.js Frontend:**
```yaml
# Add to path_instructions:
    - path: "src/hooks/**"
      instructions: "Review for: cleanup in useEffect, dependency arrays, race conditions."
    - path: "src/pages/**"
      instructions: "Review for: SSR/SSG correctness, SEO meta tags, performance."
    - path: "src/lib/**"
      instructions: "Review for: tree-shaking friendly exports, no side effects."
```

**Python/Django Backend:**
```yaml
# Add to path_instructions:
    - path: "**/*.py"
      instructions: |
        Review for: type hints, proper exception handling, no mutable default args.
        Check: context manager usage, proper async patterns.
    - path: "**/models.py"
      instructions: "Review for: index definitions, migration compatibility, field validation."
    - path: "**/views.py"
      instructions: "Review for: permission classes, serializer validation, query optimization."
```

### Step 3: CI Pipeline Integration
```yaml
# .github/workflows/pr-checks.yml
name: PR Checks

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  # Your existing CI checks
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test

  # CodeRabbit review gate (optional)
  coderabbit-gate:
    runs-on: ubuntu-latest
    if: github.event.action == 'opened'
    steps:
      - name: CodeRabbit review expected
        uses: actions/github-script@v7
        with:
          script: |
            core.info('CodeRabbit will review this PR automatically.');
            core.info('Reviews typically post within 2-5 minutes.');
```

### Step 4: Team Onboarding Document
```markdown
# CodeRabbit Quick Reference for Developers

## What happens when you open a PR:
1. CodeRabbit reviews automatically (2-5 min)
2. Posts a walkthrough summary comment
3. Adds line-level suggestions
4. Sets review state (Approved / Changes Requested)

## Commands (post in any PR comment):
@coderabbitai full review       - Re-review all files
@coderabbitai summary           - Regenerate walkthrough
@coderabbitai resolve           - Mark all comments resolved
@coderabbitai generate-docstrings - Auto-generate docstrings
@coderabbitai configuration     - Show active config
@coderabbitai help              - List all commands

## Tips:
- Reply to comments to teach CodeRabbit your preferences
- Add "WIP" to PR title to skip review
- Keep PRs under 500 lines for best review quality
- Use @coderabbitai run <recipe> for finishing touches
```

## Output
- Complete reference `.coderabbit.yaml` with all configuration sections
- Project-specific path instruction templates
- CI pipeline integration for review gating
- Team onboarding quick reference document

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Config not applied | YAML syntax error | Validate with `python3 -c "import yaml; yaml.safe_load(open('.coderabbit.yaml'))"` |
| Too many comments | Profile too aggressive or no path_instructions | Switch to `chill` or add contextual instructions |
| Reviews on generated files | Missing path_filters | Add `!**/generated/**` and similar exclusions |
| Wrong branch config | Config not on base branch | Commit `.coderabbit.yaml` to the PR's target branch |

## Resources
- [CodeRabbit Configuration Reference](https://docs.coderabbit.ai/reference/configuration)
- [CodeRabbit Path Instructions](https://docs.coderabbit.ai/guides/review-instructions)
- [CodeRabbit Tools](https://docs.coderabbit.ai/tools)
- [CodeRabbit Finishing Touches](https://docs.coderabbit.ai/finishing-touches)

## Next Steps
For initial setup, see `coderabbit-install-auth`. For tuning, see `coderabbit-core-workflow-b`.
