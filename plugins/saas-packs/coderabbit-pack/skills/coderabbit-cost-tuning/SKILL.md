---
name: coderabbit-cost-tuning
description: |
  Optimize CodeRabbit costs through tier selection, sampling, and usage monitoring.
  Use when analyzing CodeRabbit billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "coderabbit cost", "coderabbit billing",
  "reduce coderabbit costs", "coderabbit pricing", "coderabbit expensive", "coderabbit budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# CodeRabbit Cost Tuning

## Overview
Optimize CodeRabbit per-seat licensing costs by right-sizing seat allocation, focusing reviews on high-value repositories, and configuring review scope to minimize unnecessary AI processing. CodeRabbit charges per seat based on active committers.

## Prerequisites
- CodeRabbit Pro or Enterprise plan
- GitHub/GitLab org admin access
- Access to CodeRabbit dashboard for seat management

## Instructions

### Step 1: Audit Seat Utilization
Navigate to CodeRabbit Dashboard > Organization > Seats:
```yaml
# Identify wasted seats
seat_audit:
  active_committers_30d: 15    # These cost money
  bot_accounts: 3              # Dependabot, Renovate, CI bots (should NOT be seats)
  inactive_30d: 7              # Haven't committed in 30 days
  total_seats_billed: 25

  # Savings: Remove bots (3) + inactive (7) = 10 fewer seats
  # At ~$15/seat/month = $150/month savings
```

### Step 2: Set Seat Policy to Active Committers Only
In CodeRabbit Dashboard > Organization > Billing:
- Switch seat policy from "All org members" to "Active committers"
- Define active as "committed in the last 30 days"
- Exclude bot accounts explicitly: `dependabot[bot]`, `renovate[bot]`, `github-actions[bot]`

### Step 3: Focus Reviews on High-Value Repos
```yaml
# Only enable CodeRabbit on repos where code review matters most
enable_coderabbit:
  - backend-api           # Business logic, security-critical
  - payment-service       # PCI compliance, financial data
  - infrastructure        # Terraform/IaC, blast radius high
  - mobile-app            # Customer-facing, release quality

disable_coderabbit:
  - documentation         # Markdown only, low risk
  - design-assets         # Binary files, not reviewable
  - sandbox               # Experimental, throwaway code
  - archived-*            # Read-only repos
```

### Step 4: Exclude Low-Value Paths from Reviews
```yaml
# .coderabbit.yaml - Skip files that don't benefit from AI review
reviews:
  auto_review:
    enabled: true
    ignore_paths:
      - "**/*.md"           # Documentation
      - "**/*.lock"         # Lock files
      - "**/*.json"         # Config/data files
      - "vendor/**"         # Third-party code
      - "dist/**"           # Build output
      - "**/*.generated.*"  # Auto-generated files
      - "migrations/**"     # DB migrations (review manually)
```

### Step 5: Monitor Review Value
Track comment acceptance rate. If acceptance rate is below 30%, reviews are costing money without adding value:
```bash
# Check acceptance rate for the last 100 PRs
gh api repos/ORG/REPO/pulls?state=closed\&per_page=100 --jq '.[].number' | \
  head -20 | xargs -I{} gh api repos/ORG/REPO/pulls/{}/reviews \
  --jq '[.[] | select(.user.login=="coderabbitai")] | length' | \
  awk '{sum+=$1; count++} END {print "Avg reviews/PR:", sum/count}'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Seat count higher than expected | Bots counted as seats | Explicitly exclude bot accounts |
| Reviews on archived repos | App still installed | Remove CodeRabbit from archived repos |
| Low review acceptance | Wrong review profile | Switch from `nitpicky` to `chill` |
| Cannot reduce seats | Active committers in all repos | Disable CodeRabbit on low-value repos |

## Examples

**Basic usage**: Apply coderabbit cost tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize coderabbit cost tuning for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack