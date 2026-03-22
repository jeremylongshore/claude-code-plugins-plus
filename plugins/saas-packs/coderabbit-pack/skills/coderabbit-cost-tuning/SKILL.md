---
name: coderabbit-cost-tuning
description: |
  Optimize CodeRabbit costs through seat management, repo selection, and review scope tuning.
  Use when analyzing CodeRabbit billing, reducing per-seat costs,
  or implementing usage monitoring and budget optimization.
  Trigger with phrases like "coderabbit cost", "coderabbit billing",
  "reduce coderabbit costs", "coderabbit pricing", "coderabbit expensive", "coderabbit budget".
allowed-tools: Read, Grep, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, cost-optimization, billing]

---
# CodeRabbit Cost Tuning

## Overview
Optimize CodeRabbit per-seat licensing costs by right-sizing seat allocation, focusing reviews on high-value repositories, and configuring review scope to minimize unnecessary AI processing. CodeRabbit charges per seat based on active committers who open PRs.

## Prerequisites
- CodeRabbit Pro or Enterprise plan
- GitHub/GitLab org admin access
- Access to CodeRabbit dashboard at app.coderabbit.ai

## Pricing Model
| Plan | Price | Includes |
|------|-------|----------|
| Free | $0 | Public repos, limited reviews |
| Pro | ~$15/seat/month | Unlimited reviews, all features |
| Enterprise | Custom | SSO, dedicated support, SLA |

**Seat = any developer who opens a PR in a CodeRabbit-enabled repo.**

## Instructions

### Step 1: Audit Seat Utilization
Navigate to CodeRabbit Dashboard > Organization > Seats:
```yaml
# Example seat audit
seat_audit:
  active_committers_30d: 15    # These cost money
  bot_accounts: 3              # Dependabot, Renovate, CI bots (should NOT consume seats)
  inactive_30d: 7              # Haven't opened a PR in 30 days
  total_seats_billed: 25

  # Savings: Remove bots (3) + inactive (7) = 10 fewer seats
  # At ~$15/seat/month = $150/month savings
```

### Step 2: Set Seat Policy to Active Committers Only
In CodeRabbit Dashboard > Organization > Billing:
- Switch seat policy from "All org members" to "Active committers"
- Define active as "opened a PR in the last 30 days"
- Exclude bot accounts explicitly: `dependabot[bot]`, `renovate[bot]`, `github-actions[bot]`

### Step 3: Focus Reviews on High-Value Repos
Only enable CodeRabbit on repos where AI review adds value:
```markdown
# Enable CodeRabbit (high value):
- backend-api         → Business logic, security-critical
- payment-service     → PCI compliance, financial data
- infrastructure      → Terraform/IaC, blast radius high
- mobile-app          → Customer-facing, release quality

# Disable CodeRabbit (low value):
- documentation       → Markdown only, low risk
- design-assets       → Binary files, not reviewable
- sandbox             → Experimental, throwaway code
- archived-*          → Read-only repos
- internal-tools      → Low-traffic, single-developer repos

# To disable: GitHub > Installed Apps > CodeRabbit > Repository access
# Switch to "Only select repositories" and remove low-value repos
```

### Step 4: Exclude Low-Value Files from Reviews
```yaml
# .coderabbit.yaml - Skip files that don't benefit from AI review
reviews:
  path_filters:
    - "!**/*.lock"              # Lock files (no actionable feedback)
    - "!**/package-lock.json"
    - "!**/pnpm-lock.yaml"
    - "!**/*.snap"              # Test snapshots
    - "!**/*.generated.*"       # Generated code
    - "!dist/**"                # Build output
    - "!vendor/**"              # Third-party code
    - "!**/*.min.js"            # Minified files
    - "!**/migrations/*.sql"    # DB migrations (review manually)
    - "!**/*.csv"               # Data files
    - "!**/*.json"              # Config/data files (usually low-value)

  auto_review:
    ignore_title_keywords:
      - "chore: bump"           # Skip dependency update PRs
      - "chore(deps)"
      - "auto-generated"
      - "Bump version"
    drafts: false               # Don't burn credits reviewing drafts
```

### Step 5: Use the Right Review Profile
```yaml
# More aggressive profile = more comments = more processing
# But the main cost is per-seat, not per-comment
reviews:
  profile: "assertive"   # Recommended default
  # "chill" produces fewer comments but same per-seat cost
  # Choose based on signal-to-noise, not cost optimization
```

### Step 6: Monitor Review Value
Track whether CodeRabbit reviews are being acted on:
```bash
set -euo pipefail
ORG="${1:-your-org}"
REPO="${2:-your-repo}"

echo "=== CodeRabbit Review Value Analysis ==="
TOTAL_PRS=0
REVIEWED_PRS=0

for PR_NUM in $(gh api "repos/$ORG/$REPO/pulls?state=closed&per_page=30" --jq '.[].number'); do
  TOTAL_PRS=$((TOTAL_PRS + 1))
  CR_COMMENTS=$(gh api "repos/$ORG/$REPO/pulls/$PR_NUM/comments" \
    --jq '[.[] | select(.user.login=="coderabbitai[bot]")] | length' 2>/dev/null || echo "0")
  if [ "$CR_COMMENTS" -gt 0 ]; then
    REVIEWED_PRS=$((REVIEWED_PRS + 1))
    echo "PR #$PR_NUM: $CR_COMMENTS CodeRabbit comments"
  fi
done

echo ""
echo "Coverage: $REVIEWED_PRS/$TOTAL_PRS PRs received CodeRabbit reviews"
echo "If coverage is low, check: base_branches filter, drafts setting, seat assignment"
```

### Step 7: CLI Credit Management
```markdown
# CodeRabbit CLI charges per file reviewed (~$0.25/file)
# Tips to reduce CLI costs:

# Review only specific files (not entire repo)
cr review src/api/routes.ts src/middleware/auth.ts

# Use --prompt-only to get review text without interactive mode
cr review --prompt-only

# Set up pre-push hook (not pre-commit) to avoid reviewing WIP code
# See coderabbit-local-dev-loop for hook setup
```

## Output
- Seat audit completed with wasted seats identified
- Repository access scoped to high-value repos only
- Path filters configured to skip low-value files
- Review coverage metrics measured
- CLI usage optimized with targeted file reviews

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Seat count higher than expected | Bots counted as seats | Exclude bot accounts in dashboard |
| Reviews on archived repos | App still installed | Remove CodeRabbit from archived repos |
| Low review acceptance rate | Reviews too nitpicky | Switch profile to `chill` |
| Can't reduce seat count | Active committers across all repos | Disable CodeRabbit on low-value repos first |
| CLI charges higher than expected | Reviewing all files | Use `cr review <specific-files>` instead |

## Resources
- [CodeRabbit Pricing](https://coderabbit.ai/pricing)
- [CodeRabbit Seat Management](https://docs.coderabbit.ai/guides/seat-management)
- [CodeRabbit CLI Pricing](https://www.coderabbit.ai/cli)

## Next Steps
For enterprise seat management and SSO, see `coderabbit-enterprise-rbac`.
