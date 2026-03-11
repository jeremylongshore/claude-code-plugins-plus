---
name: replit-enterprise-rbac
description: |
  Configure Replit enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Replit.
  Trigger with phrases like "replit SSO", "replit RBAC",
  "replit enterprise", "replit roles", "replit permissions", "replit SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Replit Enterprise RBAC

## Overview
Manage team access to Replit workspaces, deployments, and AI coding features using its Teams and Organizations model. Replit uses per-seat licensing with workspace roles: Owner, Admin, and Member.

## Prerequisites
- Replit Teams for Business or Enterprise plan (per-seat pricing)
- Organization owner or admin role
- SSO identity provider configured (Enterprise only)

## Instructions

### Step 1: Configure Organization Roles
```yaml
# replit-role-matrix.yaml
roles:
  owner:
    permissions: [manage_billing, manage_members, manage_deployments, create_repls, use_ai, admin_settings]
  admin:
    permissions: [manage_members, manage_deployments, create_repls, use_ai]
  member:
    permissions: [create_repls, use_ai, deploy_to_staging]
    restrictions: [cannot_deploy_to_prod, cannot_manage_members]
```

### Step 2: Invite and Manage Team Members
Navigate to Replit Teams > Members and invite users with assigned roles. For bulk management, use the Replit API:
```bash
set -euo pipefail
# Invite a team member
curl -X POST https://replit.com/api/v1/teams/TEAM_ID/members \
  -H "Authorization: Bearer $REPLIT_API_KEY" \
  -d '{"email": "dev@company.com", "role": "member"}'

# List current team members
curl https://replit.com/api/v1/teams/TEAM_ID/members \
  -H "Authorization: Bearer $REPLIT_API_KEY" | jq '.[] | {username, email, role}'
```

### Step 3: Control Deployment Permissions
Separate staging and production deployment access:
- Members: can deploy to development/staging URLs
- Admins: can deploy to custom domains and production
- Owner: can configure deployment infrastructure (reserved VMs, autoscaling)

Configure in Team Settings > Deployments > Permission Policy.

### Step 4: Enable SSO (Enterprise Only)
In Organization Settings > Security > SSO:
- Configure SAML 2.0 with your IdP (Okta, Azure AD, Google Workspace)
- Map IdP groups to Replit roles
- Enable "Require SSO" to block password-based login
- Set session timeout policy (recommended: 12 hours)

### Step 5: Audit Activity
```bash
set -euo pipefail
# Review recent team activity
curl "https://replit.com/api/v1/teams/TEAM_ID/audit-log?limit=50" \
  -H "Authorization: Bearer $REPLIT_API_KEY" | \
  jq '.events[] | {user, action, resource, timestamp}'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Member can't deploy | Missing deployment permission | Promote to Admin or adjust deployment policy |
| SSO login redirect loop | Incorrect callback URL | Verify ACS URL in IdP matches Replit config |
| Seat limit exceeded | Too many active members | Remove inactive members or upgrade seat count |
| AI features disabled | Ghostwriter not enabled for team | Enable AI features in Team Settings |

## Examples

**Basic usage**: Apply replit enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize replit enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official Replit Enterprise Rbac documentation
- Community best practices and patterns
- Related skills in this plugin pack