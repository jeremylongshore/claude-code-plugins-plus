---
name: coderabbit-enterprise-rbac
description: |
  Configure CodeRabbit enterprise access control, seat management, and organization policies.
  Use when managing who gets AI reviews, configuring organization-level defaults,
  or implementing access policies for CodeRabbit across teams.
  Trigger with phrases like "coderabbit SSO", "coderabbit RBAC",
  "coderabbit enterprise", "coderabbit roles", "coderabbit permissions", "coderabbit seats".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, enterprise, rbac, access-control]

---
# CodeRabbit Enterprise RBAC

## Overview
Manage CodeRabbit AI code review access across an enterprise organization. CodeRabbit inherits repository permissions from your Git provider -- if a developer has write access to a repo and opens a PR, CodeRabbit reviews it. Enterprise controls focus on seat management, repository scoping, organization-level configuration, and review policy enforcement.

## Prerequisites
- CodeRabbit Pro or Enterprise plan
- GitHub Organization admin or GitLab Group owner role
- CodeRabbit GitHub App installed on the organization
- Access to CodeRabbit dashboard at app.coderabbit.ai

## Access Control Model
```
GitHub/GitLab Org Permissions
         │
         ▼
┌─────────────────────────┐
│ CodeRabbit GitHub App   │
│ Repository Access:      │
│  ├── All repositories   │ ← Reviews every PR in the org
│  └── Select repos only  │ ← Reviews only selected repos
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ Seat Assignment         │
│  ├── Active committers  │ ← Auto-assigns seats to PR authors
│  └── Manual assignment  │ ← Admin picks who gets seats
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────┐
│ .coderabbit.yaml        │
│  ├── Org-level defaults │ ← .github repo
│  └── Repo-level overrides│ ← Per-repo customization
└─────────────────────────┘
```

## Instructions

### Step 1: Control Repository Access
```markdown
# In GitHub > Organization > Settings > Installed Apps > CodeRabbit:

Option A: "All repositories" (org-wide)
- Every repo gets AI reviews automatically
- New repos are covered immediately
- Higher seat count (every PR author = seat)

Option B: "Only select repositories" (targeted)
- Choose which repos get AI reviews
- Lower seat count
- New repos must be manually added

# Recommended: Start with Option B (select repos)
# Add repos in tiers based on risk/value
```

### Step 2: Configure Seat Management
```markdown
# In CodeRabbit Dashboard > Organization > Subscription:

1. Seat Policy Options:
   - "Active committers" → Auto-assign to anyone who opens a PR
   - "Manual assignment" → Admin explicitly assigns seats

2. Exclude Bot Accounts:
   - dependabot[bot]
   - renovate[bot]
   - github-actions[bot]
   - Any CI service accounts

3. Monitor Seat Usage:
   - Active seats: developers who opened PRs in last 30 days
   - Idle seats: no PR activity in 30+ days → candidates for removal

# Billing: ~$15/seat/month (Pro), custom (Enterprise)
# Only PR authors consume seats, not reviewers or commenters
```

### Step 3: Set Organization-Level Defaults
```yaml
# .github/.coderabbit.yaml (in the .github repo)
# Applied to ALL repos unless overridden by repo-level config

language: "en-US"
reviews:
  profile: "assertive"
  request_changes_workflow: false
  high_level_summary: true
  review_status: true
  poem: false
  sequence_diagrams: true

  auto_review:
    enabled: true
    drafts: false
    ignore_title_keywords:
      - "WIP"
      - "DO NOT MERGE"
      - "chore: bump"

  path_filters:
    - "!**/*.lock"
    - "!**/*.snap"
    - "!**/generated/**"
    - "!dist/**"
    - "!vendor/**"

  # Organization-wide coding standards
  path_instructions:
    - path: "**"
      instructions: |
        Org-wide rules:
        1. Flag hardcoded secrets, API keys, or credentials
        2. Check for proper error handling (no empty catch blocks)
        3. Verify input validation on API endpoints

chat:
  auto_reply: true
```

### Step 4: Team-Specific Repository Overrides
```yaml
# .coderabbit.yaml in a specific repo (overrides org defaults)
reviews:
  profile: "assertive"      # Can override org default
  request_changes_workflow: true   # This repo requires CR approval

  auto_review:
    enabled: true
    base_branches:
      - main                 # Only review PRs targeting main
    drafts: false

  path_instructions:
    - path: "src/auth/**"
      instructions: |
        SECURITY-CRITICAL path. Check for:
        - Auth bypass vulnerabilities
        - Injection attacks
        - Improper session handling
        - Token validation gaps
    - path: "src/payments/**"
      instructions: |
        PCI-SENSITIVE path. Check for:
        - Credit card data handling
        - Proper encryption usage
        - Audit logging of financial operations
    - path: "migrations/**"
      instructions: |
        Verify: backward compatibility, rollback safety,
        no data loss on down migration.
```

### Step 5: Audit Review Activity
```bash
set -euo pipefail
ORG="${1:-your-org}"

echo "=== CodeRabbit Org-Wide Review Audit ==="
echo "Organization: $ORG"
echo ""

# List repos with CodeRabbit installed
echo "--- Repos with CodeRabbit ---"
for REPO in $(gh repo list "$ORG" --limit 50 --json name --jq '.[].name'); do
  INSTALLED=$(gh api "repos/$ORG/$REPO/installation" --jq '.app_slug' 2>/dev/null || echo "none")
  if [ "$INSTALLED" = "coderabbitai" ]; then
    # Count recent reviews
    REVIEWS=$(gh api "repos/$ORG/$REPO/pulls?state=closed&per_page=10" --jq '.[].number' 2>/dev/null | \
      head -5 | xargs -I{} gh api "repos/$ORG/$REPO/pulls/{}/reviews" \
        --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | length' 2>/dev/null | \
      awk '{sum+=$1} END {print sum+0}')
    echo "  $REPO: $REVIEWS reviews (last 5 PRs)"
  fi
done
```

### Step 6: Enterprise SSO and Compliance
```markdown
# CodeRabbit Enterprise plan includes:

1. SSO Integration:
   - GitHub Enterprise Cloud SSO (SAML)
   - GitLab SAML SSO
   - Automatic seat provisioning via SCIM

2. Data Residency:
   - Code is processed and not stored (ephemeral analysis)
   - Review comments stored in your Git provider (GitHub/GitLab)
   - CodeRabbit learnings stored on CodeRabbit servers
   - SOC 2 Type II certified

3. Compliance Features:
   - Audit logs available in enterprise dashboard
   - Data processing agreement (DPA) available
   - Custom data retention policies
   - IP allowlisting for self-hosted GitLab

# Contact: enterprise@coderabbit.ai for custom plans
```

## Output
- Repository access scoped to appropriate repos
- Seat management configured with bot exclusions
- Organization-level defaults deployed
- Team-specific review policies applied
- Audit script for review activity monitoring

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| CodeRabbit not reviewing PRs | App not installed on repo | Add repo in GitHub App settings |
| Seat limit exceeded | Too many active committers | Remove inactive users or upgrade plan |
| Org config not applying | No `.github` repo in org | Create `.github` repo with `.coderabbit.yaml` |
| Repo config ignored | YAML syntax error | Validate YAML, check with `@coderabbitai configuration` |
| Bot consuming seats | Bot opens PRs | Exclude bot usernames in seat management |

## Resources
- [CodeRabbit Enterprise](https://coderabbit.ai/pricing)
- [Organization Config](https://docs.coderabbit.ai/guides/organization-level-config)
- [Seat Management](https://docs.coderabbit.ai/guides/seat-management)
- [SOC 2 Compliance](https://coderabbit.ai/security)

## Next Steps
For cost optimization, see `coderabbit-cost-tuning`.
