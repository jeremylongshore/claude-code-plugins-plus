---
name: sentry-enterprise-rbac
description: |
  Configure enterprise role-based access control in Sentry.
  Use when setting up team permissions, SSO integration,
  or managing organizational access.
  Trigger with phrases like "sentry rbac", "sentry permissions",
  "sentry team access", "sentry sso setup".
allowed-tools: Read, Write, Edit, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, rbac, sso, teams, permissions]

---
# Sentry Enterprise RBAC

## Prerequisites
- Sentry Business or Enterprise plan (required for team-level roles and SSO)
- Identity provider configured (Okta, Azure AD, Google Workspace for SSO)
- Team structure and project ownership documented
- Permission requirements defined per team

## Instructions

### 1. Organization-Level Roles

| Role | Capabilities |
|------|-------------|
| **Owner** | Full access. Manage billing, members, all settings. Cannot be removed. |
| **Manager** | Manage all teams and projects. Add/remove members. Cannot manage billing. |
| **Admin** | Edit global integrations, manage projects, add/remove teams. |
| **Member** | View data, act on issues, join/leave teams. Default role for new members. |
| **Billing** | Manage payment and compliance details only. |

### 2. Team-Level Roles (Business/Enterprise)

| Role | Additional Capabilities |
|------|------------------------|
| **Team Admin** | Manage team membership, add/remove projects from team |
| **Team Contributor** | View and act on issues in team's projects |

A user's effective permissions are the union of their org-level role and team-level roles.

### 3. Create and Manage Teams via API

```bash
# Create a team
curl -X POST \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slug": "backend-team", "name": "Backend Team"}' \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/teams/"

# List teams
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/teams/" \
  | python3 -c "
import json, sys
teams = json.load(sys.stdin)
for t in teams:
    print(f\"{t['slug']}: {t.get('memberCount', 'N/A')} members\")
"

# Add member to team
curl -X POST \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/members/$MEMBER_ID/teams/$TEAM_SLUG/"

# Remove member from team
curl -X DELETE \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/members/$MEMBER_ID/teams/$TEAM_SLUG/"
```

### 4. Assign Projects to Teams

```bash
# Give a team access to a project
curl -X POST \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/projects/$SENTRY_ORG/$PROJECT_SLUG/teams/$TEAM_SLUG/"

# Remove team access from project
curl -X DELETE \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/projects/$SENTRY_ORG/$PROJECT_SLUG/teams/$TEAM_SLUG/"

# List a project's teams
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/projects/$SENTRY_ORG/$PROJECT_SLUG/teams/"
```

### 5. SSO/SAML Configuration

Configure in **Organization Settings > Auth > SAML2**:

**Okta setup:**
1. Create a SAML 2.0 app in Okta
2. Set SSO URL to: `https://sentry.io/saml/acs/$ORG_SLUG/`
3. Set Audience URI to: `https://sentry.io/saml/metadata/$ORG_SLUG/`
4. Map attributes:
   - `email` -> user's email
   - `firstName` -> first name
   - `lastName` -> last name

**In Sentry:**
1. Go to Organization Settings > Auth
2. Select SAML2 provider
3. Enter IdP metadata URL or upload XML
4. Test SSO login
5. Enable "Require SSO" to enforce for all members

### 6. SCIM Provisioning (Automated User Management)

Enable in **Organization Settings > Auth > SCIM**:

```
SCIM Base URL: https://sentry.io/api/0/organizations/$ORG_SLUG/scim/v2/
SCIM Token: Generated in Sentry SCIM settings

Features:
- Auto-create users when added to IdP group
- Auto-deactivate users when removed from IdP
- Sync team membership from IdP groups
- No manual user management needed
```

### 7. API Token Scopes and Hygiene

```bash
# Create a token with minimal scopes
# Go to: sentry.io/settings/auth-tokens/

# Scope reference:
# project:read        — read project data
# project:write       — update project settings
# project:releases    — create releases, upload source maps
# event:read          — read event data
# event:write         — update event data
# org:read            — read organization data
# org:write           — update organization settings
# member:read         — list organization members
# member:write        — manage organization members
# team:read           — list teams
# team:write          — manage teams

# CI/CD tokens: project:releases, org:read (minimum for releases)
# Monitoring tokens: event:read, project:read (read-only)
# Admin tokens: Use sparingly, rotate quarterly

# List active tokens (check in dashboard)
# sentry.io/settings/auth-tokens/
```

### 8. Access Patterns

**Team-isolated access:**
```
Team: payments
  Role: Member (org-level)
  Projects: payment-api, billing-worker
  Result: Can only see issues in their projects
```

**Cross-team visibility:**
```
Team: platform-engineering
  Role: Admin (org-level)
  Projects: All (via admin role)
  Result: Can see all projects, manage integrations
```

**Contractor access:**
```
Team: contractors
  Role: Member (org-level)
  Projects: Only assigned project
  SSO: Required
  Result: Limited blast radius, auto-deactivate via SCIM
```

### 9. Audit Logging

Enable in **Organization Settings > Audit Log** (Business/Enterprise):

Audit log tracks:
- Member added/removed/role changed
- Team created/modified/deleted
- Project created/deleted/transferred
- Integration installed/removed
- SSO configuration changes
- API token creation/revocation

```bash
# Query audit log via API
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/audit-logs/" \
  | python3 -c "
import json, sys
logs = json.load(sys.stdin)
for entry in logs[:10]:
    print(f\"{entry['dateCreated']}: {entry['event']} by {entry.get('actor', {}).get('name', 'system')}\")
"
```

## Output
- Teams created with members assigned to appropriate projects
- Organization roles configured with principle of least privilege
- SSO/SAML configured with required authentication
- SCIM provisioning automating user lifecycle
- API tokens created with minimal scopes and rotation schedule
- Audit logging enabled for compliance tracking

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| User can't see project | Not on a team that owns the project | Add user's team to project, or add user to project's team |
| SSO login fails | SAML metadata mismatch | Verify SSO URL and Audience URI match exactly |
| SCIM sync not working | Token expired or wrong base URL | Regenerate SCIM token in Sentry settings |
| API returns 403 | Token missing required scope | Create new token with needed scopes |
| Audit log empty | Not on Business/Enterprise plan | Upgrade plan for audit logging |

## Resources
- [Organization Membership](https://docs.sentry.io/organization/membership/)
- [SSO & SAML](https://docs.sentry.io/organization/authentication/sso/)
- [SCIM Provisioning](https://docs.sentry.io/organization/authentication/sso/scim-provisioning/)
- [Teams API](https://docs.sentry.io/api/teams/)
- [Members API](https://docs.sentry.io/api/organizations/list-an-organizations-members/)
