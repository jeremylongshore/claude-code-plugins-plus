---
name: coderabbit-install-auth
description: |
  Install and configure CodeRabbit AI code review on GitHub or GitLab repositories.
  Use when setting up CodeRabbit for the first time, installing the GitHub App,
  configuring the CLI, or connecting CodeRabbit to your repositories.
  Trigger with phrases like "install coderabbit", "setup coderabbit",
  "coderabbit auth", "configure coderabbit", "add coderabbit to repo".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, authentication, setup]

---
# CodeRabbit Install & Auth

## Overview
CodeRabbit is an AI-powered code review platform. It installs as a GitHub App (or GitLab integration) and automatically reviews pull requests. There is no SDK to install -- you configure it via a `.coderabbit.yaml` file and interact through PR comments. Optionally, install the CLI for local pre-commit reviews.

## Prerequisites
- GitHub organization admin or GitLab group owner permissions
- A repository to enable CodeRabbit on
- (Optional) Shell access for CLI installation

## Instructions

### Step 1: Install the CodeRabbit GitHub App
```markdown
1. Navigate to https://github.com/apps/coderabbitai
2. Click "Install" and select your organization
3. Choose repository access:
   - "All repositories" for org-wide coverage
   - "Only select repositories" for targeted setup
4. Authorize the requested permissions (read code, write PR comments)
5. You will be redirected to app.coderabbit.ai to complete onboarding
```

### Step 2: Verify Installation
```bash
set -euo pipefail
# Confirm the GitHub App is installed on your repo
gh api repos/YOUR_ORG/YOUR_REPO/installation --jq '.app_slug'
# Expected output: coderabbitai
```

### Step 3: Create Base Configuration
```yaml
# .coderabbit.yaml (place in repository root)
language: "en-US"
reviews:
  profile: "assertive"          # Options: chill, assertive
  request_changes_workflow: false
  high_level_summary: true
  poem: false
  review_status: true
  collapse_walkthrough: false
  sequence_diagrams: true
  auto_review:
    enabled: true
    drafts: false
    base_branches:
      - main
      - develop
chat:
  auto_reply: true
```

### Step 4: Install the CLI (Optional)
```bash
set -euo pipefail
# Install CodeRabbit CLI for local pre-commit reviews
curl -fsSL https://cli.coderabbit.ai/install.sh | sh

# Verify installation
cr --version
```

### Step 5: Trigger Your First Review
```bash
set -euo pipefail
# Create a test branch and PR to verify CodeRabbit is active
git checkout -b test/coderabbit-verification
echo "// test change" >> src/index.ts
git add src/index.ts && git commit -m "test: verify coderabbit integration"
git push -u origin test/coderabbit-verification
gh pr create --title "test: verify CodeRabbit" --body "Testing CodeRabbit integration"

# CodeRabbit will post a review within 2-5 minutes
# Check the PR for the walkthrough comment and line-level feedback
```

### GitLab Setup (Alternative)
```markdown
1. Navigate to app.coderabbit.ai and sign in with GitLab
2. Select your GitLab group during onboarding
3. Provide a GitLab access token with api and read_repository scopes
4. CodeRabbit automatically configures the webhook:
   https://coderabbit.ai/gitlabHandler
5. Place .coderabbit.yaml in repository root (same format as GitHub)
```

## Output
- CodeRabbit GitHub App installed on selected repositories
- `.coderabbit.yaml` configuration file in repository root
- (Optional) CLI installed for local reviews
- First automated review posted on a test PR

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No review on PR | App not installed on repo | Add repo in GitHub App settings > Repository access |
| "Not accessible" error | Missing permissions | Reinstall GitHub App with correct org/repo selection |
| Review only on some PRs | PR author has no seat | Assign a seat at app.coderabbit.ai > Subscription |
| CLI install fails | Unsupported platform | Check system requirements at coderabbit.ai/cli |
| GitLab webhook missing | Token scope insufficient | Ensure token has `api` and `read_repository` scopes |

## Seat Management
CodeRabbit charges per seat (developer who creates PRs). To manage seats:
```markdown
1. Go to app.coderabbit.ai > Organization > Subscription
2. Assign seats to specific developers, or set "Active committers" mode
3. Bot accounts (dependabot, renovate) should NOT consume seats
4. Only users who open PRs need seats; reviewers do not
```

## Resources
- [CodeRabbit Getting Started](https://docs.coderabbit.ai/getting-started/yaml-configuration)
- [GitHub App Installation](https://github.com/apps/coderabbitai)
- [GitLab Integration](https://docs.coderabbit.ai/platforms/gitlab-com)
- [CodeRabbit CLI](https://www.coderabbit.ai/cli)
- [Configuration Reference](https://docs.coderabbit.ai/reference/configuration)

## Next Steps
Proceed to `coderabbit-hello-world` for your first customized review configuration.
