---
name: coderabbit-multi-env-setup
description: |
  Configure CodeRabbit review behavior per branch and environment using path instructions and base branches.
  Use when setting different review profiles per branch, configuring stricter reviews for release branches,
  or customizing CodeRabbit behavior across dev/staging/prod workflows.
  Trigger with phrases like "coderabbit environments", "coderabbit staging",
  "coderabbit per-branch config", "coderabbit release review", "coderabbit environment setup".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, environments, branching]

---
# CodeRabbit Multi-Environment Setup

## Overview
Configure CodeRabbit review behavior based on branch targets and environments. CodeRabbit reads `.coderabbit.yaml` from the PR's base branch, allowing different review configurations per branch. This enables stricter reviews for production branches, relaxed reviews for development, and custom instructions per environment.

## Prerequisites
- CodeRabbit GitHub App installed on repository
- Branch strategy defined (e.g., GitFlow, trunk-based, GitHub Flow)
- `.coderabbit.yaml` committed to each relevant branch

## How Branch-Based Config Works
```
Developer opens PR: feature/auth → develop
  CodeRabbit reads: .coderabbit.yaml from develop branch
  Profile: "chill" (development, quick iteration)

Developer opens PR: develop → main
  CodeRabbit reads: .coderabbit.yaml from main branch
  Profile: "assertive" (production, thorough review)

Developer opens PR: hotfix/fix → release/v2.1
  CodeRabbit reads: .coderabbit.yaml from release/v2.1 branch
  Profile: "assertive" + security-focused instructions
```

## Instructions

### Step 1: Configure Development Branch (Relaxed)
```yaml
# .coderabbit.yaml on develop branch
language: "en-US"

reviews:
  profile: "chill"                     # Fewer comments for rapid iteration
  request_changes_workflow: false      # Don't block merges to develop
  high_level_summary: true
  sequence_diagrams: false             # Skip diagrams for dev PRs

  auto_review:
    enabled: true
    drafts: false
    base_branches:
      - develop
    ignore_title_keywords:
      - "WIP"
      - "DO NOT MERGE"
      - "experiment"

  path_filters:
    - "!**/*.lock"
    - "!**/*.snap"
    - "!dist/**"
    - "!**/*.generated.*"

  path_instructions:
    - path: "**"
      instructions: |
        Development branch review:
        - Only flag bugs, security issues, and obvious errors
        - Do NOT comment on code style, naming, or formatting
        - Do NOT suggest refactoring unless it fixes a bug

chat:
  auto_reply: true
```

### Step 2: Configure Production Branch (Strict)
```yaml
# .coderabbit.yaml on main branch
language: "en-US"

reviews:
  profile: "assertive"                 # Thorough review for production
  request_changes_workflow: true       # Block merge on issues
  high_level_summary: true
  high_level_summary_in_walkthrough: true
  sequence_diagrams: true
  review_status: true

  auto_review:
    enabled: true
    drafts: false
    base_branches:
      - main

  path_filters:
    - "!**/*.lock"
    - "!**/*.snap"
    - "!dist/**"
    - "!vendor/**"

  path_instructions:
    - path: "**"
      instructions: |
        Production review checklist:
        1. Flag any hardcoded secrets, API keys, or credentials
        2. Check error handling: no empty catch blocks, proper error propagation
        3. Verify input validation on all API endpoints
        4. Check for proper logging (structured, no PII)

    - path: "src/api/**"
      instructions: |
        API review (production):
        - Verify proper HTTP status codes
        - Check auth middleware is applied to protected routes
        - Validate request bodies with schema validation
        - Ensure error responses follow RFC 7807 format
        - Flag missing rate limiting

    - path: "src/db/**"
      instructions: |
        Database review (production):
        - All queries MUST use parameterized statements
        - Transactions required for multi-table mutations
        - Check for N+1 query patterns
        - Verify index usage for complex queries
        - Flag any raw SQL string concatenation

    - path: ".github/workflows/**"
      instructions: |
        CI/CD review (production):
        - Pin ALL action versions to SHA (not tags)
        - Never echo or log secrets
        - Include timeout-minutes on all jobs
        - Use OIDC for cloud provider authentication

chat:
  auto_reply: true
```

### Step 3: Configure Release Branch (Security-Focused)
```yaml
# .coderabbit.yaml on release/* branches
language: "en-US"

reviews:
  profile: "assertive"
  request_changes_workflow: true       # Block merges on issues

  auto_review:
    enabled: true
    drafts: false
    base_branches:
      - "release/*"

  path_instructions:
    - path: "**"
      instructions: |
        RELEASE BRANCH - Security and stability focus:
        1. Flag ANY security vulnerability (priority over all other feedback)
        2. Check for backward compatibility
        3. Verify no debug code (console.log, debugger statements)
        4. Ensure proper error messages (no stack traces exposed to users)
        5. Check for feature flags guarding unreleased features
        Only provide feedback on bugs and security. Skip style comments entirely.

    - path: "src/auth/**"
      instructions: |
        CRITICAL PATH for release. Check:
        - Token validation and expiry
        - Session management security
        - CSRF protection
        - No auth bypass vulnerabilities

chat:
  auto_reply: true
```

### Step 4: Maintain Branch Configs with a Script
```bash
#!/bin/bash
# update-coderabbit-configs.sh - Keep branch configs in sync
set -euo pipefail

CURRENT_BRANCH=$(git branch --show-current)

# Update develop branch config
git checkout develop 2>/dev/null || git checkout -b develop
cp configs/coderabbit-develop.yaml .coderabbit.yaml
git add .coderabbit.yaml
git diff --cached --quiet || git commit -m "chore: update CodeRabbit config for develop"

# Update main branch config
git checkout main
cp configs/coderabbit-main.yaml .coderabbit.yaml
git add .coderabbit.yaml
git diff --cached --quiet || git commit -m "chore: update CodeRabbit config for main"

# Return to original branch
git checkout "$CURRENT_BRANCH"

echo "CodeRabbit configs updated on develop and main"
echo "Push both branches to apply: git push origin develop main"
```

### Step 5: Verify Per-Branch Configuration
```markdown
# On a PR targeting develop:
@coderabbitai configuration
# Should show: profile: "chill", request_changes_workflow: false

# On a PR targeting main:
@coderabbitai configuration
# Should show: profile: "assertive", request_changes_workflow: true

# If both show the same config, the branch-specific .coderabbit.yaml
# is not committed to the base branch. Verify with:
# git show main:.coderabbit.yaml
# git show develop:.coderabbit.yaml
```

### Step 6: Branch Protection per Environment
```bash
set -euo pipefail
OWNER="your-org"
REPO="your-repo"

# Main: require CodeRabbit approval
gh api "repos/$OWNER/$REPO/branches/main/protection" \
  --method PUT \
  --field 'required_status_checks={"strict":true,"contexts":["coderabbitai"]}' \
  --field 'required_pull_request_reviews={"required_approving_review_count":1}' \
  --field 'enforce_admins=true' \
  --field 'restrictions=null'

# Develop: CodeRabbit review optional (not required)
gh api "repos/$OWNER/$REPO/branches/develop/protection" \
  --method PUT \
  --field 'required_status_checks={"strict":false,"contexts":[]}' \
  --field 'required_pull_request_reviews={"required_approving_review_count":0}' \
  --field 'enforce_admins=false' \
  --field 'restrictions=null'

echo "Branch protection configured"
echo "  main: CodeRabbit required"
echo "  develop: CodeRabbit optional"
```

## Output
- Branch-specific `.coderabbit.yaml` configs committed
- Development branch with relaxed review profile
- Production branch with strict review and security instructions
- Release branches with security-focused review
- Branch protection rules aligned with review policies

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Same review profile on all branches | Config only on one branch | Commit different `.coderabbit.yaml` to each base branch |
| Config changes not applied | YAML not on the base branch | Merge config changes to the target branch first |
| PR to main gets "chill" review | `.coderabbit.yaml` on main has wrong profile | Check config with `git show main:.coderabbit.yaml` |
| Release branch not reviewed | `base_branches` doesn't include `release/*` | Add glob pattern `release/*` to base_branches |

## Resources
- [CodeRabbit Configuration Reference](https://docs.coderabbit.ai/reference/configuration)
- [CodeRabbit Branch-Based Config](https://docs.coderabbit.ai/guides/review-instructions)
- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository)

## Next Steps
For deployment and org-wide rollout, see `coderabbit-deploy-integration`.
