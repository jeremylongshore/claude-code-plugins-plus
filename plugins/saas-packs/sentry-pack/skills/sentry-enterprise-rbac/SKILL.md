---
name: sentry-enterprise-rbac
description: |
  Configure enterprise role-based access control in Sentry.
  Use when setting up team permissions, SSO integration,
  or managing organizational access.
  Trigger with phrases like "sentry rbac", "sentry permissions",
  "sentry team access", "sentry sso setup".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Sentry Enterprise RBAC

## Overview
Configure role-based access control for enterprise Sentry deployments.

## Organization Structure

### Hierarchy
```
Organization
├── Teams
│   ├── Team Members (with roles)
│   └── Team Projects (assigned)
└── Projects
    └── Project Settings
```

### Team Structure Example
```
Organization: MyCompany
├── Team: Backend
│   ├── Members: alice (admin), bob (member)
│   └── Projects: api, worker, database
├── Team: Frontend
│   ├── Members: charlie (admin), dana (member)
│   └── Projects: web-app, mobile-app
└── Team: DevOps
    ├── Members: eve (owner)
    └── Projects: [all projects - admin access]
```

## Role Definitions

### Organization Roles
| Role | Permissions |
|------|-------------|
| Owner | Full admin, billing, delete org |
| Manager | Manage teams, members, settings |
| Admin | Manage projects, integrations |
| Member | View issues, create alerts |
| Billing | Manage subscription only |

### Team Roles
| Role | Permissions |
|------|-------------|
| Team Admin | Full team management |
| Contributor | Full issue access |
| Member | View and comment |

## Setting Up Teams

### Create Team via Dashboard
1. Settings → Teams → Create Team
2. Set team name and slug
3. Assign initial members

### Create Team via API
```bash
# Create team
curl -X POST \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Backend Team", "slug": "backend"}' \
  "https://sentry.io/api/0/organizations/$ORG/teams/"
```

### Add Members to Team
```bash
# Add member
curl -X POST \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "developer@company.com"}' \
  "https://sentry.io/api/0/teams/$ORG/$TEAM/members/"
```

## Project Access Control

### Assign Project to Team
```bash
curl -X POST \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/projects/$ORG/$PROJECT/teams/$TEAM/"
```

### Remove Team from Project
```bash
curl -X DELETE \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/projects/$ORG/$PROJECT/teams/$TEAM/"
```

## SSO Integration

### SAML Configuration
1. Settings → Auth → Configure SAML
2. Copy ACS URL and Entity ID to IdP
3. Upload IdP metadata or configure manually:
   - IdP Entity ID
   - SSO URL
   - Certificate

### SAML Attribute Mapping
```xml
<!-- Required attributes -->
<Attribute Name="email" />

<!-- Optional attributes -->
<Attribute Name="firstName" />
<Attribute Name="lastName" />
<Attribute Name="teams" />  <!-- For auto team assignment -->
```

### SCIM Provisioning
```bash
# Enable SCIM
# Settings → Auth → SCIM

# SCIM endpoint
https://sentry.io/api/0/organizations/$ORG/scim/v2/

# Supported resources
- Users
- Groups (Teams)
```

### Auto Team Assignment
```json
// IdP sends team membership
{
  "teams": ["backend", "frontend"],
  "role": "member"
}
```

## API Token Management

### Create Organization Token
```bash
# Create token with specific scopes
curl -X POST \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Token",
    "scopes": ["project:releases", "org:read"]
  }' \
  "https://sentry.io/api/0/organizations/$ORG/api-tokens/"
```

### Token Scopes
```
project:read       - Read project data
project:write      - Modify projects
project:releases   - Create/manage releases
org:read          - Read org data
org:write         - Modify org settings
team:read         - Read team data
team:write        - Manage teams
member:read       - List members
member:write      - Manage members
event:read        - Read events/issues
event:write       - Modify issues
alerts:read       - Read alerts
alerts:write      - Manage alerts
```

## Access Patterns

### Team-Isolated Access
```
Team: Payment-Service
├── Projects: payment-api, payment-worker
├── Members: payment team only
└── Alerts: Route to #payment-alerts
```

### Cross-Team Visibility
```
Team: SRE
├── Projects: ALL (read access)
├── Role: Manager (org-wide visibility)
└── Purpose: Incident response
```

### Contractor Access
```
Role: Member (limited)
Access: Specific project only
Duration: Time-limited token
Audit: All actions logged
```

## Audit Logging

### Access Audit Log
```bash
# Get audit log entries
curl -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$ORG/audit-logs/"
```

### Audit Events Tracked
- Member added/removed
- Role changes
- Project access changes
- SSO configuration changes
- API token creation
- Settings modifications

## Best Practices

### Principle of Least Privilege
```yaml
# Good: Minimal required access
developer:
  role: member
  teams: [their-team]
  projects: [their-projects]

# Avoid: Over-privileged access
developer:
  role: admin
  teams: [all]
  projects: [all]
```

### Team Organization
```yaml
# Organize by service ownership
teams:
  - name: auth-service
    projects: [auth-api, auth-worker]

  - name: platform
    projects: [all]
    role: read-only

# Not by function (leads to confusion)
teams:
  - name: backend  # Too broad
  - name: frontend # Too broad
```

### Token Hygiene
- Rotate tokens quarterly
- Use specific scopes
- Delete unused tokens
- Audit token usage

## Resources
- [Sentry Team Management](https://docs.sentry.io/product/accounts/membership/)
- [SSO & SAML](https://docs.sentry.io/product/accounts/sso/)
- [SCIM Provisioning](https://docs.sentry.io/product/accounts/sso/scim-provisioning/)
