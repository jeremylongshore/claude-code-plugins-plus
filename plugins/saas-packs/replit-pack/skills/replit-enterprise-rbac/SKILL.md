---
name: replit-enterprise-rbac
description: |
  Configure Replit Teams roles, SSO/SAML, custom groups, and organization-level access control.
  Use when setting up team permissions, configuring SSO, managing deployment access,
  or auditing organization security on Replit.
  Trigger with phrases like "replit SSO", "replit RBAC", "replit enterprise",
  "replit roles", "replit permissions", "replit SAML", "replit teams admin".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, rbac, enterprise, sso]

---
# Replit Enterprise RBAC

## Overview
Manage team access to Replit workspaces, deployments, and AI features. Covers the built-in role system (Admin, Manager, Editor, Viewer), custom groups (Enterprise only), SSO/SAML integration, deployment permissions, and audit logging.

## Prerequisites
- Replit Teams or Enterprise plan
- Organization Owner or Admin role
- SSO identity provider (Enterprise only): Okta, Azure AD, Google Workspace

## Role Hierarchy

| Role | Create Repls | Deploy | Manage Members | Billing | AI Features |
|------|-------------|--------|----------------|---------|-------------|
| **Owner** | Yes | All | Yes | Yes | Yes |
| **Admin** | Yes | All | Yes | View only | Yes |
| **Manager** | Yes | Staging | Add/remove | No | Yes |
| **Editor** | Yes | No | No | No | Yes |
| **Viewer** | No | No | No | No | No |

## Instructions

### Step 1: Configure Organization Roles
```markdown
In Organization Settings > Members:

1. Invite members:
   - Click "Invite" > enter email
   - Select role: Admin, Manager, Editor, or Viewer
   - Member receives email invitation

2. Bulk management (2025+):
   - CSV export of all members
   - Sort/filter by role, activity, last login
   - Bulk role changes

3. Role assignment strategy:
   - Owners: 1-2 (billing + full admin)
   - Admins: team leads (manage members + deploy)
   - Managers: senior devs (deploy to staging)
   - Editors: developers (create + code)
   - Viewers: stakeholders (read-only access)
```

### Step 2: Custom Groups (Enterprise Only)
```markdown
Enterprise plan enables custom permission groups:

1. Organization Settings > Groups
2. Create group: e.g., "Backend Team"
3. Assign permissions:
   - Access to specific Repls
   - Deployment permissions (staging only, or all)
   - AI feature access
4. Add members to group

Example groups:
- "Frontend Team": access to UI Repls, deploy to staging
- "DevOps": all Repls, deploy to production, manage secrets
- "Contractors": specific Repls only, no deployment access
- "QA": read all, deploy to staging, no production
```

### Step 3: SSO/SAML Configuration (Enterprise Only)
```markdown
Organization Settings > Security > SSO:

1. Choose provider:
   - Okta
   - Azure Active Directory
   - Google Workspace
   - Any SAML 2.0 compatible IdP

2. Configure SAML:
   - ACS URL: provided by Replit
   - Entity ID: provided by Replit
   - Certificate: from your IdP
   - Map IdP groups to Replit roles

3. Enable enforcement:
   - "Require SSO": blocks password-based login
   - Session timeout: recommended 12 hours
   - IdP-initiated logout support

4. Test:
   - Try login with SSO before enforcing
   - Verify role mapping works correctly
   - Test session timeout behavior
```

### Step 4: Deployment Permission Controls
```markdown
Control who can deploy and where:

Organization Settings > Deployments > Permissions:

Production deployments:
- Restrict to Admin + Owner only
- Require approval workflow (Enterprise)
- Custom domain management: Admin only

Staging deployments:
- Allow Managers and above
- Auto-deploy from staging branch

Development:
- All Editors can run in Workspace
- Dev database access for all team members
```

### Step 5: Audit Logging
```bash
# View recent team activity
curl "https://replit.com/api/v1/teams/TEAM_ID/audit-log?limit=50" \
  -H "Authorization: Bearer $REPLIT_TOKEN" | \
  jq '.events[] | {user, action, resource, timestamp}'

# Common audit events:
# - member.invited
# - member.removed
# - member.role_changed
# - repl.created
# - repl.deleted
# - deployment.created
# - deployment.rolled_back
# - secret.created
# - secret.deleted
```

```markdown
Enterprise audit features:
- Exportable audit logs (CSV)
- 90-day retention
- Filter by user, action, resource
- API access for SIEM integration
```

### Step 6: Quarterly Access Review
```markdown
## Access Review Checklist (run quarterly)

1. Export member list from Organization Settings
2. Review each member:
   - [ ] Last active date within 30 days?
   - [ ] Role appropriate for current responsibilities?
   - [ ] Still on the team/project?
3. Actions:
   - Remove members not active in 30+ days
   - Downgrade over-privileged members
   - Upgrade members needing more access
4. Document changes and rationale
5. Verify SSO group mappings still accurate

Cost impact:
- Each removed seat saves $25-40/month
- Quarterly review prevents seat creep
```

### Step 7: AI Feature Controls
```markdown
Replit AI features (Agent, Assistant, Ghostwriter):

Organization Settings > AI Features:
- Enable/disable AI for entire organization
- Per-role AI access (Enterprise)
- Usage tracking per member

Controls:
- Agent: can create files, install packages, deploy
- Assistant: code suggestions, chat
- Ghostwriter: inline completions

Recommendation:
- Enable AI for all developers (Editors+)
- Restrict Agent deployment to Managers+
- Monitor AI usage via dashboard
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Member can't deploy | Insufficient role | Promote to Manager or Admin |
| SSO redirect loop | Wrong ACS URL | Verify callback URL matches Replit config |
| Seat limit exceeded | Plan capacity reached | Remove inactive members or upgrade |
| Custom group not working | Not on Enterprise plan | Groups require Enterprise |
| AI features disabled | Org-level toggle off | Enable in Organization Settings > AI |

## Resources
- [Groups and Permissions](https://docs.replit.com/teams/identity-and-access-management/groups-and-permissions)
- [Replit Enterprise](https://replit.com/enterprise)
- [Replit Security](https://replit.com/products/security)
- [Replit Pro](https://replit.com/pro)

## Next Steps
For data migration patterns, see `replit-migration-deep-dive`.
