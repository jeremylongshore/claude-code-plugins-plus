---
name: coderabbit-deploy-integration
description: |
  Roll out CodeRabbit across an organization: multi-repo deployment, org-level config, and team onboarding.
  Use when deploying CodeRabbit org-wide, creating shared configurations,
  or onboarding development teams to AI code review.
  Trigger with phrases like "deploy coderabbit", "coderabbit org rollout",
  "coderabbit multi-repo", "coderabbit onboarding", "coderabbit team setup".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, deployment, onboarding]

---
# CodeRabbit Deploy Integration

## Overview
Roll out CodeRabbit AI code review across an organization. Covers multi-repo deployment strategy, organization-level configuration, team-specific customization, and developer onboarding. CodeRabbit is a GitHub/GitLab App -- deployment means configuring the App installation, customizing review behavior, and integrating review status into merge workflows.

## Prerequisites
- GitHub Organization admin access
- CodeRabbit GitHub App installed (https://github.com/apps/coderabbitai)
- CodeRabbit Pro or Enterprise plan for private repos
- List of target repositories

## Instructions

### Step 1: Plan the Rollout
```markdown
# Phase 1 (Week 1): Pilot
- Pick 2-3 high-activity repos with receptive teams
- Use "chill" profile to minimize disruption
- Collect feedback from pilot teams

# Phase 2 (Week 2-3): Expand
- Roll out to remaining backend/frontend repos
- Apply learnings from pilot (path instructions, exclusions)
- Switch to "assertive" profile

# Phase 3 (Week 4+): Enforce
- Add CodeRabbit as required status check on protected branches
- Set up org-level defaults
- Monitor adoption metrics
```

### Step 2: Create Organization-Level Configuration
```yaml
# .github/.coderabbit.yaml (in the .github repository)
# This is the org-level default applied to ALL repos in the org
# Individual repos can override by adding their own .coderabbit.yaml

language: "en-US"
early_access: false

reviews:
  profile: "assertive"
  request_changes_workflow: false    # Start with comments-only (non-blocking)
  high_level_summary: true
  high_level_summary_in_walkthrough: true
  review_status: true
  collapse_walkthrough: false
  sequence_diagrams: true
  poem: false

  auto_review:
    enabled: true
    drafts: false
    ignore_title_keywords:
      - "WIP"
      - "DO NOT MERGE"
      - "chore: bump"
      - "chore(deps)"

  path_filters:
    - "!**/*.lock"
    - "!**/package-lock.json"
    - "!**/pnpm-lock.yaml"
    - "!**/*.snap"
    - "!**/*.generated.*"
    - "!dist/**"
    - "!vendor/**"

chat:
  auto_reply: true
```

### Step 3: Create Team-Specific Repo Configs
```yaml
# .coderabbit.yaml for a backend API repo
# Inherits org defaults, adds API-specific instructions
reviews:
  profile: "assertive"
  auto_review:
    enabled: true
    base_branches: [main, develop]
  path_instructions:
    - path: "src/api/**"
      instructions: |
        Review for: input validation, proper HTTP status codes, auth middleware.
        Flag missing error handling and unvalidated request bodies.
    - path: "src/db/**"
      instructions: |
        Review for: parameterized queries, transaction boundaries, N+1 patterns.
        Flag string concatenation in SQL.
    - path: "src/auth/**"
      instructions: |
        SECURITY-CRITICAL. Review for: token validation, password hashing (bcrypt/argon2),
        session management, CSRF protection. Flag any security bypass.
    - path: ".github/workflows/**"
      instructions: |
        Review for: pinned action versions (SHA not tag), no secrets in logs,
        timeout-minutes on all jobs.
```

```yaml
# .coderabbit.yaml for a frontend React repo
reviews:
  profile: "assertive"
  path_instructions:
    - path: "src/components/**"
      instructions: |
        Review for: accessibility (aria labels, keyboard nav), performance
        (no inline styles, memo for expensive renders), proper prop types.
    - path: "src/hooks/**"
      instructions: |
        Review for: cleanup in useEffect, dependency arrays, race conditions.
    - path: "**/*.test.*"
      instructions: |
        Review for: edge cases, async handling, user interaction testing.
        Do NOT comment on import order or test naming conventions.
```

### Step 4: Script Multi-Repo Config Deployment
```bash
#!/bin/bash
# deploy-coderabbit-config.sh - Deploy .coderabbit.yaml to multiple repos
set -euo pipefail

ORG="your-org"
CONFIG_TEMPLATE=".coderabbit.yaml"
REPOS=("backend-api" "frontend-app" "mobile-api" "infrastructure")

for REPO in "${REPOS[@]}"; do
  echo "Deploying to $ORG/$REPO..."

  # Clone, add config, create PR
  TMPDIR=$(mktemp -d)
  gh repo clone "$ORG/$REPO" "$TMPDIR" -- --depth 1
  cp "$CONFIG_TEMPLATE" "$TMPDIR/.coderabbit.yaml"

  cd "$TMPDIR"
  git checkout -b feat/add-coderabbit-config
  git add .coderabbit.yaml
  git commit -m "feat: add CodeRabbit AI code review configuration"
  git push -u origin feat/add-coderabbit-config
  gh pr create \
    --title "feat: enable CodeRabbit AI code review" \
    --body "Adding .coderabbit.yaml for automated AI code reviews. See CodeRabbit docs: https://docs.coderabbit.ai"
  cd -
  rm -rf "$TMPDIR"

  echo "PR created for $ORG/$REPO"
done
```

### Step 5: Set Up Branch Protection with CodeRabbit
```bash
set -euo pipefail
ORG="your-org"
REPOS=("backend-api" "frontend-app")

for REPO in "${REPOS[@]}"; do
  echo "Setting branch protection for $ORG/$REPO..."

  gh api "repos/$ORG/$REPO/branches/main/protection" \
    --method PUT \
    --field 'required_status_checks={"strict":true,"contexts":["coderabbitai"]}' \
    --field 'required_pull_request_reviews={"required_approving_review_count":1}' \
    --field 'enforce_admins=false' \
    --field 'restrictions=null'

  echo "Branch protection set: CodeRabbit required for $ORG/$REPO"
done
```

### Step 6: Developer Onboarding Guide
```markdown
# Share with your team:

## CodeRabbit Quick Reference

CodeRabbit automatically reviews your PRs. No action needed on your part.

### What to expect:
1. Open a PR → CodeRabbit posts a review in 2-5 minutes
2. Walkthrough comment summarizes all changes
3. Line-level comments suggest improvements
4. Reply to any comment to discuss with the AI

### Useful commands (post as PR comment):
@coderabbitai full review     → Re-review all files from scratch
@coderabbitai summary         → Regenerate the walkthrough summary
@coderabbitai resolve         → Mark all CodeRabbit comments as resolved
@coderabbitai configuration   → Show current active config
@coderabbitai help            → List all available commands

### Tips:
- Keep PRs under 500 lines for best review quality
- Reply to CodeRabbit comments to teach it your preferences
- Add "WIP" to PR title to skip review on work-in-progress
```

## Output
- Organization-level CodeRabbit configuration deployed
- Team-specific repo configs with path instructions
- Multi-repo deployment script
- Branch protection with CodeRabbit as required check
- Developer onboarding guide

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Org config not applied | No `.github` repo | Create `.github` repo with `.coderabbit.yaml` |
| Repo config ignored | YAML syntax error | Validate YAML, run `@coderabbitai configuration` |
| Team resistance | Too many comments | Switch to `chill` profile initially |
| PRs blocked by review | `request_changes_workflow: true` | Start with `false` until team is comfortable |
| Bot accounts consuming seats | Bots opening PRs | Exclude bot accounts in seat management |

## Resources
- [CodeRabbit Getting Started](https://docs.coderabbit.ai/getting-started/yaml-configuration)
- [CodeRabbit Configuration Reference](https://docs.coderabbit.ai/reference/configuration)
- [Organization-Level Config](https://docs.coderabbit.ai/guides/organization-level-config)

## Next Steps
For multi-environment configuration, see `coderabbit-multi-env-setup`.
