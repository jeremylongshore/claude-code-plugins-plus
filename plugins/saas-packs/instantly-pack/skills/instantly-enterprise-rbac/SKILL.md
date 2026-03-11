---
name: instantly-enterprise-rbac
description: |
  Configure Instantly enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Instantly.
  Trigger with phrases like "instantly SSO", "instantly RBAC",
  "instantly enterprise", "instantly roles", "instantly permissions", "instantly SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Instantly Enterprise RBAC

## Overview
Manage team access to Instantly email outreach campaigns, sending accounts, and lead lists. Instantly uses per-seat pricing with workspace-level roles: Owner, Admin, and Member.

## Prerequisites
- Instantly Growth or Hypergrowth plan (per-seat + sending volume pricing)
- Workspace owner or admin role
- Email sending accounts connected and warmed up

## Instructions

### Step 1: Define Team Roles and Sending Permissions
```yaml
# instantly-access-matrix.yaml
roles:
  owner:
    permissions: [manage_billing, manage_members, all_campaigns, all_accounts, analytics]
  admin:
    permissions: [manage_members, all_campaigns, all_accounts, analytics]
  member:
    permissions: [own_campaigns, assigned_accounts, own_analytics]

# Sending account assignment
sending_accounts:
  "john@outreach.company.com": assigned_to: john@company.com
  "sales1@outreach.company.com": assigned_to: sarah@company.com
  "sales2@outreach.company.com": assigned_to: sarah@company.com
```

### Step 2: Invite Team Members with Role Assignment
```bash
set -euo pipefail
# Invite an SDR as a Member (limited to own campaigns)
curl -X POST https://api.instantly.ai/api/v1/team/invite \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" \
  -d '{"email": "sdr@company.com", "role": "member"}'

# List team members
curl https://api.instantly.ai/api/v1/team/members \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | jq '.[] | {email, role, status}'
```

### Step 3: Assign Sending Accounts to Specific Members
Prevent cross-contamination of email reputation by assigning each warmed sending account to exactly one team member:
```bash
set -euo pipefail
curl -X POST https://api.instantly.ai/api/v1/account/assign \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" \
  -d '{"account_email": "john@outreach.company.com", "assigned_to": "john@company.com"}'
```

### Step 4: Set Campaign Visibility Rules
- **Private campaigns**: Only the creator and admins can see them
- **Team campaigns**: Visible to all workspace members
- Configure default visibility in Workspace Settings > Campaigns > Default Visibility

### Step 5: Monitor Sending Limits and Deliverability
```bash
set -euo pipefail
# Check sending limits and current usage per account
curl https://api.instantly.ai/api/v1/account/status \
  -H "Authorization: Bearer $INSTANTLY_API_KEY" | \
  jq '.accounts[] | {email, daily_limit, sent_today, warmup_status, reputation_score}'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Member can't see campaign | Campaign set to private | Change visibility or add member as collaborator |
| Sending account bounce spike | Account not fully warmed | Reduce daily limit, extend warmup period |
| `403` on team endpoint | User is Member, not Admin | Promote to Admin for team management |
| Duplicate leads across SDRs | No lead deduplication | Enable workspace-level lead dedup in settings |

## Examples

**Basic usage**: Apply instantly enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize instantly enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official Instantly Enterprise Rbac documentation
- Community best practices and patterns
- Related skills in this plugin pack