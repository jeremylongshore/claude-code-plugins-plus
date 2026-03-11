---
name: coderabbit-enterprise-rbac
description: |
  Configure CodeRabbit enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for CodeRabbit.
  Trigger with phrases like "coderabbit SSO", "coderabbit RBAC",
  "coderabbit enterprise", "coderabbit roles", "coderabbit permissions", "coderabbit SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# CodeRabbit Enterprise RBAC

## Overview
Manage CodeRabbit AI code review access through GitHub or GitLab organization integration. CodeRabbit inherits repository permissions from your Git provider -- if a developer has write access to a repo, CodeRabbit will review their PRs.

## Prerequisites
- CodeRabbit Pro or Enterprise plan (per-seat pricing)
- GitHub Organization admin or GitLab Group owner role
- CodeRabbit GitHub App installed on the organization

## Instructions

### Step 1: Control Repository Access via GitHub App
```yaml
# In GitHub Org Settings > Installed Apps > CodeRabbit:
# Select "Only select repositories" instead of "All repositories"
# This limits which repos CodeRabbit can review
enabled_repos:
  - backend-api        # Core service, always review
  - frontend-app       # High-traffic, always review
  - infrastructure     # IaC changes need review
disabled_repos:
  - sandbox            # Experimental, skip reviews
  - docs-internal      # Low-risk markdown only
```

### Step 2: Configure Organization-Wide Review Rules
```yaml
# .coderabbit.yaml at the org level (applied to all repos)
reviews:
  auto_review:
    enabled: true
    ignore_paths:
      - "*.md"
      - "*.lock"
      - "vendor/**"
  review_language: "en"
  profile: "assertive"    # Options: chill, assertive, nitpicky
  seat_assignment: "active_committers"  # Only count active devs as seats
```

### Step 3: Manage Seat Allocation
CodeRabbit charges per seat. Control costs by limiting seats to active committers:
- Navigate to CodeRabbit Dashboard > Organization > Seats
- Set seat policy to "Active committers only" (contributors with commits in last 30 days)
- Remove bot accounts and CI service accounts from seat count

### Step 4: Set Per-Repo Review Policies
```yaml
# .coderabbit.yaml in a specific repo (overrides org defaults)
reviews:
  auto_review:
    enabled: true
    drafts: false           # Skip draft PRs
    base_branches:
      - main                # Only review PRs targeting main
  path_instructions:
    - path: "src/auth/**"
      instructions: "Security-sensitive. Check for auth bypass and injection."
    - path: "migrations/**"
      instructions: "Verify backward compatibility and rollback safety."
```

### Step 5: Audit Review Activity
Check the CodeRabbit dashboard for review metrics per repository and team member. Export data for compliance reporting: reviews generated, comments accepted vs dismissed, and average time-to-review.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| CodeRabbit not reviewing PRs | App not installed on repo | Add repo in GitHub App settings |
| Seat limit exceeded | Too many active committers | Remove inactive users or upgrade plan |
| Reviews on wrong branches | No `base_branches` filter | Add branch filter to `.coderabbit.yaml` |
| Bot reviewing bot PRs | Dependabot/Renovate triggers | Add bot usernames to ignore list |

## Examples

**Basic usage**: Apply coderabbit enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize coderabbit enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official Coderabbit Enterprise Rbac documentation
- Community best practices and patterns
- Related skills in this plugin pack